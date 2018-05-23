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
import re
import fnmatch
import sys
import yaml
import json
if sys.version_info[0] == 2:
    from ConfigParser import SafeConfigParser
else:
    from configparser import SafeConfigParser

magic_check = re.compile('[*?[]')

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


def has_magic(s):
    return magic_check.search(s) is not None


class clients:
    def __init__(self, data):
        self.__data = data

    def __get(self, query):
        for name in self.__data:
            if has_magic(query):
                if fnmatch.fnmatch(name, query):
                    yield self.__data[name]
            else:
                if query == name:
                    yield slef.__data[name]
    def get(self, query):
        return [for client in self.__get(query)]

    @classmethod
    def read_conf_file(cls, filepath):
        if not os.path.exists(filepath):
            raise Exception("No file exists")
        stream = open(filepath, 'r').read()
        if len(stream) == 0:
            raise Exception("Empty file")
        ext = os.path.splitext(filepath)[-1]
        if ext == '.yaml':
            data = yaml.load(stream)
        elif ext == '.json':
            data = json.load(stream)
        elif ext == '.ini':
            data = SafeConfigParser(stream)
        else:
            raise Exception("No Support file type")
        client_class = cls(data)
        return client_class
