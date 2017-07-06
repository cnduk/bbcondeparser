#!/usr/bin/env python
import os
from setuptools import setup, find_packages

from bbcondeparser import __version__

readme_fname = os.path.join(os.path.dirname(__file__), 'README.rst')
with open(readme_fname, 'rb') as fandle:
    long_desc = fandle.read().decode('utf-8')

setup(
    name='bbcondeparser',
    version=__version__,
    author='Conde Nast Digital UK',
    author_email='condenet.technical@condenast.co.uk',
    description="parser for Conde Nast BBCode",
    long_description=long_desc,
    packages=find_packages(),
    install_requires=[],
    tests_require=['mock'],
    url="https://github.com/cnduk/bbcondeparser",
    download_url="https://github.com/cnduk/bbcondeparser/tarball/v{}".format(__version__),
    keywords=["bbcode"],
    license='MIT',
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Text Processing :: Markup",
    ],
)