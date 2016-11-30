import os.path as op
import pandas as pd


REF = "hg38"
REPO = op.join(op.dirname(__file__), 'data/TREDs.meta.{}.csv')


class TREDsRepo(dict):

    def __init__(self, ref=REF, toy=False):

        assert ref == REF, "Only supporting {} currently!".format(REF)
        repo = REPO.format(ref)
        if not op.exists(repo):
            assert ref == REF, "Ref {} not supported currently!".format(ref)

        df = pd.read_csv(repo)
        for i, row in df.iterrows():
            name = row["abbreviation"]
            self[name] = TRED(row)

        if toy:
            tr = self.get("HD")
            tr.name = "toy"
            tr.chromosome = "CHR4"
            tr.repeat_start = 1001
            self[tr.name] = tr

    def set_ploidy(self, haploid):
        if not haploid:
            return
        for k, v in self.items():
            if v.chromosome in haploid:
                v.ploidy = 1

    def get_info(self, tredName):
        tr = self.get(tredName)
        info = "END={};MOTIF={};NS=1;REF={};CR={};IH={};RL={};VT=STR".\
                    format(tr.repeat_end, tr.repeat, tr.ref_copy,
                           tr.cutoff_risk, tr.inheritance,
                           tr.ref_copy * len(tr.repeat))
        return tr.chromosome, tr.repeat_start, tr.ref_copy, tr.repeat, info


class TRED(object):

    def __init__(self, row):

        self.row = row
        self.name = row["abbreviation"]
        self.repeat = row["repeat"]
        repeat_location = row["repeat_location"]
        self.chromosome, repeat_location = repeat_location.split(":")
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
        self.ploidy = 2

    def __repr__(self):
        return "{} inheritance={} id={}_{}_{}".\
                format(self.name, self.inheritance,
                       self.chromosome, self.repeat_start, self.repeat)

    def __str__(self):
        return ";".join(str(x) for x in \
                (self.name, self.repeat,
                 self.chromosome, self.repeat_start, self.repeat_end,
                 self.prefix, self.suffix))
