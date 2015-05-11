#!/usr/bin/env python
# -*- coding: utf-8 -*-

#from setuptools import setup, find_packages
from distutils.core import setup
from sshpt import sshpt
import sys, os

version = sshpt.__version__

setup(
    name = 'sshpt',
    license = sshpt.__license__,
    version = version,
    author = "{},{}".format(sshpt.__author__, sshpt.__second_author__),
    author_email = 'YouKnowWho@YouKnowWhat.com',
    url = 'http://code.google.com/p/sshpt/',
    description = 'SSH Power Tool - Run commands and copy files to multiple servers simultaneously WITHOUT requiring pre-shared authentication keys',
    long_description = open('README.txt').read(),
    scripts = ['sshpt/sshpt.py'],
    packages= ['sshpt', 'sshpt.test'],
    entry_points = {
        'console_scripts':
            ['sshpt=sshpt.sshpt:main']
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: Unix",
        "Environment :: Console",
        "Programming Language :: Python :: 2.5",
        "Topic :: System :: Systems Administration",
    ], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='ssh administration parallel',
    install_requires=[
        "paramiko>=1.15.0",
    ],
)
