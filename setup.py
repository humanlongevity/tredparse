#!/usr/bin/env python

from setuptools import Extension, setup


name = "tredparse"
classifiers = [
    'Development Status :: 4 - Beta',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: BSD License',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2',
    'Topic :: Scientific/Engineering :: Bio-Informatics',
    ]

libssw_ext = {"sources": ["src/ssw.c"], "include_dirs": ["src"]}
exec(open(name + "/__init__.py").read())

setup(
      name=name,
      version=__version__,
      author=__author__[0],
      author_email=__email__,
      packages=[name, "ssw"],
      package_dir={'ssw': 'src', 'tredparse': 'tredparse'},
      include_package_data=True,
      package_data={name: ["data/*.*"]},
      ext_modules=[Extension("libssw", **libssw_ext)],
      py_modules=["ssw.__init__", "ssw.ssw_wrap"],
      scripts=["tred.py", "tredreport.py"],
      classifiers=classifiers,
      zip_safe=False,
      url='https://github.com/tanghaibao/tredparse',
      description='Short Tandem Repeat (STR) genotyper',
      long_description=open("README.md").read(),
      install_requires=['cython', 'pandas', 'pysam']
     )
