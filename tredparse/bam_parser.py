import pandas as pd
import pysam
import numpy as np
import logging

from collections import defaultdict
from utils import datafile


SPAN = 1000
FLANKMATCH = 9
DNAPE_ELONGATE = SPAN * 10  # How far do we look beyond the target for paired-end
UNIQY = datafile("chrY.hg38.unique_ccn.gc")


class BamParser:
    '''
    Find Huntington repeats from aligned reads bam file
    :inputParams: InputParams object
    '''

    def __init__(self, inputParams):
        '''
        :param referenceVersion: hg19 or hg38
        :param chromosomePrefix: our reference has "chr4". You may need CHR4, pass in CHR
        '''
        self.inputParams = inputParams
        self.logger = logging.getLogger('BamParser')
        self.logger.setLevel(inputParams.getLogLevel())
        self.bam = inputParams.bam
        self.gender = inputParams.gender
        self.flankSize = inputParams.flankSize
        self.READLEN = inputParams.READLEN

        # initialize tred-specific things
        self.tred = inputParams.tred
        self.repeatSize = len(self.tred.repeat)
        self.CHR_STR = self.tred.chromosome

        # X-linked TRED
        if self.gender == 'Male' and self.tred.is_xlinked:
            self.ploidy = 1
        else:
            self.ploidy = self.tred.ploidy
        self.logger.debug("Locus: {}; Ploidy={}"\
                        .format(str(self.tred), self.ploidy))

        self.repeat = self.tred.repeat
        self.startRepeat, self.endRepeat = self.tred.repeat_start, self.tred.repeat_end
        self.referenceLen = self.tred.repeat_end - self.tred.repeat_start + 1
        self.fullPrefix, self.fullSuffix = self.tred.prefix, self.tred.suffix

        # TODO: limit by chromosome end
        self.WINDOW_START = max(0, self.startRepeat - self.READLEN)
        self.WINDOW_END = self.endRepeat + self.READLEN # go a few bases beyond end

        self.full_count = defaultdict(int)
        self.prefix_count = defaultdict(int)
        self.postfix_count = defaultdict(int)
        self.dupReads = 0
        self.details = []  # Store read sequences, enabled on logging.INFO

    def _buildDB(self):
        '''
        Build a series of aligners that each uses a reference with varying
        number of repeats - whichever scores the best is the winner.
        '''
        from ssw import Aligner

        ssws = []
        max_units = (self.READLEN - FLANKMATCH) / len(self.repeat) + 1
        # Build a list of ssw
        for units in xrange(1, max_units):
            target = self.fullPrefix + self.repeat * units + self.fullSuffix
            ssw = Aligner(ref_seq=target,
                          match=1, mismatch=5, gap_open=7, gap_extend=2,  # Strict
                          #match=1, mismatch=4, gap_open=6, gap_extend=1, # BWA-MEM
                          report_secondary=False)
            ssws.append((units, target, ssw))
        return ssws

    def get_hangs(self, al):
        """
        Determine the type of overlap given query, ref alignment coordinates
        Consider the following alignment between sequence a and b:
        aLhang \              / aRhang
                \------------/
                /------------\
        bLhang /              \ bRhang
        Terminal overlap: a before b, b before a
        Contain overlap: a in b, b in a
        """
        aLhang, aRhang = al.ref_begin, len(al.ref_seq) - al.ref_end - 1
        bLhang, bRhang = al.query_begin, len(al.query_seq) - al.query_end - 1

        s1 = aRhang + bLhang
        s2 = aLhang + bRhang
        s3 = aLhang + aRhang
        s4 = bLhang + bRhang

        return min(s1, s2, s3, s4)

    def _parseReadSW(self, chromosome, pos, seq, db, verbose=False):
        '''
        Use Smith-Waterman matcher to classify reads and count number of
        repeats. This is the preferred method that allows mismatches (sequencing
        errors or SNPs) inside the read.
        '''
        fs = self.flankSize - FLANKMATCH
        res = []
        for units, target, ssw in db:
            min_len = min(len(seq), len(target)) / 2
            min_score = max(min_len, 30)
            al = ssw.align(seq, min_score=min_score, min_len=min_len)
            if not al:
                continue
            prefix_read = al.ref_begin < fs
            suffix_read = al.ref_end > len(target) - fs - 1
            hang = self.get_hangs(al)
            hang_read = hang > FLANKMATCH

            if verbose:
                import sys
                print >> sys.stderr, units, target
                print >> sys.stderr, al
                print >> sys.stderr, '\n'.join(al.alignment)
                print >> sys.stderr, prefix_read, suffix_read, hang_read, hang

            if hang_read:
                tag = "HANG"
            elif prefix_read:
                tag = "PREF"
                if suffix_read:
                    tag = "FULL"
            elif suffix_read:
                tag = "POST"
            else:
                continue
            res.append((al.score, units, tag))

        if not res:
            return

        score, h, tag = max(res, key=lambda x: (x[0], -x[1]))
        countMap = None
        if tag == "FULL":
            countMap = self.full_count
        elif tag == "PREF":
            countMap = self.prefix_count
        elif tag == "POST":
            countMap = self.postfix_count

        if countMap is not None:
            countMap[h] += 1

        s = "{}: h={:>3}, seq={}".format(tag, h, seq)
        self.logger.debug(s)
        self.details.append({'tag': tag, 'h': h, 'seq': seq})

    def _makePlotFrame(self):
        columns = ['NumReps', 'full', 'prefix', 'postfix']
        numReps = pd.unique(self.full_count.keys() +
                            self.prefix_count.keys() +
                            self.postfix_count.keys())
        rows = []
        for nr in numReps:
            rows.append([nr, self.full_count.get(nr),
                         self.prefix_count.get(nr),
                         self.postfix_count.get(nr)])

        df = pd.DataFrame(rows, columns=columns)
        df.replace(to_replace={np.NaN : 0}, inplace=True)
        df.sort_values(by='NumReps', inplace=True)
        df.set_index(keys='NumReps', inplace=True)
        df['partial'] = df['prefix'] + df['postfix']

        return df

    def _parse(self):
        samfile = pysam.AlignmentFile(self.bam, "rb")
        db = self._buildDB()

        chr, start, end = self.CHR_STR, self.WINDOW_START, self.WINDOW_END
        if test_fetch(samfile, chr, start, end, self.logger):
            for read in samfile.fetch(chr, start, end):
                if read.is_duplicate:
                    self.dupReads += 1
                    continue
                self._parseReadSW(chromosome=chr, pos=read.reference_start,
                           seq=read.query_sequence, db=db)

        self.logger.debug("full: {}".format(self.full_count))
        self.logger.debug("prefix: {}".format(self.prefix_count))
        self.logger.debug("postfix: {}".format(self.postfix_count))

        self.df = self._makePlotFrame()


