HLI Short Tandem Repeat (STR) caller
====================================
[![Travis-CI](https://travis-ci.org/tanghaibao/tredparse.svg?branch=master)](https://travis-ci.org/tanghaibao/tredparse)

|||
|---|---|
| Author | Haibao Tang ([tanghaibao](http://github.com/tanghaibao)) |
|| Smriti Ramakrishnan ([smr18](http://github.com/smr18)) |
| Email | <htang@humanlongevity.com> |
| License | [BSD](http://creativecommons.org/licenses/BSD/) |


Description
-----------
Process a list of TRED (trinucleotide repeats disease) loci, and infer
the most likely genotype.


Installation
------------
-   Make sure your Python version &gt;= 2.7 (tested in ubuntu):
    ```
    virtualenv ~/t
    source ~/t/bin/activate
    pip install .
    ```

-   Test the installation by running against BAM file, or a list of BAM
    files:
    ```
    tred.py tests/sample.csv
    ```


Example
-------
Run `tred.py` on sample CSV file and generate TSV file with the
genotype:
```
tred.py nucleus-20160321.csv --workdir work
```

Highlight the potential risk individuals:
```
tredreport.py work/*.vcf.gz --tsv nucleus-20160321-TREDs.tsv
```

Several risk individuals show up in results:
```
SCA17 disease_cutoff=41 patients=2
           SampleKey  SCA17.1  SCA17.2  SCA17.PP
    290983_169083774       41       41         1
    291038_176635163       41       41         1
```

A `.report` file will also be generated that contains a summary of
number of people affected by over-expanded TREDs.
