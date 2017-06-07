#!/usr/bin/env python
from setuptools import setup, find_packages

from bbcondeparser import __version__

setup(
    name='bbcondeparser',
    version=__version__,
    author='Conde Nast Digital UK',
    author_email='condenet.technical@condenast.co.uk',
    description="parser for Conde Nast BBCode",
    packages=find_packages(),
    install_requires=['six'],
    tests_require=['mock'],
    url="https://github.com/cnduk/bbcondeparser",
    download_url="https://github.com/cnduk/bbcondeparser/tarball/v{}".format(__version__),
    keywords=["bbcode"],
)