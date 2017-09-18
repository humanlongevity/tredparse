#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
Copyright (c) 2015-2017 Human Longevity Inc.

Author: Haibao Tang <htang@humanlongevity.com>
License: Non-Commercial Use Only. For details, see `LICENSE` file

HLI TRED caller: parse the target regions from the input BAM file, extract full and partial
reads, build probabilistic model and calculate the most likely repeat sizes given the
data.
"""

import sys
from tredparse.tred import main


if __name__ == '__main__':
    main(sys.argv[1:])
