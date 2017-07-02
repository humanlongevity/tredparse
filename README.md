# TREDPARSE: HLI Short Tandem Repeat (STR) caller

[![Travis-CI](https://travis-ci.org/humanlongevity/tredparse.svg?branch=master)](https://travis-ci.org/humanlongevity/tredparse)

| | |
|---|---|
| Author | Haibao Tang ([tanghaibao](http://github.com/tanghaibao)) |
| | Smriti Ramakrishnan ([smr18](http://github.com/smr18)) |
| Email | <htang@humanlongevity.com> |
| License | See included LICENSE |

## Description

Process a list of TRED (trinucleotide repeats disease) loci, and infer
the most likely genotype.

## Installation

 Make sure your Python version &gt;= 2.7 (tested in ubuntu):

```bash
virtualenv ~/t
source ~/t/bin/activate
pip install .
```

For accessing BAMs that are located on S3, please refer to
`Dockerfiles/tredparse.dockerfile` for installation of SAMTOOLS/pysam with S3
support.

## Example

First specify the input bam paths and sample keys in a CSV file, like
`tests/samples.csv`. This file is comma separated:

```
#SampleKey,BAM,TRED
t001,tests/t001.bam,HD
t002,tests/t002.bam,DM1
```

If third column is omitted, then all 30 TREDs are scanned. For example:

```
#SampleKey,BAM
t001,tests/t001.bam
t002,tests/t002.bam
```

Please also note that the BAM path can start with `http://` or `s3://`, provided
that the corresponding BAM index can be found.

Run `tred.py` on sample CSV file and generate TSV file with the
genotype:

```bash
tred.py tests/samples.csv --workdir work
```

Highlight the potential risk individuals:

```bash
tredreport.py work/*.json --tsv work.tsv
```

The inferred "at-risk" individuals show up in results:

```bash
[DM1] - Myotonic dystrophy 1
rep=CAG inherit=AD cutoff=50 n=1 loc=chr19:45770205-45770264
SampleKey Calls DM1.FR                          DM1.PR     DM1.RR  DM1.PP
    t002  5/62   5|24  ...|1;39|1;40|1;42|1;43|1;46|2  49|3;50|8     1.0

[HD] - Huntington disease
rep=CAG inherit=AD cutoff=40 n=1 loc=chr4:3074877-3074933
SampleKey  Calls HD.FR                           HD.PR HD.RR  HD.PP
    t001  15/41  15|4  ...|1;21|1;24|2;29|1;34|1;41|1          1.0
```

One particular individual `t001` appears to have `15/41` call (one allele at `15` CAGs
and the other at `41` CAGs) at Huntington disease locus (HD). Since the risk cutoff
is `40`, we have inferred it to be at-risk.

A `.report.txt` file will also be generated that contains a summary of
number of people affected by over-expanded TREDs as well as population allele
frequency.

To better understand the uncertainties in the prediction, one call plot the
likelihood surface based on the model. Using the same example as above at the
Huntington disease case, we can run a command on the JSON output, with option
`--tred HD` to specify the locus.

```bash
tredplot.py likelihood2 work/t001.json --tred HD
```

This generates the following plot:

![](https://dl.dropboxusercontent.com/u/15937715/Data/TREDPARSE/likelihood2.png)

## Server demo

The server/client allows `tredparse` to be run as a service, also showing the
detailed debug information for the detailed computation.

![](https://dl.dropboxusercontent.com/u/15937715/Data/TREDPARSE/screencast.gif)

Install `meteor` if you don't have it yet.

```bash
curl https://install.meteor.com/ | sh
```

Then build the docker image to run the command, then run the server.

```bash
cd Dockerfiles
make build
cd ../server
meteor update
meteor npm install
meteor
```
