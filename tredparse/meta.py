#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
Handles the STR database and extractions of various properties of a particular
STR locus.
"""

import json
import pandas as pd

from .utils import datafile


REF = "hg38"
REPO = datafile("TREDs.meta.csv")
HLI_BAMS = datafile("HLI_bams.csv.gz")


class TREDsRepo(dict):

    def __init__(self, ref=REF, toy=False):

        self.ref = ref
        df = pd.read_csv(REPO, index_col=0)
        self.names = []
        for name, row in df.iterrows():
            self[name] = TRED(name, row, ref=ref)
            self.names.append(name)
        self.df = df

        if toy:
            tr = self.get("HD")
            tr.name = "toy"
            tr.chr = "CHR4"
            tr.repeat_start = 1001
            tr.repeat_end = 1057
            self[tr.name] = tr

    def to_json(self):
        s = self.df.to_json(orient='index')
        s = s.decode('windows-1252').encode('utf8')
        s = json.dumps(json.loads(s), sort_keys=True, indent=2)
        return s

    def set_ploidy(self, haploid):
        if not haploid:
            return
        for k, v in self.items():
            if v.chr in haploid:
                v.ploidy = 1

    def get_info(self, tredName):
        tr = self.get(tredName)
        info = "END={};MOTIF={};NS=1;REF={};CR={};IH={};RL={};VT=STR".\
                    format(tr.repeat_end, tr.repeat, tr.ref_copy,
                           tr.cutoff_risk, tr.inheritance,
                           tr.ref_copy * len(tr.repeat))
        return tr.chr, tr.repeat_start, tr.ref_copy, tr.repeat, info


class TRED(object):

    def __init__(self, name, row, ref=REF):

        self.row = row
        self.name = name
        self.repeat = row["repeat"]
        repeat_location_field = "repeat_location"
        if ref != REF:
            repeat_location_field += "." + ref.split("_")[0]
        repeat_location = row[repeat_location_field]
        if "_nochr" in ref:  # Some reference version do not have chr
            repeat_location = repeat_location.replace("chr", "")
        self.chr, repeat_location = repeat_location.split(":")
        repeat_start, repeat_end = repeat_location.split("-")
        self.repeat_start = int(repeat_start)
        self.repeat_end = int(repeat_end)
        self.ref_copy = (self.repeat_end - self.repeat_start + 1) / len(self.repeat)
        self.prefix = row["prefix"]
        self.suffix = row["suffix"]
        self.cutoff_prerisk = row["cutoff_prerisk"]
        self.cutoff_risk = row["cutoff_risk"]
        self.inheritance = row["inheritance"]
        self.is_xlinked = self.inheritance[0] == 'X'
        self.is_recessive = self.inheritance[-1] == 'R'
        self.is_expansion = row["mutation_nature"] == 'increase'
        self.ploidy = 2

    def __repr__(self):
        return "{} inheritance={} id={}_{}_{}".\
                format(self.name, self.inheritance,
                       self.chr, self.repeat_start, self.repeat)

    def __str__(self):
        return ";".join(str(x) for x in \
                (self.name, self.repeat,
                 self.chr, self.repeat_start, self.repeat_end,
                 self.prefix, self.suffix))
