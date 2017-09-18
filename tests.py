#!/usr/bin/env python
# -*- coding: UTF-8 -*-


import pytest


def test_tred():
    """ Run tred.py on sample CSV file and generate TSV file with the genotype
    """
    from tredparse.tred import main
    main(["tests/samples.csv", "--workdir", "work"])


def test_tredreport():
    """ Highlight the potential risk individuals
    """
    from tredparse.tredreport import main
    main(["work/t001.json", "work/t002.json", "--tsv", "work.tsv"])


@pytest.mark.skip(reason="Requires latex")
def test_tredplot():
    """ Plot the likelihood surface based on the model
    """
    from tredparse.tredplot import likelihood
    likelihood(["work/t001.json", "--tred", "HD"])
