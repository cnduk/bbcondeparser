#!/usr/bin/env python
from setuptools import setup, find_packages

VERSION = '0.0.2'

setup(
    name='bbcondeparser',
    version=VERSION,
    author='Conde Nast Digital UK',
    author_email='condenet.technical@condenast.co.uk',
    description="parser for Conde Nast BBCode",
    packages=find_packages(),
    install_requires=['six'],
    tests_require=['mock'],
    url="https://github.com/cnduk/bbcondeparser",
    download_url="https://github.com/cnduk/bbcondeparser/tarball/v{}".format(VERSION),
    keywords=["bbcode"],
)