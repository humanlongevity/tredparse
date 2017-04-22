#!/bin/bash

export PYTHONPATH=$PYTHONPATH:~/code
python -m jcvi.projects.str mini s3://hli-processed/processed/179258/isis_alignment_and_variant_calling/176449128/Data/Intensities/BaseCalls/Alignment/176449128_S1.bam t001_HD.bam
python -m jcvi.projects.str mini s3://hli-processed/processed/147857/isis_alignment_and_variant_calling/187499847/Data/Intensities/BaseCalls/Alignment/187499847_S1.bam t002_DM1.bam
python -m jcvi.projects.str mini s3://hli-processed/processed/330410/isaac_align/170500320_S1.bam t003_SCA17.bam
python -m jcvi.projects.str mini s3://hli-processed/processed/220033/isis_alignment_and_variant_calling/176444255/Data/Intensities/BaseCalls/Alignment/176444255_S1.bam t004_AR.bam
