# TREDPARSE: HLI Short Tandem Repeat (STR) caller

[![Travis-CI](https://travis-ci.org/tanghaibao/tredparse.svg?branch=master)](https://travis-ci.org/tanghaibao/tredparse)

| | |
|---|---|
| Author | Haibao Tang ([tanghaibao](http://github.com/tanghaibao)) |
| | Smriti Ramakrishnan ([smr18](http://github.com/smr18)) |
| Email | <htang@humanlongevity.com> |
| License | Restricted |

## Description

Process a list of TRED (trinucleotide repeats disease) loci, and infer
the most likely genotype.

## Installation

- Make sure your Python version &gt;= 2.7 (tested in ubuntu):

  ```bash
  virtualenv ~/t
  source ~/t/bin/activate
  pip install .
  ```
For accessing BAMs that are located on S3, please refer to
`Dockerfiles/tredparse.dockerfile` for installation of SAMTOOLS/pysam with S3
support.

## Example

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
[HD] - Huntington disease
rep=CAG inherit=AD cutoff=40 n=1 loc=chr4:3074877-3074933
SampleKey  Calls HD.FR                           HD.PR HD.RR  HD.PP
176449128  15/41  15|4  ...|1;21|1;24|2;29|1;34|1;41|1          1.0
```

A `.report.txt` file will also be generated that contains a summary of
number of people affected by over-expanded TREDs as well as population allele
frequency.

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