class BamParserResults:
    '''
    Encapsulates all results: counts from BamParser and calls from different callers
    '''
    def __init__(self, inputParams, tred, df, details,
                       Q, PP, label, integratedCalls):
        self.inputParams = inputParams
        self.tred = tred
        self.details = details
        self.Q = Q
        self.PP = PP
        self.label = label
        self.df_full = dict((k, v) for k, v in \
                                df["full"].to_dict().items() if v)
        self.df_partial = dict((k, v) for k, v in \
                                df["partial"].to_dict().items() if v)
        self.FDP = int(sum(self.df_full.values()))
        self.PDP = int(sum(self.df_partial.values()))
        self.integratedCalls = integratedCalls


class PEextractor:
    """
    Infer distance paired-end reads spanning a certain region.
    """
    def __init__(self, bp):
        samfile = pysam.AlignmentFile(bp.bam, "rb")
        chr = bp.CHR_STR
        start = bp.startRepeat
        end = bp.endRepeat
        self.ref = bp.referenceLen

        # Compute the target distribution (defined as paired spanning the CAG repeats)
        pstart = max(start - DNAPE_ELONGATE, 0)
        pend = end + DNAPE_ELONGATE
        cache = {}
        if test_fetch(samfile, chr, pstart, pend, bp.logger):
            cache = defaultdict(list)
            for x in samfile.fetch(chr, pstart, pend):
                if not x.is_paired:
                    continue
                if x.is_unmapped:
                    continue
                if x.is_duplicate:
                    continue
                cache[x.query_name].append(x)

        self.global_lens, self.target_lens = [], []
        for name, reads in cache.iteritems():
            if len(reads) < 2:
                continue
            a, b = reads[:2]
            if not ((not a.is_reverse) and b.is_reverse):  # Mapped in +, - orientation
                continue

            tlen = self.get_target_length(a, b)
            if tlen >= SPAN:  # Skip pairs that are too distant
                continue
            # Get all pairs where read1 is on left flank and read2 is on right flank (spanning pair)
            if a.reference_start < start - FLANKMATCH and \
               b.reference_end > end + FLANKMATCH:
                self.target_lens.append(tlen)
            else:
                self.global_lens.append(tlen)

    def get_target_length(self, a, b):
        start, end = a.reference_start, b.reference_end
        if a.query_alignment_start > 0:  # has clips
            start -= a.query_alignment_start
        if b.query_alignment_end < b.query_length:  # has clips
            end += b.query_length - b.query_alignment_end
        return end - start


class BamReadLen:
    """
    Returns the read length in BAM file.
    """
    def __init__(self, bamfile, logger):
        self.bamfile = bamfile
        self.logger = logger

    @property
    def readlen(self, firstN=100):
        sam = pysam.AlignmentFile(self.bamfile, 'rb')
        rls = []
        for read in sam.fetch():
            rls.append(read.query_length)
            if len(rls) > firstN:
                break
        rmin, rmax = min(rls), max(rls)
        if rmin != rmax:
            self.logger.debug("Read length: min={}bp max={}bp".format(rmin, rmax))
        return int(np.median(rls))


class BamDepth:
    def __init__(self, bamfile, logger):
        self.bamfile = bamfile
        self.logger = logger

    def region_depth(self, chr, start, end):
        sam = pysam.AlignmentFile(self.bamfile, 'rb')
        depths = [c.n for c in sam.pileup(chr, start, end)]
        return sum(depths) * 1. / (end - start + 1)

    def get_Y_depth(self, N=5):
        fp = open(UNIQY)
        depths = []
        for i, row in enumerate(fp):
            # Some regions still have mapped reads, exclude a few
            if i in (1, 4, 6, 7, 10, 11, 13, 16, 18, 19):
                continue
            if len(depths) >= N:
                break
            c, start, end, gc = row.split()
            start, end = int(start), int(end)
            d = self.region_depth(c, start, end)
            depths.append(d)
        self.logger.debug("Y depths (first {} regions): {}"\
                    .format(N, np.array(depths)))
        return np.median(depths)


def test_fetch(samfile, chr, start, end, logger):
    try:
        samfile.fetch(chr, start, end)
        return True
    except ValueError:
        logger.error("No reads extracted for region {}:{}-{}".format(chr, start, end))
        return False
