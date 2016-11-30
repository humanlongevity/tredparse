#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
Report signficant calls - predisease and disease. When a list of vcf files are
given, a new tsv file will be written - otherwise will summarize calls based on
the given tsv file.
"""

import argparse
import os.path as op
import json
import math
import sys
import vcf
import pandas as pd

from collections import Counter
from multiprocessing import Pool, cpu_count

from tredparse.meta import TREDsRepo
from tredparse.utils import DefaultHelpParser


def left_truncate_text(a, maxcol=30):
    trim = lambda t: (t if not isinstance(t, basestring) \
                      or len(t) <= maxcol else "..." + t[-(maxcol - 3):])
    return [trim(x) for x in list(a)]


def get_tred_summary(df, tred, repo, na12878=False,
                     nogcnorxlinked=False, reads=False):
    pf1 = tred + ".1"
    pf2 = tred + ".2"
    tr = repo[tred]
    row = tr.row
    title = row["title"]
    inheritance = row["inheritance"]
    repeat = row["repeat"]
    repeat_location = row["repeat_location"]

    cutoff_prerisk, cutoff_risk = tr.cutoff_prerisk, tr.cutoff_risk

    if tr.is_recessive:  # recessive (AR, XLR)
        prerisk = df[(df[pf1] >= cutoff_prerisk) & (df[pf1] < cutoff_risk)]
        risk = df[df[pf1] >= cutoff_risk]
    else:
        prerisk = df[(df[pf2] >= cutoff_prerisk) & (df[pf2] < cutoff_risk)]
        risk = df[df[pf2] >= cutoff_risk]

    risk = risk.copy()
    if na12878:
        na_index = [x for x in df["SampleKey"] if "NA12878" in x]
        na = df[df["SampleKey"] == na_index[0]]
        risk = risk.append(na)

    n_prerisk = prerisk.shape[0]
    n_risk = risk.shape[0]
    calls = "Calls"
    risk[calls] = ["{}/{}".format(a, b) for (a, b) in zip(risk[pf1], risk[pf2])]

    columns = ["SampleKey", calls]
    if reads:
        columns.extend([tred + ".FR", tred + ".PR"])
        # Truncate the display of FR/PR
        risk[tred + ".FR"] = left_truncate_text(risk[tred + ".FR"])
        risk[tred + ".PR"] = left_truncate_text(risk[tred + ".PR"])

    pt = risk[columns]
    if (n_risk > 1 and na12878) or (n_risk > 0 and not na12878):
        print "[{}] - {}".format(tred, title)
        print "rep={}".format(repeat), "inherit={}".format(inheritance),\
              "cutoff={}".format(cutoff_risk), \
              "n={}".format(n_risk), \
              "loc={}".format(repeat_location)
        if ('N' in repeat or inheritance[0] == 'X') and nogcnorxlinked:
            print "GCN or X-linked disease. Patient reporting disabled."
        else:
            print pt.to_string(index=False)
        print

    # Allele frequency
    cnt = Counter()
    cnt.update(df[pf1])
    cnt.update(df[pf2])
    del cnt[-1]

    return tr, n_prerisk, n_risk, counts_to_af(cnt)


def counts_to_af(counts):
    return "{" + ",".join("{}:{}".format(int(k), v) for k, v in \
                sorted(counts.items()) if not math.isnan(k)) + "}"


def df_to_tsv(df, tsvfile):
    dd = ["SampleKey"]
    allowed_columns = ["1", "2", "label"]
    columns = dd + sorted([x for x in df.columns if (x not in dd) and \
                    any([x.endswith("." + z) for z in allowed_columns])])

    df = df.reindex_axis(columns, axis='columns')
    df.sort_values("SampleKey")
    df.to_csv(tsvfile, sep='\t', index=False)
    print >> sys.stderr, "TSV output written to `{}` (# samples={})"\
                .format(tsvfile, df.shape[0])


def vcf_to_df_worker(vcffile):
    samplekey = op.basename(vcffile).split(".")[0]
    reader = vcf.Reader(open(vcffile, "rb"))
    d = {'SampleKey': samplekey}
    for rec in reader:
        tr = rec.ID
        sample = rec.samples[0]
        a, b = sample["GB"].split("/")
        d[tr + ".1"] = int(a)
        d[tr + ".2"] = int(b)
        for k in ["PP", "FR", "PR"]:
            d[tr + "." + k] = sample[k]
        d[tr + ".label"] = sample["LABEL"]
    return d


def vcf_to_df(vcffiles, tsvfile, cpus):
    """
    Compile a number of vcf files into tsv file for easier manipulation.
    """
    df = pd.DataFrame()
    p = Pool(processes=cpus)
    results = []
    r = p.map_async(vcf_to_df_worker, vcffiles,
                    callback=results.append)
    r.wait()

    for res in results:
        df = df.append(res, ignore_index=True)
    return df


def json_to_df_worker(jsonfile):
    samplekey, bam, results = json.load(open(jsonfile))
    # We'll infer sample key from file names for now since the keys are not
    # properly populated in v0.6.4 and v0.6.5
    samplekey = op.basename(jsonfile).split(".")[0]
    d = {'SampleKey': samplekey}
    d.update(results)

    return d


def json_to_df(jsonfiles, tsvfile, cpus):
    """
    Compile a number of json files into tsv file for easier manipulation.
    """
    df = pd.DataFrame()
    p = Pool(processes=cpus)
    results = []
    r = p.map_async(json_to_df_worker, jsonfiles,
                    callback=results.append)
    r.wait()

    for res in results:
        df = df.append(res, ignore_index=True)
    return df


def main():
    p = DefaultHelpParser(description=__doc__, prog=__file__,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("files", nargs="*")
    p.add_argument('--tsv', help='Path to the tsv file',
                   default="out.tsv", required=True)
    p.add_argument('--na12878', default=False, action="store_true",
                   help="Include NA12878 in print out cases")
    p.add_argument('--nogcnorxlinked', default=False, action="store_true",
                   help="Do not report GCN or X-linked disease")
    p.add_argument('--reads', default=False, action="store_true",
                   help="Append reads information to output to help debug")
    p.add_argument('--cpus', default=cpu_count(),
                   help='Number of threads')
    args = p.parse_args()

    files = args.files
    tsvfile = args.tsv

    repo = TREDsRepo()
    alltreds = repo.keys()
    if files:
        cpus = min(len(files), args.cpus)
        jsonformat = files[0].endswith(".json")
        if jsonformat:
            df = json_to_df(files, tsvfile, cpus)
        else:
            df = vcf_to_df(files, tsvfile, cpus)
        df_to_tsv(df, tsvfile)
    else:
        df = pd.read_csv(tsvfile, sep="\t")

    if df.empty:
        print >> sys.stderr, "Dataframe empty - check input files"
        sys.exit(1)

    reportfile = tsvfile + ".report"
    summary = pd.DataFrame()
    for tred in alltreds:
        try:
            tr, n_prerisk, n_risk, af = \
                get_tred_summary(df, tred, repo,
                                 nogcnorxlinked=args.nogcnorxlinked,
                                 na12878=args.na12878,
                                 reads=args.reads)
        except KeyError as e:
            print >> sys.stderr, "{} not found. Skipped ({})".format(tred, e)
            continue

        tr = tr.row
        columns = ["abbreviation", "title", "motif", "inheritance",
                   "cutoff_prerisk", "cutoff_risk"]
        d = dict((c, tr[c]) for c in columns)
        d["n_prerisk"] = n_prerisk
        d["n_risk"] = n_risk
        d["allele_freq"] = af
        summary = summary.append(d, ignore_index=True)

    summary = summary.reindex_axis(columns + \
            ["n_prerisk", "n_risk", "allele_freq"], axis='columns')
    summary.to_csv(reportfile, sep="\t", index=False, float_format="%d")
    print >> sys.stderr, "Summary report written to `{}` (# samples={})"\
                    .format(reportfile, summary.shape[0])


if __name__ == '__main__':
    main()
