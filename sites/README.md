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
