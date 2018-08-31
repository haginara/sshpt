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

from ._compat import PY2, PY3
from ._compat import input
import sys
import select
import getpass
if PY2:
    from ConfigParser import SafeConfigParser
else:
    from configparser import SafeConfigParser
from argparse import ArgumentParser
import logging
logging.basicConfig(level=logging.INFO)

from . import version
from .sshpt import SSHPowerTool
from .SSHQueue import stopSSHQueue
from .OutputThread import stopOutputThread

from .Generic import Password

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

def create_argument():
    """
        sshpt [host_gruop] [credential]
            host_group:
                [host_option] [host]
                host_options:
                    {{--hosts|-f|-S|-i|-j}}
                host:
                    {{host}}
            credential:
                [username] [secret]
                username:
                    {{username}}
                secret:
                    [password|keyfile(keepass)]
                    password:
                        -p
                    keyfile:
                        -k
                        -K

                {{-k|-K}} {{options}} {{Action:cmd|scp}}
            Action:
                cmd:
                    {{}}
                scp:
                    {{}}
    """
    usage = 'usage: sshpt [options] "[command1]" "[command2]" ...'
    parser = ArgumentParser(usage=usage)

    parser.add_argument('-v', '--version', action='version', version=version.__version__)

    host_group = parser.add_mutually_exclusive_group(required=True)
    host_group.add_argument("-H", "--hosts", dest='hosts', default=None,
        help='Specify a host list on the command line. ex)--hosts="host1,host2,host3"')
    host_group.add_argument('-S', "--server-file", dest='server_file',
        help='Server file ahs list of servers and information to connect to')
    parser.add_argument("-u", "--username", dest="username", default='root', metavar="<username>",
        help="The username to be used when connecting.  Defaults to the currently logged-in user.")
    parser.add_argument("-p", "--password", dest="password", default=None, metavar="<password>",
        help="The password to be used when connecting (not recommended--use an authfile unless the username and password are transient).")
    parser.add_argument("-k", "--key-file", dest="keyfile", default=None, metavar="<file>",
        help="Location of the private key file")
    parser.add_argument("-K", "--key-pass", dest="keypass", metavar="<password>", default=None,
        help="The password to be used when use the private key file).")

    parser.add_argument("-o", "--outfile", dest="outfile", default=None, metavar="<file>",
        help="Location of the file where the results will be saved.")
    parser.add_argument("-O", "--output-format", dest="output_format",
        choices=['csv', 'json'], default="csv",
        help="Ouptut format")

    parser.add_argument("-T", "--threads", dest="max_threads", type=int, default=10, metavar="<int>",
        help="Number of threads to spawn for simultaneous connection attempts [default: 10].")
    parser.add_argument("-q", "--quiet", action="store_false", dest="verbose", default=True,
        help="Don't print status messages to stdout (only print errors).")
    parser.add_argument("-P", "--port", dest="port", type=int, default=22, metavar="<port>",
        help="The port to be used when connecting.  Defaults to 22.")
    parser.add_argument("-t", "--timeout", dest="timeout", default=30, metavar="<seconds>",
        help="Timeout (in seconds) before giving up on an SSH connection (default: 30)")
   
    action_parsers = parser.add_subparsers(title='Available actions', dest='action')
    scp_parser = action_parsers.add_parser("scp")
    scp_parser.add_argument("-c", "--copy-file", required=True, dest="local_filepath", default=None, metavar="<file>",
        help="Location of the file to copy to and optionally execute (-x) on hosts.")
    scp_parser.add_argument("-d", "--dest", required=True, dest="remote_filepath", default="/tmp/", metavar="<path>",
        help="Path where the file should be copied on the remote host (default: /tmp/).")
    scp_parser.add_argument("-x", "--execute", action="store_true", dest="execute", default=False,
        help="Execute the copied file (just like executing a given command).")
    scp_parser.add_argument("-r", "--remove", action="store_true", dest="remove", default=False,
        help="Remove (clean up) the SFTP'd file after execution.")
    scp_parser.add_argument("-s", "--sudo", nargs="?", action="store", dest="sudo", default=False,
        help="Use sudo to execute the command (default: as root).")

    cmd_parser = action_parsers.add_parser("cmd")
    cmd_parser.add_argument("-s", "--sudo", nargs="?", action="store", dest="sudo", default=False,
        help="Use sudo to execute the command (default: as root).")
    cmd_parser.add_argument('commands', metavar='Commands', type=str, nargs='*', default=False,
        help='Commands')

    options, args = parser.parse_known_args()

    if options.hosts:
        options.hosts = options.hosts.split(":")
    elif options.server_file:
        ini_config = SafeConfigParser(allow_no_value=True)
        ini_config.read(options.ini_file[0])
        options.hosts = [server[1] for server in ini_config.items(options.ini_file[1])]
        if ini_config.has_section('Commands'):
            for command in ini_config.items("Commands"):
                if options.commands == command[0]:
                    options.commands = command[1]
                    break
    elif options.json:
        pass

    if options.authfile:
        credentials = open(options.authfile).readline()
        options.username, options.password = credentials.split(":")
        # Get rid of trailing newline
        options.password = Password(options.password.rstrip('\n'))
    options.sudo = 'root' if options.sudo is None else options.sudo

    # Get the username and password to use when checking hosts
    if options.username is None:
        options.username = input('Username: ')

    if options.keyfile and options.keypass is None:
        options.keypass = Password(getpass.getpass('Passphrase: '))
    elif options.password is None:
        options.password = Password(getpass.getpass('Password: '))
        if options.password == '':
            print ('\nPlease type the password')
            raise Exception('Please type the password')
    elif options.password:
        options.password = Password(options.password)

    options.hosts = _normalize_hosts(options.hosts)
    return options


def main():
    """Main program function:  Grabs command-line arguments, starts up threads, and runs the program.
    """
    # Grab command line arguments and the command to run (if any)
    options = create_argument()
    if 0 != option_parse(options):
        return 2
    sshpt = SSHPowerTool(options)
    # This wierd little sequence of loops allows us to hit control-C
    # in the middle of program execution and get immediate results
    try:
        output_queue = sshpt()
        # Just to be safe we wait for the OutputThread to finish before moving on
        output_queue.join()
    except KeyboardInterrupt:
        print ('caught KeyboardInterrupt, exiting...')
        # Return code should be 1 if the user issues a SIGINT (control-C)
        # Clean up
        stopSSHQueue()
        stopOutputThread()
        return 1
    return 0


if __name__ == '__main__':
    main()
