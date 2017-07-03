#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
Copyright (c) 2015-2017 Human Longevity Inc.

Author: Haibao Tang <htang@humanlongevity.com>
License: Non-Commercial Use Only. For details, see `LICENSE` file

This file contains the statistical models applied in the STR caller. Four
submodels are available:

    - Spanning read
    - Partial read
    - Repeat-only read
    - Paired-end distances

Please see Supplemental methods for mathematical details.
"""

import logging
import numpy as np

from math import exp
from collections import defaultdict

from bam_parser import PEextractor, FLANKMATCH, SPAN
from utils import datafile, listify
from scipy.stats import gaussian_kde, poisson


# Global settings
MAX_PERIOD = 6
SMALL_VALUE = exp(-10)
REALLY_SMALL_VALUE = exp(-100)
MODEL_PREFIX = "illumina_v3.pcrfree"
STEPMODEL = datafile(MODEL_PREFIX + ".stepmodel")
NOISEMODEL = datafile(MODEL_PREFIX + ".stuttermodel")
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


def histogram(a, bins=40):
    if not a:
        return ""
    ar, br = np.histogram(a, bins=bins, range=(0, SPAN))
    return ",".join(["{}:{}".format(int(b), a) for (a, b) in zip(ar, br)])


class IntegratedCaller:
    """
    Models the stutter probability and calculates likelihood of a read set with
    full reads and partial reads.
    """
    def __init__(self, bamParser, score=1.0, gc=.68,
                       maxinsert=300, fullsearch=False):

        self.tred = bamParser.tred
        self.stepmodel = StepModel()
        self.noisemodel = NoiseModel()
        self.readlen = bamParser.READLEN
        self.period = bamParser.repeatSize
        self.t1 = self.readlen - FLANKMATCH
        self.t2 = self.readlen - 2 * FLANKMATCH
        self.t3 = self.readlen - 3 * FLANKMATCH
        self.max_partial = self.t2
        self.score = score
        self.gc = gc
        self.counts = bamParser.counts
        self.rept = bamParser.rept
        self.ploidy = bamParser.ploidy
        self.half_depth = bamParser.depth / 2
        self.maxinsert = maxinsert
        self.fullsearch = fullsearch
        self.logger = logging.getLogger('IntegratedCaller')
        self.logger.setLevel(bamParser.inputParams.getLogLevel())

        pe = PEextractor(bamParser)
        #print sorted(pe.target_lens)
        self.pemodel = PEMaxLikModel(pe) if (len(pe.global_lens) >= 100 \
                    and len(pe.target_lens) >= MIN_SPANNING_PAIRS) else None
        self.PEDP = len(pe.target_lens)
        self.PEG = mean_std(pe.global_lens)
        self.PET = mean_std(pe.target_lens)
        self.P_PEG = histogram(pe.global_lens)
        self.P_PET = histogram(pe.target_lens)
        self.logger.debug("Global pairs: {} ({}), Target pairs: {} ({}), Ref: {}bp".\
                            format(len(pe.global_lens), self.PEG,
                            len(pe.target_lens), self.PET, pe.ref))
        self.spanning_db = {}
        self.partial_db = {}

        # Track probability distributions in JSON
        self.P_h1 =""
        self.P_h2 = ""
        self.P_h1h2 = ""

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
        if end > SPAN:
            end = SPAN
        a[start: end] = p[lp - end + start: lp]
        self.spanning_db[h] = a   # Memoized
        return a

    def pdf_partial(self, h):
        if h in self.partial_db:
            return self.partial_db[h]
        if h > self.max_partial:
            h = self.max_partial
        a = np.zeros(SPAN)
        c = 1. / (h + 1)
        a[:h] = c
        a += c * self.pdf_spanning(h)  # Add stutter to the last bin
        self.partial_db[h] = a  # Memoized
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

    def evaluate_spanning(self, obs_spanning, h1, h2):
        pdf1_sp = self.pdf_spanning(h1)
        pdf2_sp = self.pdf_spanning(h2)
        alpha = self.get_alpha(h1, h2, mode=0)
        pdf_sp = alpha * pdf1_sp + (1 - alpha) * pdf2_sp
        ls = safe_log(pdf_sp)
        return sum(ls[k] * c for k, c in obs_spanning.items())

    def evaluate_partial(self, obs_partial, h1, h2):
        pdf1_pp = self.pdf_partial(h1)
        pdf2_pp = self.pdf_partial(h2)
        alpha = self.get_alpha(h1, h2, mode=1)
        pdf_pp = alpha * pdf1_pp + (1 - alpha) * pdf2_pp
        lp = safe_log(pdf_pp)
        s = sum(lp[k] * c for k, c in obs_partial.items())
        return s

    def evaluate_rept(self, n_obs_rept, h1, h2):
        """
        We expect to find a total of N REPT reads in this region, where N
        follows Poisson distribution with mean mu, where:
        mu = (repeat_length - read_length) * half_depth / read_length

        Note that this is defined only if repeat_length > read_length.
        """
        d1 = max(h1 - self.readlen, 1)
        d2 = max(h2 - self.readlen, 1)
        mu = (d1 + d2) * self.half_depth / self.readlen
        prob = poisson.pmf(n_obs_rept, mu)
        return np.log(max(prob, REALLY_SMALL_VALUE))

    def evaluate(self, obs_spanning, obs_partial, n_obs_rept):
        max_full = max(obs_spanning.keys()) if obs_spanning else 0
        max_partial = max(obs_partial.keys()) if obs_partial else 0
        period = self.period

        # Only run PE mode when partial reads suggest length unseen full
        # The 10 * self.period part is a hack - to avoid PE mode as much as
        # possible: say full - [16], partial - [20], then shall we run PE?
        # I don't want to run PE just because the partial is a stutter
        reads_above_full = sum(c for k, c in obs_partial.items() \
                               if k > max_full + period)
        run_pe = max_partial >= self.t3 and \
                 reads_above_full > 1 and \
                 (self.pemodel is not None)
        self.logger.debug("Max full: {}, max partial: {}, reads above full: {}, PE mode: {}"\
                           .format(max_full, max_partial, reads_above_full, run_pe))
        possible_alleles = set(obs_spanning.keys())
        if obs_partial:
            if max_partial > self.max_partial:
                self.max_partial = max_partial
            possible_alleles.add(max_partial)
        if not possible_alleles:
            return None, None, None, None

        # === Grid search for ML estimates ===
        # Rule 1: if ever seen a full read, then .1 allele must be chose from it
        # Rule 2: if not in PE mode, then .2 allele can just be chosen from seen
        base_range = sorted(possible_alleles)
        extended_range = base_range + \
                range(max_partial + period, period * self.maxinsert + 1, period)
        if self.fullsearch:
            h1range = h2range = range(period, period * self.maxinsert + 1, period)
        else:
            h1range = base_range if max_full else extended_range
            h2range = extended_range if (n_obs_rept or run_pe) else base_range

        mls = []
        for h1 in h1range:
            h2_range = [h1] if self.ploidy == 1 else h2range
            for h2 in h2_range:
                if h2 < h1:
                    continue
                ml1 = self.evaluate_spanning(obs_spanning, h1, h2) if obs_spanning else 0
                ml2 = self.evaluate_partial(obs_partial, h1, h2) if obs_partial else 0
                ml3 = self.evaluate_rept(n_obs_rept, h1, h2)
                ml4 = self.pemodel.evaluate(h1, h2) if run_pe else 0
                ml = ml1 + ml2 + ml3 + ml4
                self.logger.debug(" ".join(str(x) for x in ("*" * 3,
                                            (h1 / self.period, h2 / self.period),
                                            ml1, ml2, ml3, ml4, ml)))
                mls.append((ml, (h1, h2)))

        # Calculate the confidence interval (CI), we use the CDF of the
        # marginal probabilities of P(h1) and P(h2)
        P_h1 = defaultdict(float)
        P_h2 = defaultdict(float)
        P_h1h2 = {}             # Joint distribution
        max_ml = max(mls)[0]    # Prevent underflow
        for ml, (h1, h2) in mls:
            mlexp = exp(ml - max_ml)
            P_h1[h1] += mlexp
            P_h2[h2] += mlexp
            P_h1h2[(h1, h2)] = mlexp

        h1_lo, h1_hi = self.calc_CI(P_h1)
        h2_lo, h2_hi = self.calc_CI(P_h2)
        h1_lo, h1_hi = h1_lo / self.period, h1_hi / self.period
        h2_lo, h2_hi = h2_lo / self.period, h2_hi / self.period

        self.logger.debug("CI(h1) = {} - {}".format(h1_lo, h1_hi))
        self.logger.debug("CI(h2) = {} - {}".format(h2_lo, h2_hi))

        self.P_h1 = self.sparsify(P_h1)
        self.P_h2 = self.sparsify(P_h2)
        self.P_h1h2 = self.sparsify(P_h1h2)

        lik, alleles = max(mls, key=lambda x: (x[0], -x[1][0]))
        all_liks = np.array([x[0] for x in mls])
        PP = self.calc_PP(lik, all_liks, mls)
        return alleles, lik, PP, (h1_lo, h1_hi, h2_lo, h2_hi)

    def sparsify(self, P, epsilon=SMALL_VALUE):
        """
        Returns the sparsified distribution, anything smaller than epsilon is
        considered as zero and NOT recorded.
        """
        Z = {}
        total = sum(v for v in P.values())
        for k, v in P.items():
            if v < SMALL_VALUE:
                continue
            k = [x / self.period for x in listify(k)]
            k = ",".join(str(x) for x in k)
            Z[k] = v / total
        return Z

    def calc_CI(self, P):
        """
        Returns the confidence interval (CI) given a probability distribution P,
        where P is a dict. We go through all the key, val pairs in the dict,
        then report the value at .025 and .975.
        """
        cum_sum = 0
        alpha, beta = .025, .975
        lo, hi = 0, 0
        in_range = False
        total_prob = sum(P.values())
        for k, v in sorted(P.items()):
            cum_sum += v
            #self.logger.debug("=> {} {} {} {}".format(k, v, cum_sum, total_prob))
            if (not in_range) and cum_sum > alpha * total_prob:
                in_range = True
                lo = k
            if cum_sum > beta * total_prob:
                break
        hi = k

        return lo, hi

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

        pathological_liks = np.array(pathological_liks)
        return min(1, np.exp(pathological_liks - lik).sum() \
                    / np.exp(all_liks - lik).sum())

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
            elif 0 < crit_allele <= cutoff_risk:
                label = "risk"
        return label

    def call(self, **kwargs):
        '''
        :return: max likelihood estimate for diploid calls
        '''
        counts = self.counts
        obs_spanning = dict((k * self.period, v) for k, v in
                            counts["FULL"].items())
        obs_partial = dict((k * self.period, v) for k, v in
                            counts["PREF"].items())
        n_obs_rept = self.rept
        alleles, lik, PP, CIs = self.evaluate(obs_spanning, obs_partial, n_obs_rept)

        if not alleles:
            alleles = (-1, -1)
            lik = PP = -1

        self.alleles = sorted([x / self.period for x in alleles])
        self.label = label = self.calc_label(self.alleles)
        self.CI = "{}-{}|{}-{}".format(*CIs) if CIs else ""
        self.PP = PP
        self.logger.debug("ML estimate: alleles={} loglikelihood={} PP={} label={}".\
                            format(self.alleles, lik, PP, label))


def safe_log(pdf):
    """
    Prevents taking the log of zeros.
    """
    pdf[pdf < SMALL_VALUE] = SMALL_VALUE
    return np.log(pdf)


class PEMaxLikModel:

    def __init__(self, pe):
        self.MINPE = pe.MINPE
        self.x_grid = np.arange(SPAN)
        # Build KDE from global_lens
        kde = gaussian_kde(pe.global_lens)
        pdf = kde.evaluate(self.x_grid)
        #pdf[pdf < SMALL_VALUE] = SMALL_VALUE
        self.pdf = pdf / pdf.sum()
        #self.cdf = np.cumsum(self.pdf)
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
        # Also not likely to get any PE distance below MINPE
        p[:self.MINPE] = SMALL_VALUE
        # Normalize to 1
        #p /= p.sum()
        self.db[h] = p
        return p

    def get_pdf(self, h1, h2):
        p1 = self.roll(h1)
        p2 = self.roll(h2)
        # find the mixture rate
        #alpha1 = 1 - self.cdf[h1 + 2 * FLANKMATCH + 1]
        #alpha2 = 1 - self.cdf[h2 + 2 * FLANKMATCH + 1]
        #alpha = alpha1 / (alpha1 + alpha2)
        alpha = .5
        pdf = alpha * p1 + (1 - alpha) * p2
        return pdf

    def evaluate(self, h1, h2):
        mm = safe_log(self.get_pdf(h1, h2))
        return sum(mm[tl] for tl in self.target_lens)
