#!
#
"""
Example .yaml
nn-host1:
    host: 10.0.10.2
    username: user
    password: user
    sudo: True

nn-host2:
    host: 10.0.10.101
    username: user
    password: user
    sudo: True
"""

import argparse
import os
import re
import fnmatch
import sys
import yaml
try:
    from yaml import CLoader as YAMLoader
except ImportError:
    from yaml import Loader as YAMLoader
import json
if sys.version_info[0] == 2:
    from ConfigParser import SafeConfigParser
else:
    from configparser import SafeConfigParser

magic_check = re.compile('[*?[]')


def has_magic(s):
    return magic_check.search(s) is not None


class StdinAction(argparse.Action):
    def __init__(self, option_strings, dest, const=None, default=None, required=False, help=None):
        super(StdinAction, self).__init__(option_strings=option_strings,
                                dest=dest,
                                nargs=0,
                                const=const,
                                default=default,
                                required=required,
                                help=help,)
        return
    def __call__(self, parser, namespace, values, option_string=None):
        # if stdin wasn't piped in, prompt the user for it now
        print("Enter list of hosts (one entry per line). ")
        print("Ctrl-D(or Ctrl-Z in Windows) to end input.")
        lines = [line.strip() for line in sys.stdin.readlines()]
        setattr(namespace, self.dest, lines)


def split_type(arg_str):
        return arg_str.split(",")


def read_conf_file(filepath):
    stream = open(filepath, 'r').read()
    if len(stream) == 0:
        raise Exception("Empty file")
    ext = os.path.splitext(filepath)[-1]
    if ext == '.yaml':
        data = yaml.load(stream, Loader=YAMLoader)
    elif ext == '.json':
        data = json.load(stream)
    else:
        data = [line.strip() for line in f.readlines()]
    return data
