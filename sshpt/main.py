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
import fnmatch
import copy
import sys
import select
import getpass
if PY2:
    from ConfigParser import SafeConfigParser
else:
    from configparser import SafeConfigParser
import yaml
from argparse import ArgumentParser
import logging
logging.basicConfig(level=logging.INFO)

from . import version
from .sshpt import SSHPowerTool
from .SSHQueue import stopSSHQueue
from .OutputThread import stopOutputThread

from .Generic import Password

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
    parser.add_argument('hosts')
    parser.add_argument("-u", "--username", dest="username", default='root', metavar="<username>",
        help="The username to be used when connecting.  Defaults to the currently logged-in user.")
    parser.add_argument("-p", "--password", dest="password", default=None, metavar="<password>",
        help="The password to be used when connecting (not recommended--use an authfile unless the username and password are transient).")
    parser.add_argument("--use-password", action='store_true',
        help="Use passowrd input")
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

    options.sudo = 'root' if options.sudo is None else options.sudo

    # Get the username and password to use when checking hosts
    if options.username is None:
        options.username = input('Username: ')

    if options.keyfile and options.keypass is None:
        options.keypass = Password(getpass.getpass('Passphrase: '))
    
    if options.password:
        options.password = Password(options.password)
    elif options.use_password:
        options.password = Password(getpass.getpass('Password: '))
        if options.password == '':
            print ('\nPlease type the password')
            raise Exception('Please type the password')
    else:
        options.password = ""

    if options.hosts:
        hosts_str = copy.deepcopy(options.hosts)
        options.hosts = []
        for host in hosts_str.split(","):
            options.hosts.append(
                {'host': host, 'port': options.port, 'username': options.username, 'password': options.password, 'keyfile': options.keyfile, 'keypass':options.keypass}
            )
    if options.server_file:
        with open(options.server_file, 'r') as f:
            servers_from_yml = yaml.load(f.read())
            hosts = []
            for alias in servers_from_yml:
                for host in options.hosts:
                    host = copy.deepcopy(host)
                    search = host['host']
                    if fnmatch.fnmatch(alias, search):
                        if 'password' in servers_from_yml[alias]:
                            servers_from_yml[alias]['password'] = Password(servers_from_yml[alias]['password'])
                        host.update(servers_from_yml[alias])
                        hosts.append(host)
            options.hosts = hosts
    if options.outfile is None and options.verbose is False:
        print("Error: You have not specified any mechanism to output results.")
        print("Please don't use quite mode (-q) without an output file (-o <file>).")
        raise Exception
    return options


def main():
    """Main program function:  Grabs command-line arguments, starts up threads, and runs the program.
    """
    # Grab command line arguments and the command to run (if any)
    options = create_argument()
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
