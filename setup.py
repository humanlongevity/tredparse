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


def import_init(filename="__init__.py"):
    """ Get various info from the package without importing them
    """
    import ast

    with open(filename) as init_file:
        module = ast.parse(init_file.read())

    itr = lambda x: (ast.literal_eval(node.value) for node in ast.walk(module) \
        if isinstance(node, ast.Assign) and node.targets[0].id == x)

    try:
        return next(itr("__author__")), \
               next(itr("__email__")), \
               next(itr("__license__")), \
               next(itr("__version__"))
    except StopIteration:
        raise ValueError("One of author, email, license, or version"
                    " cannot be found in {}".format(filename))


libssw_ext = {"sources": ["src/ssw.c"], "include_dirs": ["src"]}
author, email, license, version = import_init(filename="tredparse/__init__.py")

setup(
      name=name,
      version=version,
      author=author[0],
      author_email=email,
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
      long_description=open("README.md").read(),
      install_requires=['cython', 'pandas', 'pysam']
)
