#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
Report signficant calls - predisease and disease. When VCF or JSON files are
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


def get_tred_summary(df, tred, repo, na12878=False, reads=False, minPP=.5):
    pf1 = tred + ".1"
    pf2 = tred + ".2"
    tr = repo[tred]
    row = tr.row
    title = row["title"]
    inheritance = row["inheritance"]
    repeat = row["repeat"]
    repeat_location = row["repeat_location"]

    cutoff_prerisk, cutoff_risk = tr.cutoff_prerisk, tr.cutoff_risk
    label = tred + ".label"
    pp = tred + ".PP"
    prerisk = df[df[label] == "prerisk"]
    risk = df[(df[label] == "risk") & (df[pp] > minPP)]

    risk = risk.copy()
    if na12878:
        na_index = [x for x in df["SampleKey"] if "NA12878" in x]
        na = df[df["SampleKey"] == na_index[0]]
        risk = risk.append(na)

    n_prerisk = prerisk.shape[0]
    n_risk = risk.shape[0]
    calls = "Calls"
    risk[calls] = ["{}/{}".format(int(a), int(b)) for (a, b) in zip(risk[pf1], risk[pf2])]

    columns = ["SampleKey", calls]
    if reads:
        columns.extend([tred + ".FR", tred + ".PR", tred + ".RR", pp])
        # Truncate the display of FR/PR
        risk[tred + ".FR"] = left_truncate_text(risk[tred + ".FR"])
        risk[tred + ".PR"] = left_truncate_text(risk[tred + ".PR"])
        risk[tred + ".RR"] = left_truncate_text(risk[tred + ".RR"])

    pt = risk[columns]
    if (n_risk > 1 and na12878) or (n_risk > 0 and not na12878):
        print "[{}] - {}".format(tred, title)
        print "rep={}".format(repeat), "inherit={}".format(inheritance),\
              "cutoff={}".format(cutoff_risk), \
              "n={}".format(n_risk), \
              "loc={}".format(repeat_location)
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


def df_to_tsv(df, tsvfile, allowed_columns=["1", "2", "label"]):
    dd = ["SampleKey"]
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
    js = json.load(open(jsonfile))
    samplekey = js['samplekey']
    results = js['tredCalls']
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
    p.add_argument('--tsv', default="out.tsv",
                   help="Path to the tsv file")
    p.add_argument('--columns', default="1,2,label",
                   help="Columns to extract, use comma to separate")
    p.add_argument('--NA12878', default=False, action="store_true",
                   help="Include NA12878 in print out cases")
    p.add_argument('--reads', default=False, action="store_true",
                   help="Append reads information to output to help debug")
    p.add_argument('--minPP', default=.5, type=float,
                   help="Minimum P(pathological) report cases")
    p.add_argument('--cpus', default=cpu_count(),
                   help='Number of threads')
    args = p.parse_args()

    files = args.files
    tsvfile = args.tsv
    columns = args.columns.split(",")

    repo = TREDsRepo()
    alltreds = repo.names
    if files:
        nfiles = len(files)
        cpus = min(nfiles, args.cpus)
        jsonformat = files[0].endswith(".json")
        suffix = "JSON" if jsonformat else "VCF"
        print >> sys.stderr, "Using {} cpus to parse {} {} files"\
                .format(cpus, nfiles, suffix)
        if jsonformat:
            df = json_to_df(files, tsvfile, cpus)
        else:
            df = vcf_to_df(files, tsvfile, cpus)
        df_to_tsv(df, tsvfile, allowed_columns=columns)
    else:
        df = pd.read_csv(tsvfile, sep="\t")

    if df.empty:
        print >> sys.stderr, "Dataframe empty - check input files"
        sys.exit(1)

    reportfile = tsvfile + ".report"
    summary = pd.DataFrame()
    total_prerisk = total_risk = total_loci = 0
    for tred in alltreds:
        try:
            tr, n_prerisk, n_risk, af = \
                get_tred_summary(df, tred, repo,
                                 na12878=args.NA12878,
                                 reads=args.reads, minPP=args.minPP)
            total_prerisk += n_prerisk
            total_risk += n_risk
            if n_risk:
                total_loci += 1
        except KeyError as e:
            print >> sys.stderr, "{} not found. Skipped ({})".format(tred, e)
            continue

        tr = tr.row
        columns = ["abbreviation", "title", "motif", "inheritance",
                   "cutoff_prerisk", "cutoff_risk"]
        d = dict((c, tr[c]) for c in columns[1:])
        d["abbreviation"] = tred
        d["n_prerisk"] = n_prerisk
        d["n_risk"] = n_risk
        d["allele_freq"] = af
        summary = summary.append(d, ignore_index=True)

    summary.to_csv(reportfile, sep="\t", index=False, float_format="%d")
    print >> sys.stderr, "Summary report written to `{}` (# samples={})"\
                    .format(reportfile, summary.shape[0])
    print >> sys.stderr, "Summary: n_prerisk={}, n_risk={}, n_affected_loci={}"\
                    .format(total_prerisk, total_risk, total_loci)


if __name__ == '__main__':
    main()
