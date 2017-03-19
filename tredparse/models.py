import logging
import numpy as np

from math import exp
from bam_parser import PEextractor, FLANKMATCH, SPAN
from utils import datafile
from scipy.stats import gaussian_kde


# Global settings
MAX_PERIOD = 6
SMALL_VALUE = exp(-10)
MODEL_PREFIX = "illumina_v3.pcrfree"
STEPMODEL = datafile(MODEL_PREFIX + ".stepmodel")
NOISEMODEL = datafile(MODEL_PREFIX + ".stuttermodel")
MIN_PARTIAL_READS = 5
MIN_SPANNING_PAIRS = 5


class StepModel:
    """
    Contains information about step size distributions
    """
    def __init__(self, filename=STEPMODEL):
        self.non_unit_step_by_period = {}
        self.step_size_by_period = {}
        fp = open(filename, "r")
        for i in range(MAX_PERIOD):
            line = fp.readline()
            self.non_unit_step_by_period[i + 1] = float(line.strip())
        self.prob_increase = float(fp.readline().split("=")[1].strip())
        for i in range(MAX_PERIOD):
            line = fp.readline()
            self.step_size_by_period[i + 1] = \
                    np.array([float(x) for x in line.strip().split()[1:]])
        # For periods larger than MAX_PERIOD
        for i in range(MAX_PERIOD, 3 * MAX_PERIOD):
            self.step_size_by_period[i] = self.step_size_by_period[MAX_PERIOD]
        fp.close()


class NoiseModel:
    """
    Logistic model to predict mutation probability
    """
    def __init__(self, filename=NOISEMODEL):
        self.weights = []
        fp = open(filename)
        for i in xrange(MAX_PERIOD): # headers
            fp.next()
        for row in fp:
            row = row.strip()
            if not row:
                continue
            self.weights.append(float(row))

    def predict(self, x):
        z = self.weights[0]
        assert len(self.weights) == len(x) + 1
        for b, xx in zip(self.weights[1:], x):
            z += b * xx
        return 1.0 / (1 + exp(-1 * z))


def mean_std(a):
    if not a:
        return ""
    a = np.array(a)
    return "{:.0f}+/-{:.0f}bp".format(a.mean(), a.std())


