#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import sys, os

version = '1.3.0'

setup(name = 'sshpt',
    license = 'GPLv3',
    version = version,
    description = 'SSH Power Tool - Run commands and copy files to multiple servers simultaneously WITHOUT requiring pre-shared authentication keys',
    scripts = ['sshpt.py'],
    py_modules = ['sshpt'],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: Unix",
        "Environment :: Console",
        "Programming Language :: Python :: 2.5",
        "Topic :: System :: Systems Administration",
    ], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='ssh administration parallel',
    author = 'Dan McDougall',
    author_email = 'YouKnowWho@YouKnowWhat.com',
    url = 'http://code.google.com/p/sshpt/',
    packages=find_packages(
        exclude=['ez_setup', 'examples', 'tests']
    ),
    install_requires=[
    "paramiko>=1.7.0",
    ],
)
