#!/usr/bin/env python
# -*- coding: utf-8 -*-

#from distutils.core import setup
from setuptools import setup, find_packages
from sshpt import sshpt
import sys, os

version = sshpt.__version__

EXCLUDE_FROM_PACKAGES=[ 'test' ]
print  find_packages()

setup(
    name = 'sshpt',
    license = sshpt.__license__,
    version = version,
    author = "{},{}".format(sshpt.__author__, sshpt.__second_author__),
    author_email = 'YouKnowWho@YouKnowWhat.com',
    url = 'http://code.google.com/p/sshpt/',
    description = 'SSH Power Tool - Run commands and copy files to multiple servers simultaneously WITHOUT requiring pre-shared authentication keys',
    long_description = open('README.txt').read(),
    keywords='ssh administration parallel',
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: Unix",
        "Environment :: Console",
        "Programming Language :: Python :: 2.5",
        "Topic :: System :: Systems Administration",
    ], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    packages = find_packages(exclude=EXCLUDE_FROM_PACKAGES),
    #package_dir =  {'sshpt': 'sshpt'},
    #scripts = ['sshpt/sshpt.py'],
    entry_points = {
        'console_scripts': [
            'sshpt = sshpt:main',
        ],
    },
    install_requires=[
        "paramiko>=1.15.0",
    ],
)
