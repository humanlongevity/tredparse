#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
Copyright (c) 2015-2017 Human Longevity Inc.

Author: Haibao Tang <htang@humanlongevity.com>
License: Non-Commercial Use Only. For details, see `LICENSE` file

Report signficant calls - predisease and disease. When VCF or JSON files are
given, a new tsv file will be written - otherwise will summarize calls based on
the given tsv file.
"""

import sys
from tredparse.tredreport import main


if __name__ == '__main__':
    main(sys.argv[1:])
