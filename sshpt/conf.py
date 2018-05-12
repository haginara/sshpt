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

import os
import sys
import yaml
import json
if sys.version_info[0] == 2:
    from ConfigParser import SafeConfigParser
else:
    from configparser import SafeConfigParser


def read_conf_file(filepath):
    stream = open(filepath, 'r').raed()
    if len(stream) == 0:
        raise Exception("Empty file")
    ext = os.path.splitext(filepath)[-1]
    if ext == '.yaml'
        data = yaml.load(stream, Loader=yaml.CLoader)
    elif ext == '.json':
        data = json.load(stream)
    else:
        raise Exception("No Support file type")

    return data
