#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
Copyright (c) 2015-2017 Human Longevity Inc.

Author: Haibao Tang <htang@humanlongevity.com>
License: Non-Commercial Use Only. For details, see `LICENSE` file

This file contains utility subroutines, initially from `jcvi` Python libraries.
Mostly related to plotting and used by `tredplot.py`.
"""

import errno
import os
import time
import os.path as op
import shutil
import signal
import sys
import logging
import fnmatch

from subprocess import PIPE, call
from optparse import OptionParser as OptionP, OptionGroup, SUPPRESS_HELP

from tredparse import __copyright__, __version__

# http://newbebweb.blogspot.com/2012/02/python-head-ioerror-errno-32-broken.html
nobreakbuffer = lambda: signal.signal(signal.SIGPIPE, signal.SIG_DFL)
nobreakbuffer()
os.environ["LC_ALL"] = "C"
JCVIHELP = "TREDPARSE v{} [{}]\n".format(__version__, __copyright__)


class ActionDispatcher (object):
    """
    This class will be invoked
    a) when either a directory is run via __main__, listing all SCRIPTs
    b) when a script is run directly, listing all ACTIONs

    This is controlled through the meta variable, which is automatically
    determined in get_meta().
    """
    def __init__(self, actions):

        self.actions = actions
        if not actions:
            actions = [(None, None)]
        self.valid_actions, self.action_helps = zip(*actions)

    def get_meta(self):
        args = splitall(sys.argv[0])[-3:]
        args[-1] = args[-1].replace(".py", "")
        meta = "SCRIPT" if args[-1] == "__main__" else "ACTION"
        return meta, args

    def print_help(self):
        meta, args = self.get_meta()
        if meta == "SCRIPT":
            args[-1] = meta
        else:
            args[-1] += " " + meta

        help = "Usage:\n    python -m {0}\n\n\n".format(".".join(args))
        help += "Available {0}s:\n".format(meta)
        max_action_len = max(len(action) for action, ah in self.actions)
        for action, action_help in sorted(self.actions):
            action = action.rjust(max_action_len + 4)
            help += " | ".join((action, action_help[0].upper() + \
                                        action_help[1:])) + '\n'
        help += "\n" + JCVIHELP

        sys.stderr.write(help)
        sys.exit(1)

    def dispatch(self, globals):
        from difflib import get_close_matches
        meta = "ACTION"  # function is only invoked for listing ACTIONs
        if len(sys.argv) == 1:
            self.print_help()

        action = sys.argv[1]

        if not action in self.valid_actions:
            print >> sys.stderr, "[error] {0} not a valid {1}\n".format(action, meta)
            alt = get_close_matches(action, self.valid_actions)
            print >> sys.stderr, "Did you mean one of these?\n\t{0}\n".\
                                format(", ".join(alt))
            self.print_help()

        globals[action](sys.argv[2:])


class OptionParser (OptionP):

    def __init__(self, doc):

        OptionP.__init__(self, doc, epilog=JCVIHELP)

    def parse_args(self, args=None):
        dests = set()
        ol = []
        for g in [self] + self.option_groups:
            ol += g.option_list
        for o in ol:
            if o.dest in dests:
                continue
            self.add_help_from_choices(o)
            dests.add(o.dest)

        return OptionP.parse_args(self, args)

    def add_help_from_choices(self, o):
        if o.help == SUPPRESS_HELP:
            return

        default_tag = "%default"
        assert o.help, "Option {0} do not have help string".format(o)
        help_pf = o.help[:1].upper() + o.help[1:]
        if "[" in help_pf:
            help_pf = help_pf.rsplit("[", 1)[0]
        help_pf = help_pf.strip()

        if o.type == "choice":
            if o.default is None:
                default_tag = "guess"
            ctext = "|".join(sorted(str(x) for x in o.choices))
            if len(ctext) > 100:
                ctext = ctext[:100] + " ... "
            choice_text = "must be one of {0}".format(ctext)
            o.help = "{0}, {1} [default: {2}]".format(help_pf,
                            choice_text, default_tag)
        else:
            o.help = help_pf
            if o.default is None:
                default_tag = "disabled"
            if o.get_opt_string() not in ("--help", "--version") \
                        and o.action != "store_false":
                o.help += " [default: {0}]".format(default_tag)

    def set_grid(self):
        """
        Add --grid options for command line programs
        """
        self.add_option("--grid", dest="grid",
                default=False, action="store_true",
                help="Run on the grid [default: %default]")

    def set_grid_opts(self, array=False, vcode="99999"):
        queue_choices = ("default", "fast", "medium", "himem")
        valid_pcodes = popen("qconf -sprjl", debug=False).read().strip().split("\n")
        valid_pcodes.append(vcode)

        group = OptionGroup(self, "Grid parameters")
        group.add_option("-P", dest="pcode", default=vcode, choices=valid_pcodes,
                        help="Specify accounting project code [default: %default]")
        group.add_option("-l", dest="queue", default="default", choices=queue_choices,
                        help="Name of the queue [default: %default]")
        group.add_option("-t", dest="threaded", default=None, type="int",
                        help="Append '-pe threaded N' [default: %default]")
        if array:
            group.add_option("-c", dest="concurrency", type="int",
                            help="Append task concurrency limit '-tc N'")
        group.add_option("-d", dest="outdir", default=".",
                        help="Specify directory to store grid output/error files")
        group.add_option("-N", dest="name", default=None,
                        help="Specify descriptive name for the job [default: %default]")
        group.add_option("-H", dest="hold_jid", default=None,
                        help="Define the job dependency list [default: %default]")
        self.add_option_group(group)

    def set_table(self, sep=",", align=False):
        group = OptionGroup(self, "Table formatting")
        group.add_option("--sep", default=sep, help="Separator")
        if align:
            group.add_option("--noalign", dest="align", default=True,
                             action="store_false", help="Cell alignment")
        else:
            group.add_option("--align", default=False,
                             action="store_true", help="Cell alignment")
        self.add_option_group(group)

    def set_params(self, prog=None, params=""):
        """
        Add --params options for given command line programs
        """
        dest_prog = "to {0}".format(prog) if prog else ""
        self.add_option("--params", dest="extra", default=params,
                help="Extra parameters to pass {0}".format(dest_prog) + \
                     " (these WILL NOT be validated)")

    def set_outfile(self, outfile="stdout"):
        """
        Add --outfile options to print out to filename.
        """
        self.add_option("-o", "--outfile", default=outfile,
                help="Outfile name [default: %default]")

    def set_outdir(self, outdir="."):
        self.add_option("--outdir", default=outdir,
                help="Specify output directory")

    def set_email(self):
        """
        Add --email option to specify an email address
        """
        self.add_option("--email", default=get_email_address(),
                help='Specify an email address [default: "%default"]')

    def set_tmpdir(self, tmpdir=None):
        """
        Add --temporary_directory option to specify unix `sort` tmpdir
        """
        self.add_option("-T", "--tmpdir", default=tmpdir,
                help="Use temp directory instead of $TMP [default: %default]")

    def set_cpus(self, cpus=0):
        """
        Add --cpus options to specify how many threads to use.
        """
        from multiprocessing import cpu_count

        max_cpus = cpu_count()
        if not 0 < cpus < max_cpus:
            cpus = max_cpus
        self.add_option("--cpus", default=cpus, type="int",
                     help="Number of CPUs to use, 0=unlimited [default: %default]")

    def set_db_opts(self, dbname="mta4", credentials=True):
        """
        Add db connection specific attributes
        """
        from jcvi.utils.db import valid_dbconn, get_profile

        self.add_option("--db", default=dbname, dest="dbname",
                help="Specify name of database to query [default: %default]")
        self.add_option("--connector", default="Sybase", dest="dbconn",
                choices=valid_dbconn.keys(), help="Specify database connector [default: %default]")
        hostname, username, password = get_profile()
        if credentials:
            self.add_option("--hostname", default=hostname,
                    help="Specify hostname [default: %default]")
            self.add_option("--username", default=username,
                    help="Username to connect to database [default: %default]")
            self.add_option("--password", default=password,
                    help="Password to connect to database [default: %default]")
        self.add_option("--port", type="int",
                help="Specify port number [default: %default]")

    def set_aws_opts(self, store="hli-mv-data-science/htang"):
        from jcvi.utils.aws import s3ify
        store = s3ify(store)
        group = OptionGroup(self, "AWS and Docker options")
        self.add_option_group(group)
        # https://github.com/hlids/infrastructure/wiki/Docker-calling-convention
        group.add_option("--sample_id", help="Sample ID")
        group.add_option("--workflow_execution_id", help="Workflow execution ID")
        group.add_option("--input_bam_path", help="Input BAM location (s3 ok)")
        group.add_option("--output_path", default=store, help="Output s3 path")
        group.add_option("--workdir", default=os.getcwd(), help="Specify work dir")
        group.add_option("--nocleanup", default=False, action="store_true",
                     help="Don't clean up after done")

    def set_stripnames(self, default=True):
        if default:
            self.add_option("--no_strip_names", dest="strip_names",
                action="store_false", default=True,
                help="do not strip alternative splicing "
                "(e.g. At5g06540.1 -> At5g06540)")
        else:
            self.add_option("--strip_names",
                action="store_true", default=False,
                help="strip alternative splicing "
                "(e.g. At5g06540.1 -> At5g06540)")

    def set_fixchrnames(self, orgn="medicago"):
        self.add_option("--fixchrname", default=orgn, dest="fix_chr_name",
                help="Fix quirky chromosome names [default: %default]")

    def set_SO_opts(self):
        verifySO_choices = ("verify", "resolve:prefix", "resolve:suffix")
        self.add_option("--verifySO", choices=verifySO_choices,
                help="Verify validity of GFF3 feature type against the SO; " + \
                     "`resolve` will try to converge towards a valid SO " + \
                     "term by removing elements from the feature type " + \
                     "string by splitting at underscores. Example: " + \
                     "`mRNA_TE_gene` resolves to `mRNA` using 'resolve:prefix'")

    def set_beds(self):
        self.add_option("--qbed", help="Path to qbed")
        self.add_option("--sbed", help="Path to sbed")

    def set_histogram(self, vmin=0, vmax=None, bins=20,
                      xlabel="value", title=None):
        self.add_option("--vmin", default=vmin, type="int",
                        help="Minimum value, inclusive")
        self.add_option("--vmax", default=vmax, type="int",
                        help="Maximum value, inclusive")
        self.add_option("--bins", default=bins, type="int",
                        help="Number of bins to plot in the histogram")
        self.add_option("--xlabel", default=xlabel, help="Label on the X-axis")
        self.add_option("--title", default=title, help="Title of the plot")

    def set_sam_options(self, extra=True, bowtie=False):
        self.add_option("--sam", dest="bam", default=True, action="store_false",
                     help="Write to SAM file instead of BAM")
        self.add_option("--uniq", default=False, action="store_true",
                     help="Keep only uniquely mapped [default: %default]")
        if bowtie:
            self.add_option("--mapped", default=False, action="store_true",
                         help="Keep mapped reads [default: %default]")
        self.add_option("--unmapped", default=False, action="store_true",
                     help="Keep unmapped reads [default: %default]")
        if extra:
            self.set_cpus()
            self.set_params()

    def set_mingap(self, default=100):
        self.add_option("--mingap", default=default, type="int",
                     help="Minimum size of gaps [default: %default]")

    def set_align(self, pctid=None, hitlen=None, pctcov=None, evalue=None, \
            compreh_pctid=None, compreh_pctcov=None, intron=None, bpsplice=None):
        if pctid is not None:
            self.add_option("--pctid", default=pctid, type="int",
                     help="Sequence percent identity [default: %default]")
        if hitlen is not None:
            self.add_option("--hitlen", default=hitlen, type="int",
                     help="Minimum overlap length [default: %default]")
        if pctcov is not None:
            self.add_option("--pctcov", default=pctcov, type="int",
                     help="Percentage coverage cutoff [default: %default]")
        if evalue is not None:
            self.add_option("--evalue", default=evalue, type="float",
                     help="E-value cutoff [default: %default]")
        if compreh_pctid is not None:
            self.add_option("--compreh_pctid", default=pctid, type="int",
                     help="Sequence percent identity cutoff used to " + \
                          "build PASA comprehensive transcriptome [default: %default]")
        if compreh_pctcov is not None:
            self.add_option("--compreh_pctcov", default=compreh_pctcov, \
                     type="int", help="Percent coverage cutoff used to " + \
                     "build PASA comprehensive transcriptome [default: %default]")
        if intron is not None:
            self.add_option("--intron", default=intron, type="int",
                    help="Maximum intron length used for mapping " + \
                         "[default: %default]")
        if bpsplice is not None:
            self.add_option("--bpsplice", default=bpsplice, type="int",
                    help="Number of bp of perfect splice boundary " + \
                         "[default: %default]")

    def set_image_options(self, args=None, figsize="6x6", dpi=300,
                          format="pdf", font="Helvetica", palette="deep",
                          style="darkgrid", cmap="jet"):
        """
        Add image format options for given command line programs.
        """
        allowed_format = ("emf", "eps", "pdf", "png", "ps", \
                          "raw", "rgba", "svg", "svgz")
        allowed_fonts = ("Helvetica", "Palatino", "Schoolbook", "Arial")
        allowed_styles = ("darkgrid", "whitegrid", "dark", "white", "ticks")
        allowed_diverge = ("BrBG", "PiYG", "PRGn", "PuOr", "RdBu", \
                           "RdGy", "RdYlBu", "RdYlGn", "Spectral")

        group = OptionGroup(self, "Image options")
        self.add_option_group(group)

        group.add_option("--figsize", default=figsize,
                help="Figure size `width`x`height` in inches [default: %default]")
        group.add_option("--dpi", default=dpi, type="int",
                help="Physical dot density (dots per inch) [default: %default]")
        group.add_option("--format", default=format, choices=allowed_format,
                help="Generate image of format [default: %default]")
        group.add_option("--font", default=font, choices=allowed_fonts,
                help="Font name")
        group.add_option("--style", default=style, choices=allowed_styles,
                help="Axes background")
        group.add_option("--diverge", default="PiYG", choices=allowed_diverge,
                help="Contrasting color scheme")
        group.add_option("--cmap", default=cmap, help="Use this color map")

        if args is None:
            args = sys.argv[1:]

        opts, args = self.parse_args(args)

        assert opts.dpi > 0
        assert "x" in opts.figsize

        setup_theme(style=opts.style, font=opts.font)

        return opts, args, ImageOptions(opts)

    def set_depth(self, depth=50):
        self.add_option("--depth", default=depth, type="float",
                     help="Desired depth [default: %default]")

    def set_rclip(self, rclip=0):
        self.add_option("--rclip", default=rclip, type="int",
                help="Pair ID is derived from rstrip N chars [default: %default]")

    def set_chr(self, chr=",".join([str(x) for x in range(1, 23)] + ["X", "Y", "MT"])):
        self.add_option("--chr", default=chr, help="Chromosomes to process")

    def set_ref(self, ref="/mnt/ref"):
        self.add_option("--ref", default=ref, help="Reference folder")

    def set_cutoff(self, cutoff=0):
        self.add_option("--cutoff", default=cutoff, type="int",
                help="Distance to call valid links between mates")

    def set_mateorientation(self, mateorientation=None):
        self.add_option("--mateorientation", default=mateorientation,
                choices=("++", "--", "+-", "-+"),
                help="Use only certain mate orientations [default: %default]")

    def set_mates(self, rclip=0, cutoff=0, mateorientation=None):
        self.set_rclip(rclip=rclip)
        self.set_cutoff(cutoff=cutoff)
        self.set_mateorientation(mateorientation=mateorientation)

    def set_bedpe(self):
        self.add_option("--norc", dest="rc", default=True, action="store_false",
                     help="Do not reverse complement, expect innie reads")
        self.add_option("--minlen", default=2000, type="int",
                     help="Minimum insert size")
        self.add_option("--maxlen", default=8000, type="int",
                     help="Maximum insert size")
        self.add_option("--dup", default=10, type="int",
                     help="Filter duplicates with coordinates within this distance")

    def set_fastq_names(self):
        self.add_option("--names", default="*.fq,*.fastq,*.fq.gz,*.fastq.gz",
                     help="File names to search, use comma to separate multiple")

    def set_pairs(self):
        """
        %prog pairs <blastfile|samfile|bedfile>

        Report how many paired ends mapped, avg distance between paired ends, etc.
        Paired reads must have the same prefix, use --rclip to remove trailing
        part, e.g. /1, /2, or .f, .r, default behavior is to truncate until last
        char.
        """
        self.set_usage(self.set_pairs.__doc__)

        self.add_option("--pairsfile", default=None,
                help="Write valid pairs to pairsfile [default: %default]")
        self.add_option("--nrows", default=200000, type="int",
                help="Only use the first n lines [default: %default]")
        self.set_mates()
        self.add_option("--pdf", default=False, action="store_true",
                help="Print PDF instead ASCII histogram [default: %default]")
        self.add_option("--bins", default=20, type="int",
                help="Number of bins in the histogram [default: %default]")
        self.add_option("--distmode", default="ss", choices=("ss", "ee"),
                help="Distance mode between paired reads, ss is outer distance, " \
                     "ee is inner distance [default: %default]")

    def set_sep(self, sep='\t', help="Separator in the tabfile", multiple=False):
        if multiple:
            help += ", multiple values allowed"
        self.add_option("--sep", default=sep,
                help="{0} [default: '%default']".format(help))

    def set_firstN(self, firstN=100000):
        self.add_option("--firstN", default=firstN, type="int",
                help="Use only the first N reads [default: %default]")

    def set_tag(self, tag=False, specify_tag=False):
        if not specify_tag:
            self.add_option("--tag", default=tag, action="store_true",
                    help="Add tag (/1, /2) to the read name")
        else:
            tag_choices = ["/1", "/2"]
            self.add_option("--tag", default=None, choices=tag_choices,
                    help="Specify tag to be added to read name")

    def set_phred(self, phred=None):
        phdchoices = ("33", "64")
        self.add_option("--phred", default=phred, choices=phdchoices,
                help="Phred score offset {0} [default: guess]".format(phdchoices))

    def set_size(self, size=0):
        self.add_option("--size", default=size, type="int",
                help="Insert mean size, stdev assumed to be 20% around mean")

    def set_trinity_opts(self, gg=False):
        self.set_home("trinity")
        self.set_cpus()
        self.set_params(prog="Trinity")
        topts = OptionGroup(self, "General Trinity options")
        self.add_option_group(topts)
        topts.add_option("--max_memory", default="128G", type="str",
                help="Jellyfish memory allocation [default: %default]")
        topts.add_option("--min_contig_length", default=90, type="int",
                help="Minimum assembled contig length to report" + \
                     " [default: %default]")
        topts.add_option("--bflyGCThreads", default=None, type="int",
                help="Threads for garbage collection [default: %default]")
        topts.add_option("--grid_conf_file", default="$TRINITY_HOME/htc_conf/JCVI_SGE.0611.conf", \
                type="str", help="Configuration file for supported compute farms" + \
                                 " [default: %default]")
        ggopts = OptionGroup(self, "Genome-guided Trinity options")
        self.add_option_group(ggopts)
        ggopts.add_option("--use_bam", default=None, type="str",
                     help="provide coord-sorted bam file as starting point" + \
                          " [default: %default]")
        ggopts.add_option("--max_intron", default=15000, type="int",
                     help="maximum allowed intron length [default: %default]")
        ggopts.add_option("--gg_cpu", default=None, type="int",
                     help="set number of threads for individual GG-Trinity" + \
                          " commands. if not defined, inherits from `--cpu`" + \
                          " [default: %default]")

    def set_pasa_opts(self, action="assemble"):
        self.set_home("pasa")
        if action == "assemble":
            self.set_home("tgi")
            self.add_option("--clean", default=False, action="store_true",
                    help="Clean transcripts using tgi seqclean [default: %default]")
            self.set_align(pctid=95, pctcov=90, intron=15000, bpsplice=3)
            self.add_option("--aligners", default="blat,gmap",
                    help="Specify splice aligners to use for mapping [default: %default]")
            self.add_option("--fl_accs", default=None, type="str",
                    help="File containing list of FL-cDNA accessions [default: %default]")
            self.set_cpus()
            self.add_option("--compreh", default=False, action="store_true",
                    help="Run comprehensive transcriptome assembly [default: %default]")
            self.set_align(compreh_pctid=95, compreh_pctcov=30)
            self.add_option("--prefix", default="compreh_init_build", type="str",
                    help="Prefix for compreh_trans output file names [default: %default]")
        elif action == "compare":
            self.add_option("--annots_gff3", default=None, type="str",
                    help="Reference annotation to load and compare against" + \
                    " [default: %default]")
            genetic_code = ["universal", "Euplotes", "Tetrahymena", "Candida", "Acetabularia"]
            self.add_option("--genetic_code", default="universal", choices=genetic_code,
                    help="Choose translation table [default: %default]")
            self.add_option("--pctovl", default=50, type="int",
                    help="Minimum pct overlap between gene and FL assembly " + \
                         "[default: %default]")
            self.add_option("--pct_coding", default=50, type="int",
                    help="Minimum pct of cDNA sequence to be protein coding " + \
                         "[default: %default]")
            self.add_option("--orf_size", default=0, type="int",
                    help="Minimum size of ORF encoded protein [default: %default]")
            self.add_option("--utr_exons", default=2, type="int",
                    help="Maximum number of UTR exons [default: %default]")
            self.add_option("--pctlen_FL", default=70, type="int",
                    help="Minimum protein length for comparisons involving " + \
                         "FL assemblies [default: %default]")
            self.add_option("--pctlen_nonFL", default=70, type="int",
                    help="Minimum protein length for comparisons involving " + \
                         "non-FL assemblies [default: %default]")
            self.add_option("--pctid_prot", default=70, type="int",
                    help="Minimum pctid allowed for protein pairwise comparison" + \
                         "[default: %default]")
            self.add_option("--pct_aln", default=70, type="int",
                    help="Minimum pct of shorter protein length aligning to " + \
                         "update protein or isoform [default: %default]")
            self.add_option("--pctovl_gene", default=80, type="int",
                    help="Minimum pct overlap among genome span of the ORF of " + \
                         "each overlapping gene to allow merging [default: %default]")
            self.add_option("--stompovl", default="", action="store_true",
                    help="Ignore alignment results, only consider genome span of ORF" + \
                         "[default: %default]")
            self.add_option("--trust_FL", default="", action="store_true",
                    help="Trust FL-status of cDNA [default: %default]")

    def set_annot_reformat_opts(self):
        self.add_option("--pad0", default=6, type="int",
                     help="Pad gene identifiers with 0 [default: %default]")
        self.add_option("--prefix", default="Medtr",
                     help="Genome prefix [default: %default]")
        self.add_option("--uc", default=False, action="store_true",
                     help="Toggle gene identifier upper case" \
                        + " [default: %default]")

    def set_home(self, prog, default=None):
        tag = "--{0}_home".format(prog)
        default = default or {"amos": "~/code/amos-code",
                   "trinity": "~/export/trinityrnaseq-2.0.6",
                   "cdhit": "~/export/cd-hit-v4.6.1-2012-08-27",
                   "maker": "~/export/maker",
                   "augustus": "~/export/maker/exe/augustus",
                   "pasa": "~/export/PASApipeline-2.0.2",
                   "gatk": "~/export",
                   "gmes": "~/export/gmes",
                   "gt": "~/export/genometools",
                   "sspace": "~/export/SSPACE-STANDARD-3.0_linux-x86_64",
                   "gapfiller": "~/export/GapFiller_v1-11_linux-x86_64",
                   "pbjelly": "~/export/PBSuite_15.2.20",
                   "picard": "~/export/picard-tools-1.138",
                   "khmer": "~/export/khmer",
                   "tassel": "/usr/local/projects/MTG4/packages/tassel",
                   "tgi": "~/export/seqclean-x86_64",
                   "eddyyeh": "/home/shared/scripts/eddyyeh",
                   "fiona": "~/export/fiona-0.2.0-Linux-x86_64",
                   "fermi": "~/export/fermi",
                   "lobstr": "/mnt/software/lobSTR",
                   "shapeit": "/mnt/software/shapeit",
                   "impute": "/mnt/software/impute",
                   "beagle": "java -jar /mnt/software/beagle.14Jan16.841.jar",
                   "minimac": "/mnt/software/Minimac3/bin",
                   }.get(prog, None)
        if default is None:  # Last attempt at guessing the path
            try:
                default = op.dirname(which(prog))
            except:
                default = None
        else:
            default = op.expanduser(default)
        help = "Home directory for {0} [default: %default]".format(prog.upper())
        self.add_option(tag, default=default, help=help)

    def set_aligner(self, aligner="bowtie"):
        valid_aligners = ("bowtie", "bwa")
        self.add_option("--aligner", default=aligner, choices=valid_aligners,
                     help="Use aligner [default: %default]")

    def set_verbose(self, help="Print detailed reports"):
        self.add_option("--verbose", default=False, action="store_true", help=help)


def ConfigSectionMap(Config, section):
    """
    Read a specific section from a ConfigParser() object and return
    a dict() of all key-value pairs in that section
    """
    cfg = {}
    options = Config.options(section)
    for option in options:
        try:
            cfg[option] = Config.get(section, option)
            if cfg[option] == -1:
                logging.debug("skip: {0}".format(option))
        except:
            logging.debug("exception on {0}!".format(option))
            cfg[option] = None
    return cfg


def get_abs_path(link_name):
    source = link_name
    if op.islink(source):
        source = os.readlink(source)
    else:
        source = op.basename(source)

    link_dir = op.dirname(link_name)
    source = op.normpath(op.join(link_dir, source))
    source = op.abspath(source)
    if source == link_name:
        return source
    else:
        return get_abs_path(source)


datadir = get_abs_path(op.join(op.dirname(__file__), '../utils/data'))
datafile = lambda x: op.join(datadir, x)


def splitall(path):
    allparts = []
    while True:
        path, p1 = op.split(path)
        if not p1:
            break
        allparts.append(p1)
    allparts = allparts[::-1]
    return allparts


def get_module_docstring(filepath):
    "Get module-level docstring of Python module at filepath, e.g. 'path/to/file.py'."
    co = compile(open(filepath).read(), filepath, 'exec')
    if co.co_consts and isinstance(co.co_consts[0], basestring):
        docstring = co.co_consts[0]
    else:
        docstring = None
    return docstring


def dmain(mainfile):
    cwd = op.dirname(mainfile)
    pyscripts = glob(op.join(cwd, "*.py"))
    actions = []
    for ps in sorted(pyscripts):
        action = op.basename(ps).replace(".py", "")
        if action[0] == "_":  # hidden namespace
            continue
        pd = get_module_docstring(ps)
        action_help = [x.rstrip(":.,\n") for x in pd.splitlines(True) \
                if len(x.strip()) > 10 and x[0] != '%'][0] \
                if pd else "no docstring found"
        actions.append((action, action_help))

    a = ActionDispatcher(actions)
    a.print_help()


def backup(filename):
    bakname = filename + ".bak"
    if op.exists(filename):
        logging.debug("Backup `{0}` to `{1}`".format(filename, bakname))
        sh("mv {0} {1}".format(filename, bakname))
    return bakname


def getusername():
    from getpass import getuser
    return getuser()


def getdomainname():
    from socket import getfqdn
    return ".".join(str(x) for x in getfqdn().split(".")[1:])


def sh(cmd, grid=False, infile=None, outfile=None, errfile=None,
        append=False, background=False, threaded=None, log=True,
        grid_opts=None, shell="/bin/bash"):
    """
    simple wrapper for system calls
    """
    if not cmd:
        return 1
    if grid:
        from jcvi.apps.grid import GridProcess
        pr = GridProcess(cmd, infile=infile, outfile=outfile, errfile=errfile,
                         threaded=threaded, grid_opts=grid_opts)
        pr.start()
        return pr.jobid
    else:
        if infile:
            cat = "cat"
            if infile.endswith(".gz"):
                cat = "zcat"
            cmd = "{0} {1} |".format(cat, infile) + cmd
        if outfile and outfile != "stdout":
            if outfile.endswith(".gz"):
                cmd += " | gzip"
            tag = ">"
            if append:
                tag = ">>"
            cmd += " {0}{1}".format(tag, outfile)
        if errfile:
            if errfile == outfile:
                errfile = "&1"
            cmd += " 2>{0}".format(errfile)
        if background:
            cmd += " &"

        if log:
            logging.debug(cmd)
        return call(cmd, shell=True, executable=shell)


def Popen(cmd, stdin=None, stdout=PIPE, debug=False, shell="/bin/bash"):
    """
    Capture the cmd stdout output to a file handle.
    """
    from subprocess import Popen as P
    if debug:
        logging.debug(cmd)
    # See: <https://blog.nelhage.com/2010/02/a-very-subtle-bug/>
    proc = P(cmd, bufsize=1, stdin=stdin, stdout=stdout, \
             shell=True, executable=shell)
    return proc


def popen(cmd, debug=True, shell="/bin/bash"):
    return Popen(cmd, debug=debug, shell=shell).stdout


def is_exe(fpath):
    return op.isfile(fpath) and os.access(fpath, os.X_OK)


def which(program):
    """
    Emulates the unix which command.

    >>> which("cat")
    "/bin/cat"
    >>> which("nosuchprogram")
    """
    fpath, fname = op.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = op.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


def glob(pathname, pattern=None):
    """
    Wraps around glob.glob(), but return a sorted list.
    """
    import glob as gl
    if pattern:
        pathname = op.join(pathname, pattern)
    return sorted(gl.glob(pathname))


def iglob(pathname, patterns):
    """
    Allow multiple file formats. This is also recursive. For example:

    >>> iglob("apps", "*.py,*.pyc")
    """
    matches = []
    patterns = patterns.split(",") if "," in patterns else listify(patterns)
    for root, dirnames, filenames in os.walk(pathname):
        matching = []
        for pattern in patterns:
            matching.extend(fnmatch.filter(filenames, pattern))
        for filename in matching:
            matches.append(op.join(root, filename))
    return sorted(matches)


def symlink(target, link_name):
    try:
        os.symlink(target, link_name)
    except OSError, e:
        if e.errno == errno.EEXIST:
            os.remove(link_name)
            os.symlink(target, link_name)


def mkdir(dirname, overwrite=False):
    """
    Wraps around os.mkdir(), but checks for existence first.
    """
    if op.isdir(dirname):
        if overwrite:
            shutil.rmtree(dirname)
            os.mkdir(dirname)
            logging.debug("Overwrite folder `{0}`.".format(dirname))
        else:
            return False  # Nothing is changed
    else:
        try:
            os.mkdir(dirname)
        except:
            os.makedirs(dirname)
        logging.debug("`{0}` not found. Creating new.".format(dirname))

    return True


def is_newer_file(a, b):
    """
    Check if the file a is newer than file b
    """
    if not (op.exists(a) and op.exists(b)):
        return False
    am = os.stat(a).st_mtime
    bm = os.stat(b).st_mtime
    return am > bm


def parse_multi_values(param):
    values = None
    if param:
        if op.isfile(param):
            values = list(set(x.strip() for x in open(param)))
        else:
            values = list(set(param.split(",")))
    return values


def listify(a):
    return a if (isinstance(a, list) or isinstance(a, tuple)) else [a]


def last_updated(a):
    """
    Check the time since file was last updated.
    """
    return time.time() - op.getmtime(a)


def need_update(a, b):
    """
    Check if file a is newer than file b and decide whether or not to update
    file b. Can generalize to two lists.
    """
    a = listify(a)
    b = listify(b)

    return any((not op.exists(x)) for x in b) or \
           all((os.stat(x).st_size == 0 for x in b)) or \
           any(is_newer_file(x, y) for x in a for y in b)


def get_today():
    """
    Returns the date in 2010-07-14 format
    """
    from datetime import date
    return str(date.today())


def ls_ftp(dir):
    from urlparse import urlparse
    from ftplib import FTP, error_perm
    o = urlparse(dir)

    ftp = FTP(o.netloc)
    ftp.login()
    ftp.cwd(o.path)

    files = []
    try:
        files = ftp.nlst()
    except error_perm, resp:
        if str(resp) == "550 No files found":
            print "no files in this directory"
        else:
            raise
    return files


def download(url, filename=None, debug=True, cookies=None):
    from urlparse import urlsplit
    from subprocess import CalledProcessError
    from jcvi.formats.base import FileShredder

    scheme, netloc, path, query, fragment = urlsplit(url)
    filename = filename or op.basename(path)
    filename = filename.strip()

    if not filename:
        filename = "index.html"

    if op.exists(filename):
        if debug:
            msg = "File `{0}` exists. Download skipped.".format(filename)
            logging.error(msg)
    else:
        from jcvi.utils.ez_setup import get_best_downloader

        downloader = get_best_downloader()
        try:
            downloader(url, filename, cookies=cookies)
        except (CalledProcessError, KeyboardInterrupt) as e:
            print >> sys.stderr, e
            FileShredder([filename])

    return filename


def getfilesize(filename, ratio=None):
    rawsize = op.getsize(filename)
    if not filename.endswith(".gz"):
        return rawsize

    import struct

    fo = open(filename, 'rb')
    fo.seek(-4, 2)
    r = fo.read()
    fo.close()
    size = struct.unpack('<I', r)[0]
    # This is only ISIZE, which is the UNCOMPRESSED modulo 2 ** 32
    if ratio is None:
        return size

    # Heuristic
    heuristicsize = rawsize / ratio
    while size < heuristicsize:
        size += 2 ** 32
    if size > 2 ** 32:
        logging.warn(\
            "Gzip file estimated uncompressed size: {0}.".format(size))

    return size


def debug():
    """
    Turn on the debugging
    """
    format = "%(asctime)s [%(module)s]"
    format += " %(message)s"
    logging.basicConfig(level=logging.DEBUG,
            format=format,
            datefmt="%H:%M:%S")

debug()


"""
From jcvi.graphics.base
"""

import os.path as op

from functools import partial

import numpy as np
import matplotlib as mpl
mpl.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from matplotlib import cm, rc, rcParams
from matplotlib.patches import Rectangle, Polygon, CirclePolygon, PathPatch, \
            FancyArrow, FancyArrowPatch
from matplotlib.path import Path


class ImageOptions (object):

    def __init__(self, opts):
        self.w, self.h = [int(x) for x in opts.figsize.split('x')]
        self.dpi = opts.dpi
        self.format = opts.format
        self.cmap = cm.get_cmap(opts.cmap)
        self.opts = opts

    def __str__(self):
        return "({0}px x {1}px)".format(self.dpi * self.w, self.dpi * self.h)


class TextHandler (object):

    def __init__(self, fig):
        self.heights = []
        try:
            self.build_height_array(fig)
        except ValueError:
            logging.debug("Failed to init heights. Variable label sizes skipped.")

    @classmethod
    def get_text_width_height(cls, fig, txt="chr01", size=12, usetex=True):
        tp = mpl.textpath.TextPath((0,0), txt, size=size, usetex=usetex)
        bb = tp.get_extents()
        xmin, ymin = fig.transFigure.inverted().transform((bb.xmin, bb.ymin))
        xmax, ymax = fig.transFigure.inverted().transform((bb.xmax, bb.ymax))
        return xmax - xmin, ymax - ymin

    def build_height_array(self, fig, start=1, stop=36):
        for i in xrange(start, stop + 1):
            w, h = TextHandler.get_text_width_height(fig, size=i)
            self.heights.append((h, i))

    def select_fontsize(self, height, minsize=1, maxsize=12):
        if not self.heights:
            return maxsize if height > .01 else minsize

        from bisect import bisect_left

        i = bisect_left(self.heights, (height,))
        size = self.heights[i - 1][1] if i else minsize
        size = min(size, maxsize)
        return size


CHARS = {
    '&':  r'\&',
    '%':  r'\%',
    '$':  r'\$',
    '#':  r'\#',
    '_':  r'\_',
    '{':  r'\{',
    '}':  r'\}',
}


def latex(s):
    return "".join([CHARS.get(char, char) for char in s])


def shorten(s, maxchar=20):
    if len(s) <= maxchar:
        return s
    pad = (maxchar - 3) / 2
    return s[:pad] + "..." + s[-pad:]


def normalize_axes(axes):
    axes = listify(axes)
    for ax in axes:
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_axis_off()


def panel_labels(ax, labels, size=16):
    for xx, yy, panel_label in labels:
        panel_label = r"$\textbf{{{0}}}$".format(panel_label)
        ax.text(xx, yy, panel_label, size=size,
                        ha="center", va="center")


def savefig(figname, dpi=150, iopts=None, cleanup=True):
    try:
        format = figname.rsplit(".", 1)[-1].lower()
    except:
        format = "pdf"
    try:
        plt.savefig(figname, dpi=dpi, format=format)
    except Exception as e:
        message = "savefig failed. Reset usetex to False."
        message += "\n{0}".format(str(e))
        logging.error(message)
        rc('text', **{'usetex': False})
        plt.savefig(figname, dpi=dpi)

    msg = "Figure saved to `{0}`".format(figname)
    if iopts:
        msg += " {0}".format(iopts)
    logging.debug(msg)

    if cleanup:
        plt.rcdefaults()


# human readable size (Kb, Mb, Gb)
def human_readable(x, pos, base=False):
    x = str(int(x))
    if x.endswith("000000000"):
        x = x[:-9] + "G"
    elif x.endswith("000000"):
        x = x[:-6] + "M"
    elif x.endswith("000"):
        x = x[:-3] + "K"
    if base and x[-1] in "MK":
        x += "b"
    return x


human_readable_base = partial(human_readable, base=True)
human_formatter = ticker.FuncFormatter(human_readable)
human_base_formatter = ticker.FuncFormatter(human_readable_base)
mb_formatter = ticker.FuncFormatter(lambda x, pos: "{0}M".format(int(x / 1000000)))
mb_float_formatter = ticker.FuncFormatter(lambda x, pos: "{0:.1f}M".format(x / 1000000.))
kb_formatter = ticker.FuncFormatter(lambda x, pos: "{0}K".format(int(x / 1000)))


def set_human_axis(ax, formatter=human_formatter):
    ax.xaxis.set_major_formatter(formatter)
    ax.yaxis.set_major_formatter(formatter)


set_human_base_axis = partial(set_human_axis, formatter=human_base_formatter)

available_fonts = [op.basename(x) for x in glob(datadir + "/*.ttf")]


def fontprop(ax, name, size=12):

    assert name in available_fonts, "Font must be one of {0}.".\
            format(available_fonts)

    import matplotlib.font_manager as fm

    fname = op.join(datadir, name)
    prop = fm.FontProperties(fname=fname, size=size)

    logging.debug("Set font to `{0}` (`{1}`).".format(name, prop.get_file()))
    for text in ax.texts:
        text.set_fontproperties(prop)

    return prop


def markup(s):
    import re
    s = latex(s)
    s = re.sub("\*(.*)\*", r"\\textit{\1}", s)
    return s


def append_percentage(s):
    # The percent symbol needs escaping in latex
    if rcParams['text.usetex'] is True:
        return s + r'$\%$'
    else:
        return s + '%'


def setup_theme(context='notebook', style="darkgrid", palette='deep', font='Helvetica'):
    try:
        import seaborn as sns
        extra_rc = {"lines.linewidth": 1,
                    "lines.markeredgewidth": 1,
                    "patch.edgecolor": 'k',
                    }
        sns.set(context=context, style=style, palette=palette, rc=extra_rc)
    except (ImportError, SyntaxError):
        pass

    rc('text', usetex=True)

    if font == "Helvetica":
        rc('font', **{'family': 'sans-serif', 'sans-serif': ['Helvetica']})
    elif font == "Palatino":
        rc('font', **{'family':'serif','serif': ['Palatino']})
    elif font == "Schoolbook":
        rc('font', **{'family':'serif','serif': ['Century Schoolbook L']})


setup_theme()


def print_colors(palette, outfile="Palette.png"):
    """
    print color palette (a tuple) to a PNG file for quick check
    """
    fig = plt.figure()
    ax = fig.add_subplot(111)

    xmax = 20 * (len(palette) + 1)
    x1s = np.arange(0, xmax, 20)
    xintervals = [10] * len(palette)
    xx = zip(x1s, xintervals)
    ax.broken_barh(xx, (5, 10), facecolors=palette)

    ax.set_ylim(0, 20)
    ax.set_xlim(0, xmax)
    ax.set_axis_off()

    savefig(outfile)


def discrete_rainbow(N=7, cmap=cm.Set1, usepreset=True, shuffle=False, \
                     plot=False):
    """
    Return a discrete colormap and the set of colors.

    modified from
    <http://www.scipy.org/Cookbook/Matplotlib/ColormapTransformations>

    cmap: colormap instance, eg. cm.jet.
    N: Number of colors.

    Example
    >>> x = resize(arange(100), (5,100))
    >>> djet = cmap_discretize(cm.jet, 5)
    >>> imshow(x, cmap=djet)

    See available matplotlib colormaps at:
    <http://dept.astro.lsa.umich.edu/~msshin/science/code/matplotlib_cm/>

    If N>20 the sampled colors might not be very distinctive.
    If you want to error and try anyway, set usepreset=False
    """
    import random
    from scipy import interpolate

    if usepreset:
        if 0 < N <= 5:
            cmap = cm.gist_rainbow
        elif N <= 20:
            cmap = cm.Set1
        else:
            sys.exit(discrete_rainbow.__doc__)

    cdict = cmap._segmentdata.copy()
    # N colors
    colors_i = np.linspace(0,1.,N)
    # N+1 indices
    indices = np.linspace(0,1.,N+1)
    rgbs = []
    for key in ('red','green','blue'):
       # Find the N colors
       D = np.array(cdict[key])
       I = interpolate.interp1d(D[:,0], D[:,1])
       colors = I(colors_i)
       rgbs.append(colors)
       # Place these colors at the correct indices.
       A = np.zeros((N+1,3), float)
       A[:,0] = indices
       A[1:,1] = colors
       A[:-1,2] = colors
       # Create a tuple for the dictionary.
       L = []
       for l in A:
           L.append(tuple(l))
       cdict[key] = tuple(L)

    palette = zip(*rgbs)

    if shuffle:
        random.shuffle(palette)

    if plot:
        print_colors(palette)

    # Return (colormap object, RGB tuples)
    return mpl.colors.LinearSegmentedColormap('colormap',cdict,1024), palette


def get_intensity(octal):
    from math import sqrt

    r, g, b = octal[1:3], octal[3:5], octal[5:]
    r, g, b = int(r, 16), int(g, 16), int(b, 16)
    intensity = sqrt((r * r + g * g + b * b) / 3)
    return intensity


def adjust_spines(ax, spines):
    # Modified from <http://matplotlib.org/examples/pylab_examples/spine_placement_demo.html>
    for loc, spine in ax.spines.items():
        if loc in spines:
            pass
            #spine.set_position(('outward', 10)) # outward by 10 points
            #spine.set_smart_bounds(True)
        else:
            spine.set_color('none') # don't draw spine

    if 'left' in spines:
        ax.yaxis.set_ticks_position('left')
    else:
        ax.yaxis.set_ticks_position('right')

    if 'bottom' in spines:
        ax.xaxis.set_ticks_position('bottom')
    else:
        ax.xaxis.set_ticks_position('top')


def set_ticklabels_helvetica(ax, xcast=int, ycast=int):
    xticklabels = [xcast(x) for x in ax.get_xticks()]
    yticklabels = [ycast(x) for x in ax.get_yticks()]
    ax.set_xticklabels(xticklabels, family='Helvetica')
    ax.set_yticklabels(yticklabels, family='Helvetica')


def draw_cmap(ax, cmap_text, vmin, vmax, cmap=None, reverse=False):
    # Draw a horizontal colormap at bottom-right corder of the canvas
    Y = np.outer(np.ones(10), np.arange(0, 1, 0.01))
    if reverse:
        Y = Y[::-1]
    xmin, xmax = .6, .9
    ymin, ymax = .02, .04
    ax.imshow(Y, extent=(xmin, xmax, ymin, ymax), cmap=cmap)
    ax.text(xmin - .01, (ymin + ymax) * .5, markup(cmap_text),
            ha="right", va="center", size=10)
    vmiddle = (vmin + vmax) * .5
    xmiddle = (xmin + xmax) * .5
    for x, v in zip((xmin, xmiddle, xmax), (vmin, vmiddle, vmax)):
        ax.text(x, ymin - .005, "%.1f" % v, ha="center", va="top", size=10)


def write_messages(ax, messages):
    """
    Write text on canvas, usually on the top right corner.
    """
    tc = "gray"
    axt = ax.transAxes
    yy = .95
    for msg in messages:
        ax.text(.95, yy, msg, color=tc, transform=axt, ha="right")
        yy -= .05


def quickplot_ax(ax, data, xmin, xmax, xlabel, title=None, ylabel="Counts",
                 counts=True, percentage=True, highlight=None):
    '''
    TODO: redundant with quickplot(), need to be refactored.
    '''
    if percentage:
        total_length = sum(data.values())
        data = dict((k, v * 100. / total_length) for (k, v) in data.items())

    left, height = zip(*sorted(data.items()))
    pad = max(height) * .01
    c1, c2 = "darkslategray", "tomato"
    if counts:
        for l, h in zip(left, height):
            if xmax and l > xmax:
                break
            tag = str(int(h))
            rotation = 90
            if percentage:
                tag = append_percentage(tag)
                rotation = 0
            color = c1
            if highlight is not None and l == highlight:
                color = c2
            ax.text(l, h + pad, tag, color=color, size=8,
                     ha="center", va="bottom", rotation=rotation)
    if xmax is None:
        xmax = max(left)

    ax.bar(left, height, align="center", fc=c1)
    if highlight:
        ax.bar([highlight], [data[highlight]], align="center", ec=c2, fc=c2)

    ax.set_xlabel(markup(xlabel))
    if ylabel:
        ax.set_ylabel(markup(ylabel))
    if title:
        ax.set_title(markup(title))
    ax.set_xlim((xmin - .5, xmax + .5))
    if percentage:
        ax.set_ylim(0, 100)


def quickplot(data, xmin, xmax, xlabel, title, ylabel="Counts",
              figname="plot.pdf", counts=True, print_stats=True):
    """
    Simple plotting function - given a dictionary of data, produce a bar plot
    with the counts shown on the plot.
    """
    plt.figure(1, (6, 6))
    left, height = zip(*sorted(data.items()))
    pad = max(height) * .01
    if counts:
        for l, h in zip(left, height):
            if xmax and l > xmax:
                break
            plt.text(l, h + pad, str(h), color="darkslategray", size=8,
                     ha="center", va="bottom", rotation=90)
    if xmax is None:
        xmax = max(left)

    plt.bar(left, height, align="center")
    plt.xlabel(markup(xlabel))
    plt.ylabel(markup(ylabel))
    plt.title(markup(title))
    plt.xlim((xmin - .5, xmax + .5))

    # Basic statistics
    messages = []
    counts_over_xmax = sum([v for k, v in data.items() if k > xmax])
    if counts_over_xmax:
        messages += ["Counts over xmax({0}): {1}".format(xmax, counts_over_xmax)]
    kk = []
    for k, v in data.items():
        kk += [k] * v
    messages += ["Total: {0}".format(np.sum(height))]
    messages += ["Maximum: {0}".format(np.max(kk))]
    messages += ["Minimum: {0}".format(np.min(kk))]
    messages += ["Average: {0:.2f}".format(np.mean(kk))]
    messages += ["Median: {0}".format(np.median(kk))]
    ax = plt.gca()
    if print_stats:
        write_messages(ax, messages)

    set_human_axis(ax)
    set_ticklabels_helvetica(ax)
    savefig(figname)