class IntegratedCaller:
    """
    Models the stutter probability and calculates likelihood of a read set with
    full reads and partial reads.
    """
    def __init__(self, bamParser, score=1.0, gc=.68, maxinsert=100):
        self.tred = bamParser.tred
        self.stepmodel = StepModel()
        self.noisemodel = NoiseModel()
        self.readlen = bamParser.READLEN
        self.period = bamParser.repeatSize
        self.t1 = self.readlen - FLANKMATCH
        self.t2 = self.readlen - 2 * FLANKMATCH
        self.max_partial = self.t2
        self.score = score
        self.gc = gc
        self.df = bamParser.df
        self.ploidy = bamParser.ploidy
        self.maxinsert = maxinsert
        self.logger = logging.getLogger('IntegratedCaller')
        self.logger.setLevel(bamParser.inputParams.getLogLevel())

        pe = PEextractor(bamParser)
        self.pemodel = PEMaxLikModel(pe) if (len(pe.global_lens) >= 100 \
                    and len(pe.target_lens) >= MIN_SPANNING_PAIRS) else None
        self.PEDP = len(pe.target_lens)
        self.PEG = mean_std(pe.global_lens)
        self.PET = mean_std(pe.target_lens)
        self.logger.debug("Global pairs: {}{}, Target pairs: {}{}, Ref: {}bp".\
                            format(len(pe.global_lens), self.PEG,
                            len(pe.target_lens), self.PET, pe.ref))
        self.spanning_db = {}
        self.prepostfix_db = {}

    def pdf_spanning(self, h):
        if h in self.spanning_db:
            return self.spanning_db[h]
        a = np.zeros(SPAN)
        period = self.period
        score = self.score
        gc = self.gc
        stutter_prob = self.noisemodel.predict((period, h / period, gc, score))
        p = self.stepmodel.step_size_by_period[period] * stutter_prob
        lp = len(p)
        dev = lp / 2
        p[dev] = 1 - stutter_prob
        start, end = h - dev, h + dev + 1
        if start < 0:
            start = 0
        a[start: end] = p[lp - end + start: lp]
        self.spanning_db[h] = a   # Memoized
        return a

    def pdf_prepostfix(self, h):
        if h in self.prepostfix_db:
            return self.prepostfix_db[h]
        if h > self.max_partial:
            h = self.max_partial
        a = np.zeros(SPAN)
        c = 1. / (h + 1)
        a[:h] = c
        a += c * self.pdf_spanning(h)  # Add stutter to the last bin
        self.prepostfix_db[h] = a  # Memoized
        return a

    def get_alpha(self, h1, h2, mode=0):
        # What is the mixing probability of two distributions
        if mode == 0:  # Spanning reads
            s1 = max(0, self.t2 - h1)
            s2 = max(0, self.t2 - h2)
        else:
            s1 = min(h1, self.t1)
            s2 = min(h2, self.t1)
        return s1 * 1. / (s1 + s2) if (s1 + s2) else .5

    def evaluate_spanning(self, observations_spanning, h1, h2):
        pdf1_sp = self.pdf_spanning(h1)
        pdf2_sp = self.pdf_spanning(h2)
        alpha = self.get_alpha(h1, h2, mode=0)
        pdf_sp = alpha * pdf1_sp + (1 - alpha) * pdf2_sp
        ls = safe_log(pdf_sp)
        return sum(ls[k] * c for k, c in observations_spanning.items())

    def evaluate_prepostfix(self, observations_prepostfix, h1, h2):
        pdf1_pp = self.pdf_prepostfix(h1)
        pdf2_pp = self.pdf_prepostfix(h2)
        alpha = self.get_alpha(h1, h2, mode=1)
        pdf_pp = alpha * pdf1_pp + (1 - alpha) * pdf2_pp
        lp = safe_log(pdf_pp)
        s = sum(lp[k] * c for k, c in observations_prepostfix.items())
        return s

    def evaluate(self, observations_spanning, observations_prepostfix):
        max_full = max(observations_spanning.keys()) \
                        if observations_spanning else 0
        max_partial = max(observations_prepostfix.keys()) \
                        if observations_prepostfix else 0
        period = self.period
        total_partial = sum(c for k, c in observations_prepostfix.items())
        if total_partial < MIN_PARTIAL_READS:
            self.logger.debug("Partial reads: {} < {} (low depth of coverage)".\
                                format(total_partial, MIN_PARTIAL_READS))
            return None, None, None, None

        # Only run PE mode when partial reads suggest length unseen full
        # The 10 * self.period part is a hack - to avoid PE mode as much as
        # possible: say full - [16], partial - [20], then shall we run PE?
        # I don't want to run PE just because the partial is a stutter
        reads_above_full = sum(c for k, c in observations_prepostfix.items() \
                               if k > max_full + period)
        run_pe = (max_partial > max_full + 10 * period) and \
                  reads_above_full > 1 and \
                  self.pemodel is not None
        self.logger.debug("Max full: {}, max partial: {}, reads above full: {}, PE mode: {}"\
                           .format(max_full, max_partial, reads_above_full, run_pe))
        possible_alleles = set(observations_spanning.keys())
        if observations_prepostfix:
            if max_partial > self.max_partial:
                self.max_partial = max_partial
            possible_alleles.add(max_partial)
        if not possible_alleles:
            return None, None, None, None

        base_range = sorted(possible_alleles)
        extended_range = base_range + \
                range(max_partial + period, period * self.maxinsert + 1, period)
        # Rule 1: if ever seen a full read, then .1 allele must be chose from it
        # Rule 2: if not in PE mode, then .2 allele can just be chosen from seen
        h1range = base_range if max_full else extended_range
        h2range = base_range if not run_pe else extended_range
        mls = []
        for h1 in h1range:
            h2_range = [h1] if self.ploidy == 1 else h2range
            for h2 in h2_range:
                if h2 < h1:
                    continue
                ml1 = self.evaluate_spanning(observations_spanning, h1, h2) \
                                            if observations_spanning else 0
                ml2 = self.evaluate_prepostfix(observations_prepostfix, h1, h2) \
                                            if observations_prepostfix else 0
                ml3 = self.pemodel.evaluate(h1, h2) if run_pe else 0
                ml = ml1 + ml2 + ml3
                self.logger.debug(" ".join(str(x) for x in ("*" * 3,
                                            (h1 / self.period, h2 / self.period),
                                            ml1, ml2, ml3, ml)))
                mls.append((ml, (h1, h2)))

        # Calculate the expectation (disabled for now)
        '''
        h1_sum = h2_sum = total_prob = 0
        for ml, (h1, h2) in mls:
            mlexp = exp(ml)
            h1_sum += h1 / self.period * mlexp
            h2_sum += h2 / self.period * mlexp
            total_prob += mlexp

        self.logger.debug("h1_mean = {}, h2_mean = {}"\
                    .format(int(h1_sum / total_prob), int(h2_sum / total_prob)))
        '''

        lik, alleles = max(mls, key=lambda x: (x[0], -x[1][0]))
        all_liks = np.array([x[0] for x in mls])
        Q = self.calc_Q(lik, all_liks)
        PP = self.calc_PP(lik, all_liks, mls)
        return alleles, lik, Q, PP

    def calc_PP(self, lik, all_liks, mls):
        """
        :return: prob. of pathological, which is the cumulative prob. of size >=
        cutoff. Also look at inheritance pattern.
        """
        tred = self.tred
        self.logger.debug("Inheritance: {} Cutoff_risk: {}".\
                            format(tred.inheritance, tred.cutoff_risk))

        if tred.is_expansion:
            if not tred.is_recessive:  # Dominant
                pathological_liks = [x[0] for x in mls \
                        if max(x[1]) / self.period >= tred.cutoff_risk]
            else:                      # Recessive
                pathological_liks = [x[0] for x in mls \
                        if min(x[1]) / self.period >= tred.cutoff_risk]
        else:
            if not tred.is_recessive:  # Dominant
                pathological_liks = [x[0] for x in mls \
                        if min(x[1]) / self.period <= tred.cutoff_risk]
            else:                      # Recessive
                pathological_liks = [x[0] for x in mls \
                        if max(x[1]) / self.period <= tred.cutoff_risk]

        return np.exp(pathological_liks - lik).sum() \
                    / np.exp(all_liks - lik).sum()

    def calc_Q(self, lik, all_liks):
        '''
        :return: posterior probability of the observations

        Avoid underflow by using this trick:
        http://www.johndcook.com/blog/2012/07/26/avoiding-underflow-in-bayesian-computations/
        '''
        return 1 / np.exp(all_liks - lik).sum()

    def calc_label(self, alleles):
        '''
        :return: disease status based on the alleles and inheritance

        Possible values are 'ok', 'prerisk', 'risk', and 'missing'.
        '''
        tred = self.tred
        a, b = sorted(alleles)
        label = "ok" if a != -1 else "missing"
        cutoff_prerisk, cutoff_risk = tred.cutoff_prerisk, tred.cutoff_risk
        if tred.is_expansion:
            crit_allele = a if tred.is_recessive else b
            if cutoff_prerisk <= crit_allele < cutoff_risk:
                label = "prerisk"
            elif crit_allele >= cutoff_risk:
                label = "risk"
        else:
            crit_allele = b if tred.is_recessive else a
            if cutoff_prerisk <= crit_allele < cutoff_risk:
                label = "prerisk"
            elif crit_allele <= cutoff_risk:
                label = "risk"
        return label

    def call(self, **kwargs):
        '''
        :return: max likelihood estimate for diploid calls
        '''
        df = self.df
        observations_spanning = dict((k * self.period, int(v)) for k, v in \
                                 df["full"].to_dict().items() if int(v))
        observations_prepostfix = dict((k * self.period, int(v)) for k, v in \
                                 df["partial"].to_dict().items() if int(v))
        alleles, lik, Q, PP = self.evaluate(observations_spanning, observations_prepostfix)
        if not alleles:
            alleles = (-1, -1)
            lik = Q = PP = -1

        self.alleles = sorted([x / self.period for x in alleles])
        self.label = label = self.calc_label(self.alleles)
        self.Q = Q
        self.PP = PP
        self.logger.debug("ML estimate: alleles={} lik={} Q={} PP={} label={}".\
                            format(alleles, lik, Q, PP, label))


