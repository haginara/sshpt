#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       Copyright 2011 Dan McDougall <YouKnowWho@YouKnowWhat.com>
#       Copyright 2015 Jonghak Choi <haginara@gmail.com>
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; Version 3 of the License
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, the license can be downloaded here:
#
#       http://www.gnu.org/licenses/gpl.html

from __future__ import absolute_import
from __future__ import print_function

import os
import sys
import fnmatch
import json
import yaml
try:
    from yaml import CLoader as YAMLoader
except ImportError:
    from yaml import Loader as YAMLoader
import select
import getpass
if sys.version_info[0] == 2:
    from ConfigParser import SafeConfigParser
else:
    from configparser import SafeConfigParser


from .conf import read_conf_file
from .conf import StdinAction
from .conf import split_type

import argparse
from argparse import ArgumentParser
import logging
logging.basicConfig(level=logging.INFO)

from . import version
from .sshpt import SSHPowerTool
from .sshpt import ServerConnection
from .SSHQueue import stopSSHQueue
from .OutputThread import stopOutputThread

from .Generic import Password
from .Generic import normalizeString

logger = logging.getLogger(__name__)


def _parse_hostfile(host):
    keys = ['host', 'username', 'password']
    values = host.split(":")
    hosts = dict(zip(keys, values))
    hosts['password'] = Password(hosts['password'])
    return hosts


def _normalize_hosts(hosts):
    if hosts is None:
        return []
    if isinstance(hosts, str):
        hosts = filter(lambda h: (not h.startswith("#") and h != ""), hosts.splitlines())
        hosts = [host.strip() for host in hosts]
    return [_parse_hostfile(host) if ':' in host else {'host': host} for host in hosts]


def option_parse(options):
    if options.outfile is None and options.verbose is False:
        print("Error: You have not specified any mechanism to output results.")
        print("Please don't use quite mode (-q) without an output file (-o <file>).")
        return 2
    return 0


class NamespaceOption(object):
    """
    host=host.get('host'),
    username=host.get('username', self.options.username),
    password=host.get('password', self.options.password).password,
    keyfile=self.options.keyfile, keypass=self.options.keypass,
    timeout=self.options.timeout,
    commands=self.options.commands,
    local_filepath=self.options.local_filepath, remote_filepath=self.options.remote_filepath,
    execute=self.options.execute, remove=self.options.remove, sudo=self.options.sudo, port=self.options.port)
    """
    def __str__(self):
        return "%s" % self.__dict__


class ArgParser(object):
    def __init__(self):
        usage = 'usage: sshpt [options] "[command1]" "[command2]" ...'
        parser = ArgumentParser()
        parser.add_argument('-v', '--version', action='version', version=version.__version__)
        parser.add_argument("-f", "--conf-file", dest="hostfile", default='servers.yaml', type=read_conf_file,
            help="Location of the file containing the host list.")
        parser.add_argument("-T", "--threads", dest="max_threads", type=int, default=10, metavar="<int>",
            help="Number of threads to spawn for simultaneous connection attempts [default: 10].")
        parser.add_argument("group",
            help="Group of servers that you want to command remotely")
        parser.add_argument("-q", "--quiet", action="store_false", dest="verbose", default=True,
            help="Don't print status messages to stdout (only print errors).")
        parser.add_argument("-V", "--verbose", action='store_true',
            help="Making output verbose")
        parser.add_argument("-o", "--outfile", dest="outfile", default=None, metavar="<file>",
            help="Location of the file where the results will be saved.")
        parser.add_argument("-of", "--output-format", dest="output_format", choices=['csv', 'json', 'yaml'], default="csv",
            help="Ouptut format")
        parser.add_argument('subcommand', help='Subcommand to run')
        args, others = parser.parse_known_args()
        if not hasattr(self, args.subcommand):
            print('Unrecognized command')
            parser.print_help()
            sys.exit(1)
        # use dispatch pattern to invoke method with same name
        subcommand_args = getattr(self, args.subcommand)(others)
        args.subcommand_args = subcommand_args
        self.options = args
        logger.debug("%s", self.options)

    def __getattr__(self, key):
        if key in self.__dict__:
            return getattr(self, key)
        if key in self.options.subcommand_args:
            return getattr(self.options.subcommand_args, key)
        return getattr(self.options, key)

    def scp(self, argument):
        parser = argparse.ArgumentParser(description='SCP')
        parser.add_argument("-c", "--copy-file", dest="local", default=None, metavar="<file>",
            help="Location of the file to copy to and optionally execute (-x) on hosts.")
        parser.add_argument("-d", "--dest", dest="remote", default="/tmp/", metavar="<path>",
            help="Path where the file should be copied on the remote host (default: /tmp/).")
        parser.add_argument("-x", "--execute", action="store_true", dest="execute", default=False,
            help="Execute the copied file (just like executing a given command).")
        parser.add_argument("-r", "--remove", action="store_true", dest="remove", default=False,
            help="Remove (clean up) the SFTP'd file after execution.")
        args = parser.parse_args(argument)
        return args

    def cmd(self, argument):
        parser = argparse.ArgumentParser(description='Command')
        parser.add_argument('commands', metavar='Commands', type=str, nargs='*', default=False,
            help='Commands')
        args = parser.parse_args(argument)
        return args

    def servers(self):
        servers = self.hostfile['servers']
        if self.group == '*':
            servers = [ServerConnection.from_dict(servers[server]) for server in servers]
        elif 'ip:' in self.group:
            _ip = self.group[3:]
            servers = [ServerConnection.from_dict(servers[server]) for server in servers if fnmatch.fnmatch(_ip, server['host'])]
        else:
            servers = [ServerConnection.from_dict(servers[server]) for server in servers if fnmatch.fnmatch(self.group, server)]

        for server in servers:
            server.subcommand = self.options.subcommand
            server.subcommand_args = self.options.subcommand_args
            yield server

def main():
    """Main program function:  Grabs command-line arguments, starts up threads, and runs the program.
    """
    # Grab command line arguments and the command to run (if any)
    # This wierd little sequence of loops allows us to hit control-C
    # in the middle of program execution and get immediate results
    try:
        args = ArgParser()
        sshpt = SSHPowerTool(args)
        output_queue = sshpt()
        # Just to be safe we wait for the OutputThread to finish before moving on
        output_queue.join()
    except KeyboardInterrupt:
        logger.error ('caught KeyboardInterrupt, exiting...')
        # Return code should be 1 if the user issues a SIGINT (control-C)
        # Clean up
    finally:
        stopSSHQueue()
        stopOutputThread()
        return 1
    return 0


if __name__ == '__main__':
    main()
