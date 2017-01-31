#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
HLI TRED caller: parse the target regions from the input BAM file, extract full and partial
reads, build probabilistic model and calculate the most likely repeat sizes given the
data.
"""

import argparse
import shutil
import os
import os.path as op
import json
import gzip
import sys
import time
import logging

from tredparse.utils import DefaultHelpParser, InputParams, \
        mkdir, ls_s3, push_to_s3
from tredparse.bam_parser import BamDepth, BamReadLen, BamParser, \
        BamParserResults, read_alignment
from tredparse.models import IntegratedCaller
from tredparse.meta import TREDsRepo
from datetime import datetime as dt, timedelta
from multiprocessing import Pool, cpu_count

logging.basicConfig()
logger = logging.getLogger(__name__)


INFO = """##INFO=<ID=RPA,Number=1,Type=String,Description="Repeats per allele">
##INFO=<ID=END,Number=1,Type=Integer,Description="End position of variant">
##INFO=<ID=MOTIF,Number=1,Type=String,Description="Canonical repeat motif">
##INFO=<ID=NS,Number=1,Type=Integer,Description="Number of samples with data">
##INFO=<ID=REF,Number=1,Type=Integer,Description="Reference copy number">
##INFO=<ID=CR,Number=1,Type=Integer,Description="Disease copy number cutoff">
##INFO=<ID=IH,Number=1,Type=String,Description="Inheritance">
##INFO=<ID=RL,Number=1,Type=Integer,Description="Reference STR track length in bp">
##INFO=<ID=VT,Number=1,Type=String,Description="Variant type">
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##FORMAT=<ID=GA,Number=1,Type=String,Description="Genotype with absolute copy numbers">
##FORMAT=<ID=FR,Number=1,Type=String,Description="Full reads aligned to locus">
##FORMAT=<ID=PR,Number=1,Type=String,Description="Partial reads aligned to locus">
##FORMAT=<ID=FDP,Number=1,Type=Integer,Description="Full read Depth">
##FORMAT=<ID=PDP,Number=1,Type=Integer,Description="Partial read Depth">
##FORMAT=<ID=Q,Number=1,Type=Float,Description="Likelihood ratio score of allelotype call">
##FORMAT=<ID=PP,Number=1,Type=Float,Description="Post. probability of disease">
##FORMAT=<ID=LABEL,Number=1,Type=String,Description="Risk assessment">
"""


def set_argparse():
    TRED_NAMES = set(TREDsRepo().keys())

    p = DefaultHelpParser(description=__doc__, prog=__file__,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument('infile', nargs='?', help="Input path (BAM, list of BAMs, or csv format)")
    p.add_argument('--cpus', help='Number of CPUs to use', type=int, default=cpu_count())
    p.add_argument('--ref', help='Reference genome version',
                        choices=("hg38", "hg19"), default='hg38')
    p.add_argument('--tred', help='STR disorder, default is to run all',
                        action='append', choices=sorted(TRED_NAMES), default=None)
    p.add_argument('--haploid', help='Treat these chromosomes as haploid', action='append')
    p.add_argument('--maxinsert', default=100, type=int,
                        help="Maximum number of repeats")
    p.add_argument('--log', choices=("INFO", "DEBUG"), default="INFO",
                        help='Print debug logs, DEBUG=verbose')
    p.add_argument('--toy', help=argparse.SUPPRESS, action="store_true")
    p.add_argument('--cleanup', default=False, action="store_true",
                                help="Cleanup the workdir after done")
    p.add_argument('--checkexists', default=False, action="store_true",
                                help="Do not run if JSON output exists")
    p.add_argument('--no-output', default=False, action="store_true",
                                help="Do not write JSON and VCF output")
    set_aws_opts(p)
    return p


def set_aws_opts(p):
    group = p.add_argument_group("AWS and Docker options")
    p.add_argument_group(group)
    # https://github.com/hlids/infrastructure/wiki/Docker-calling-convention
    group.add_argument("--sample_id", help="Sample ID")
    group.add_argument("--workflow_execution_id", help="Workflow execution ID")
    group.add_argument("--input_bam_path", help="Input s3 path, override infile")
    group.add_argument("--output_path", help="Output s3 path")
    group.add_argument("--workdir", default=os.getcwd(), help="Specify work dir")


def check_bam(bam):
    # Check indices - remove if found, otherwise distinct bams may try to use
    # the previous index, leading to an error
    bbam = op.basename(bam)
    baifile = bbam + ".bai"
    altbaifile = bbam.rsplit(".", 1)[0] + ".bai"

    for bai in (baifile, altbaifile):
        if op.exists(bai):
            logger.debug("Remove index `{}`".format(bai))
            os.remove(bai)

    # Does the file exist?
    logger.debug("Working on `{}`".format(bam))
    try:
        read_alignment(bam)
    except (IOError, ValueError) as e:
        logger.error("Cannot retrieve file `{}` ({})".format(bam, e))
        return None

    return bam


def counter_s(c):
    return ";".join(["{}|{}".format(k, int(v)) for k, v in \
                    sorted(c.items()) if v])


def runBam(inputParams):
    '''
    Convenience function: parses one bam and runs all callers on it
    :param inputParams: InputParams
    :return: BamParserResult
    '''
    maxinsert = inputParams.kwargs["maxinsert"]
    bp18 = BamParser(inputParams)
    bp18._parse()

    # find the integrated likelihood calls
    integratedCaller = IntegratedCaller(bp18, maxinsert=maxinsert)
    integratedCaller.call(**inputParams.kwargs)

    return BamParserResults(inputParams, bp18.tred, bp18.df, bp18.details,
                            integratedCaller)


def run(arg):
    '''
    Run Tred Caller on a list of treds
    :param bam: path to bam file
    :param: referenceVersion, hg19 or hg38
    :return: dict of calls
    '''
    samplekey, bam, repo, tredNames, maxinsert, log = arg
    cwd = os.getcwd()
    mkdir(samplekey)
    os.chdir(samplekey)
    gender = 'Unknown'
    ydepth = -1

    tredCalls = {"inferredGender": gender, "depthY": ydepth}
    if check_bam(bam) is None:
        return samplekey, bam, tredCalls

    # Infer gender based on depth on chrY
    if any(repo[tred].is_xlinked for tred in tredNames):
        try:
            bd = BamDepth(bam, logger)
            ydepth = bd.get_Y_depth()
            if ydepth > 1:
                gender = 'Male'
            else:
                gender = 'Female'
        except:
            pass
        logger.debug("Inferred gender: {} (depthY={})".format(gender, ydepth))
        tredCalls["inferredGender"] = gender
        tredCalls["depthY"] = ydepth

    # Get read length
    READLEN = 150
    try:
        brl = BamReadLen(bam, logger)
        READLEN = brl.readlen
    except:
        pass
    logger.debug("Read length: {}bp".format(READLEN))
    tredCalls["readLen"] = READLEN

    for tred in tredNames:
        ip = InputParams(bam=bam, READLEN=READLEN, flankSize=18, tredName=tred,
                         repo=repo, maxinsert=maxinsert, gender=gender,
                         log=log)

        try:
            tpResult = runBam(ip)
        except Exception as e:
            logger.error("Exception on `{}` {} ({})".format(bam, tred, e))
            continue

        res = tpResult.integratedCalls
        tredCalls[tred + ".1"] = res[0] # .1 is the shorter allele
        tredCalls[tred + ".2"] = res[1] # .2 is the longer allele
        tredCalls[tred + ".FR"] = counter_s(tpResult.df_full)
        tredCalls[tred + ".PR"] = counter_s(tpResult.df_partial)
        tredCalls[tred + ".FDP"] = tpResult.FDP     # Full depth
        tredCalls[tred + ".PDP"] = tpResult.PDP     # Partial depth
        tredCalls[tred + ".PEDP"] = tpResult.PEDP   # PE depth
        tredCalls[tred + ".PEG"] = tpResult.PEG     # PE global estimate
        tredCalls[tred + ".PET"] = tpResult.PET     # PE target estimate
        tredCalls[tred + ".Q"] = tpResult.Q         # Quality
        tredCalls[tred + ".PP"] = tpResult.PP       # Prob(disease)
        tredCalls[tred + ".label"] = tpResult.label # Disease status
        if logger.getEffectiveLevel() == logging.DEBUG:
            tredCalls[tred + ".details"] = tpResult.details

    os.chdir(cwd)
    shutil.rmtree(samplekey)
    return {'samplekey': samplekey, 'bam': bam, 'tredCalls': tredCalls}


def vcfstanza(sampleid, bam, tredCalls, ref):
    # VCF spec
    m = "##fileformat=VCFv4.1\n"
    m += "##fileDate={}{:02d}{:02d}\n".format(dt.now().year, dt.now().month, dt.now().day)
    m += "##source={} {}\n".format(__file__, bam)
    m += "##reference={}\n".format(ref)
    m += "##inferredGender={} depthY={}\n".format(
                    tredCalls["inferredGender"], tredCalls["depthY"])
    m += "##readLen={}bp\n".format(tredCalls["readLen"])
    m += INFO
    header = "CHROM POS ID REF ALT QUAL FILTER INFO FORMAT\n".split() + [sampleid]
    m += "#" + "\t".join(header)
    return m


def to_json(results, ref, treds=["HD"], store=None):
    sampleid = results['samplekey']
    bam = results['bam']
    calls = results['tredCalls']
    if not calls:
        logger.debug("No calls are found for {} `{}`".format(sampleid, bam))
        return

    jsonfile = ".".join((sampleid, "json"))
    js = json.dumps(results)
    print js
    fw = open(jsonfile, "w")
    print >> fw, js
    fw.close()

    if store:
        push_to_s3(store, jsonfile)


def to_vcf(results, ref, treds=["HD"], store=None):
    registry = {}
    repo = TREDsRepo(ref=ref)
    for tred in treds:
        tr = repo.get_info(tred)
        registry[tred] = tr

    sampleid = results['samplekey']
    bam = results['bam']
    calls = results['tredCalls']

    if not calls:
        logger.debug("No calls are found for {} `{}`".format(sampleid, bam))
        return

    vcffile = ".".join((sampleid, "tred.vcf.gz"))
    contents = []
    for tred in treds:
        a = calls[tred + ".1"]
        b = calls[tred + ".2"]
        chr, start, ref_copy, repeat, info = registry[tred]
        alleles = set([a, b])
        refv = set([ref_copy])
        rpa = sorted(alleles - refv)
        alt = ",".join(x * repeat for x in rpa) if (rpa and rpa[0] != -1) else "."
        if rpa:
            info += ";RPA={}".format(",".join((str(x) for x in rpa)))
            if ref_copy in alleles:
                gt = "0/1"
            elif len(rpa) == 1:
                gt = "1/1"
            else:
                gt = "1/2"
        else:
            gt = "0/0"
        gb = "{}/{}".format(a, b)
        fields = "{}:{}:{}:{}:{}:{}:{:.4g}:{:.4g}:{}".format(gt, gb,
                        calls[tred + ".FR"], calls[tred + ".PR"],
                        calls[tred + ".FDP"], calls[tred + ".PDP"],
                        calls[tred + ".Q"], calls[tred + ".PP"],
                        calls[tred + ".label"])
        m = "\t".join(str(x) for x in (
           chr, start, tred, ref_copy * repeat, alt, ".", ".", info,
           "GT:GB:FR:PR:FDP:PDP:Q:PP:LABEL", fields))
        contents.append((chr, start, m))

    fw = gzip.open(vcffile, "w")
    print >> fw, vcfstanza(sampleid, bam, calls, ref)
    contents.sort()
    for chr, start, m in contents:
        print >> fw, m
    fw.close()
    logger.debug("VCF file written to `{}`".format(vcffile))

    if store:
        push_to_s3(store, vcffile)


def read_csv(csvfile, args):
    # Mode 1: See if this is just a BAM file
    if csvfile.endswith(".bam") or csvfile.endswith(".cram"):
        bam = csvfile
        if args.workflow_execution_id and args.sample_id:
            samplekey = "_".join((args.workflow_execution_id, args.sample_id))
        else:
            samplekey = op.basename(bam).rsplit(".", 1)[0]
        return [(samplekey, bam)]

    fp = open(csvfile)
    # Mode 2: See if the file contains JUST list of BAM files
    header = fp.next().strip()
    contents = []
    if header.endswith(".bam") and header.count(",") == 0:
        fp.seek(0)
        for row in fp:
            bam = row.strip()
            samplekey = op.basename(bam).rsplit(".", 1)[0]
            contents.append((samplekey, bam))
        return contents

    # Mode 3: Continue reading, this is a CSV file
    fp.seek(0)
    for row in fp:
        atoms = row.strip().split(",")
        samplekey, bam = atoms[:2]
        if bam.endswith(".bam"):
            contents.append((samplekey, bam))
    return contents


# temporary script to run on N samples
if __name__ == '__main__':
    p = set_argparse()
    args = p.parse_args()

    loglevel = getattr(logging, args.log.upper(), "INFO")
    logger.setLevel(loglevel)
    logger.debug('Commandline Arguments:{}'.format(vars(args)))

    start = time.time()
    workdir = args.workdir
    cwd = os.getcwd()

    if workdir != cwd:
        mkdir(workdir, logger=logger)

    infile = args.input_bam_path or args.infile
    if not infile:
        sys.exit(not p.print_help())

    samples = read_csv(infile, args)
    store = args.output_path

    # Check available results
    if store:
        computed = ls_s3(store)
        computed = [op.basename(x).split('.')[0] for x in computed if \
                        x.endswith(".tred.vcf.gz")]
        remaining_samples = [x for x in samples if x[0] not in computed]

        logger.debug("Already computed on `{}`: {}".\
                        format(store, len(samples) - len(remaining_samples)))
        samples = remaining_samples

    logger.debug("Total samples: {}".format(len(samples)))

    task_args = []
    os.chdir(workdir)

    ref = args.ref
    repo = TREDsRepo(ref=ref, toy=args.toy)
    repo.set_ploidy(args.haploid)
    TRED_NAMES = repo.keys()
    TRED_NAMES.remove('AR')   # Disable one AR
    treds = args.tred or TRED_NAMES

    if args.toy:
        treds = ["toy"]

    samplekey_index = {}
    # Parallel processing
    for i, (samplekey, bam) in enumerate(samples):
        jsonfile = ".".join((samplekey, "json"))
        if args.checkexists and op.exists(jsonfile):
            logger.debug("File `{}` exists. Skipped computation."\
                            .format(jsonfile))
            continue
        task_args.append((samplekey, bam, repo, treds,
                          args.maxinsert, args.log))
        samplekey_index[samplekey] = i

    cpus = min(args.cpus, len(task_args))
    if cpus == 0:
        logger.debug("All jobs already completed.")
        sys.exit(0)

    logger.debug("Starting {} threads for {} jobs.".format(cpus, len(task_args)))

    if cpus == 1:  # Serial
        for ta in task_args:
            results = run(ta)
            if args.no_output:
                continue
            try:
                to_vcf(results, ref, treds=treds, store=store)
                to_json(results, ref, treds=treds, store=store)
            except KeyError:
                continue
    else:
        p = Pool(processes=cpus)
        for results in p.imap(run, task_args):
            if args.no_output:
                continue
            try:
                to_vcf(results, ref, treds=treds, store=store)
                to_json(results, ref, treds=treds, store=store)
            except KeyError:
                continue

    print >> sys.stderr, "Elapsed time={}"\
            .format(timedelta(seconds=time.time() - start))
    os.chdir(cwd)

    if args.cleanup:
        shutil.rmtree(workdir)