def safe_log(pdf):
    pdf[pdf < SMALL_VALUE] = SMALL_VALUE
    return np.log(pdf)


class PEMaxLikModel:

    def __init__(self, pe, beta=.1):
        self.x_grid = np.arange(SPAN)
        # Build KDE from global_lens
        kde = gaussian_kde(pe.global_lens)
        self.pdf = kde.evaluate(self.x_grid)
        self.cdf = np.cumsum(self.pdf)
        self.prior = self.pdf ** beta  # prior: beta=0 is uniform prior
        self.prior /= self.prior.sum()
        self.target_lens = pe.target_lens
        self.ref = pe.ref
        self.db = {}

    def roll(self, h):
        # As the target region shrink or expand, the expected distribution changes
        if h in self.db:  # Speed-up
            return self.db[h]

        shift = self.ref - h
        p = np.roll(self.pdf, shift)
        # Rollovers to the other sides not possible! RESET to 0
        if shift > 0:
            p[:shift] = SMALL_VALUE
        elif shift < 0:
            p[shift:] = SMALL_VALUE
        p /= p.sum()
        p *= self.prior
        p /= p.sum()
        self.db[h] = p
        return p

    def get_pdf(self, h1, h2):
        p1 = self.roll(h1)
        p2 = self.roll(h2)
        # find the mixture rate
        alpha1 = 1 - self.cdf[h1]
        alpha2 = 1 - self.cdf[h2]
        alpha = alpha1 / (alpha1 + alpha2)
        pdf = alpha * p1 + (1 - alpha) * p2
        return pdf

    def evaluate(self, h1, h2):
        mm = safe_log(self.get_pdf(h1, h2))
        return sum(mm[tl] for tl in self.target_lens)
