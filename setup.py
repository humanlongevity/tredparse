#!/usr/bin/env python

from setuptools import Extension, setup
from setup_helper import SetupHelper


name = "tredparse"
classifiers = [
    'Development Status :: 4 - Beta',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: BSD License',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2',
    'Topic :: Scientific/Engineering :: Bio-Informatics',
]
with open('requirements.txt') as f:
    required = f.read().splitlines()

# Use the helper
h = SetupHelper(initfile="tredparse/__init__.py", readmefile="README.md")
h.check_version(name, majorv=2, minorv=7)

libssw_ext = {"sources": ["src/ssw.c"], "include_dirs": ["src"]}

setup(
      name=name,
      version=h.version,
      author=h.author,
      author_email=h.email,
      license=h.license,
      long_description=h.long_description,
      packages=[name, "ssw"],
      package_dir={'ssw': 'src', 'tredparse': 'tredparse'},
      include_package_data=True,
      package_data={name: ["data/*.*"]},
      ext_modules=[Extension("libssw", **libssw_ext)],
      py_modules=["ssw.__init__", "ssw.ssw_wrap"],
      scripts=["tred.py", "tredreport.py", "tredplot.py"],
      classifiers=classifiers,
      zip_safe=False,
      url='https://github.com/tanghaibao/tredparse',
      description='Short Tandem Repeat (STR) genotyper',
      install_requires=required + ['pysam']
)
