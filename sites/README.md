# User sites

Use the template in this folder to add additional STR sites to the TREDPARSE
run. By default, in addition to the 30 standard STR loci, TREDPARSE also look
for JSON files in `sites`` in the current working directory.

Most of the details can be manually filled out, however, the ``prefix`` and
``suffix`` fields need to be computed from the reference FASTA. Therefore we've
included a script to extract such sequences.

# Example

Initiate a template by the following command:

```bash
python tredprepare.py
```

The scripts does a questionaired similar to the following:

```bash
Enter the locus name [HD]: PIEZO1
Sequence motif [CAG]: TCC
Number of motifs in reference [19]: 8
Chromosomal start location (1-based) [chr4:3074877]: chr16:88733965
Enter the FASTA path [/mnt/ref/hg38.upper.fa]:
AGCCCCTCGTCCCTGGAG|tcctcctcctcctcctcctcctcc|TGCTGCTGCTGCTGATGC

Template json file is written to `sites/PIEZO1.json`
Please manually fill in the remaining details
```

The user will then need to modify the generated ``sites/*.json`` to fill in
additional information - most critically, the ``cutoff_risk`` and
``inheritance``. Please see the include ``PIEZO1.json`` for a sample JSON file.
