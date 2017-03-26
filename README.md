# HLI Short Tandem Repeat (STR) caller

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

- Test the installation by running against BAM file, or a list of BAM
  files:

  ```bash
  tred.py tests/sample.csv
  ```

For accessing BAMs that are located on S3, please refer to
`Dockerfiles/tredparse.dockerfile` for installation of SAMTOOLS/pysam with S3
support.

## Example

Run `tred.py` on sample CSV file and generate TSV file with the
genotype:

```bash
tred.py nucleus-20160321.csv --workdir work
```

Highlight the potential risk individuals:

```bash
tredreport.py work/*.vcf.gz --tsv nucleus-20160321-TREDs.tsv
```

Several risk individuals show up in results:

```bash
SCA17 disease_cutoff=41 patients=2
           SampleKey  SCA17.1  SCA17.2  SCA17.PP
    290983_169083774       41       41         1
    291038_176635163       41       41         1
```

A `.report` file will also be generated that contains a summary of
number of people affected by over-expanded TREDs.

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
