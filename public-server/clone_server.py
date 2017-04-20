#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
Selectively clone contents from the private STR server.
"""

import errno
import os
import os.path as op
import shutil
import sys


def read_contents(filename="git-ls.txt"):
    """ Find all file contents
    """
    filenames = [x.strip() for x in open(filename)]
    return [x for x in filenames]


def cp_with_mkdir(src, target):
    """ Copy file over, and automatically creating directories, like mkdir -p
    """
    src = op.abspath(src)
    if not op.exists(op.dirname(target)):
        try:
            os.makedirs(op.dirname(target))
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    if op.exists(target):
        print >> sys.stderr, "Skip {}".format(target)
        return

    # All good - proceed with copying
    if ".meteor" in target:
        print >> sys.stderr, "Copy {} => {}".format(src, target)
        shutil.copyfile(src, target)
    else:
        print >> sys.stderr, "Symlink {} => {}".format(src, target)
        os.symlink(src, target)


def main():
    for filename in read_contents():
        src = op.join("../server", filename)
        target = op.join(".", filename)
        cp_with_mkdir(src, target)


if __name__ == '__main__':
    main()
