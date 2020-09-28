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

import sys
import select
import getpass
if sys.version_info[0] == 2:
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
    usage = 'usage: sshpt [options] "[command1]" "[command2]" ...'

    default_username=getpass.getuser()
    parser = ArgumentParser(usage=usage)

    parser.add_argument('-v', '--version', action='version', version=version.__version__)
    host_group = parser.add_mutually_exclusive_group(required=True)
    host_group.add_argument("-f", "--file", dest="hostfile", default=None, type=open,
        help="Location of the file containing the host list.")
    host_group.add_argument("-S", "--stdin", dest="stdin", default=False,
        action="store_true", help="Read hosts from standard input")
    host_group.add_argument("--hosts", dest='hosts', default=None,
        help='Specify a host list on the command line. ex)--hosts="host1:host2:host3"')
    host_group.add_argument("-i", "--ini-file", default=None, nargs=2,
        help="Configuration file with INI Format. ex)--ini-file path, server")
    host_group.add_argument("-j", "--json", default=None, nargs=2,
        help="Configuration file with JSON Format. ex)--json path, server")

    parser.add_argument("-k", "--key-file", dest="keyfile", default=None, metavar="<file>",
        help="Location of the private key file")
    parser.add_argument("-K", "--key-pass", dest="keypass", metavar="<password>", default=None,
        help="The password to be used when use the private key file).")
    parser.add_argument("-o", "--outfile", dest="outfile", default=None, metavar="<file>",
        help="Location of the file where the results will be saved.")
    parser.add_argument("-a", "--authfile", dest="authfile", default=None, metavar="<file>",
        help='Location of the file containing the credentials to be used for connections (format is "username:password").')
    parser.add_argument("-T", "--threads", dest="max_threads", type=int, default=10, metavar="<int>",
        help="Number of threads to spawn for simultaneous connection attempts [default: 10].")
    parser.add_argument("-P", "--port", dest="port", type=int, default=22, metavar="<port>",
        help="The port to be used when connecting.  Defaults to 22.")
    parser.add_argument("-u", "--username", dest="username", default=default_username, metavar="<username>",
        help="The username to be used when connecting.  Defaults to the currently logged-in user [{}].".format(default_username))
    parser.add_argument("-p", "--password", dest="password", default=None, metavar="<password>",
        help="The password to be used when connecting (not recommended--use an authfile unless the username and password are transient).")
    parser.add_argument("-q", "--quiet", action="store_false", dest="verbose", default=True,
        help="Don't print status messages to stdout (only print errors).")
    parser.add_argument("-d", "--dest", dest="remote_filepath", default="/tmp/", metavar="<path>",
        help="Path where the file should be copied on the remote host (default: /tmp/).")
    parser.add_argument("-x", "--execute", action="store_true", dest="execute", default=False,
        help="Execute the copied file (just like executing a given command).")
    parser.add_argument("-r", "--remove", action="store_true", dest="remove", default=False,
        help="Remove (clean up) the SFTP'd file after execution.")
    parser.add_argument("-t", "--timeout", dest="timeout", default=30, metavar="<seconds>",
        help="Timeout (in seconds) before giving up on an SSH connection (default: 30)")
    parser.add_argument("-s", "--sudo", nargs="?", action="store", dest="sudo", default=False,
        help="Use sudo to execute the command (default: as root).")
    parser.add_argument("-X", "--passwordless", action="store_true", dest="passwordless", default=False,
        help="Use ssh keys without a password")
    parser.add_argument("-O", "--output-format", dest="output_format",
        choices=['csv', 'json'], default="csv",
        help="Ouptut format")

    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument("-c", "--copy-file", dest="local_filepath", default=None, metavar="<file>",
        help="Location of the file to copy to and optionally execute (-x) on hosts.")
    action_group.add_argument('commands', metavar='Commands', type=str, nargs='*', default=False,
        help='Commands')

    options = parser.parse_args()
    if options.hostfile:
        options.hosts = options.hostfile.read()
    elif options.stdin:
        # if stdin wasn't piped in, prompt the user for it now
        if not select.select([sys.stdin, ], [], [], 0.0)[0]:
            sys.stdout.write("Enter list of hosts (one entry per line). ")
            sys.stdout.write("Ctrl-D to end input.\n")
        # in either case, read data from stdin
        options.hosts = sys.stdin.read()
    elif options.hosts:
        options.hosts = options.hosts.split(":")
    elif options.ini_file:
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
        options.password = Password(password.rstrip('\n'))
    options.sudo = 'root' if options.sudo is None else options.sudo

    # Get the username and password to use when checking hosts
    if options.username is None:
        options.username = raw_input('Username: ')
    if options.keyfile and options.keypass is None and not options.passwordless:
        options.keypass = Password(getpass.getpass('Passphrase: '))
    elif options.password is None and not options.passwordless:
        options.password = Password(getpass.getpass('Password: '))
        if options.password == '':
            print ('\nPlease type the password')
            raise Exception('Please type the password')

    options.hosts = _normalize_hosts(options.hosts)
    return options


def main():
    """Main program function:  Grabs command-line arguments, starts up threads, and runs the program.
    """
    # Grab command line arguments and the command to run (if any)
    try:
        options = create_argument()
        if 0 != option_parse(options):
            return 2
        sshpt = SSHPowerTool(options)
        # This wierd little sequence of loops allows us to hit control-C
        # in the middle of program execution and get immediate results
        output_queue = sshpt()
        # Just to be safe we wait for the OutputThread to finish before moving on
        output_queue.join()
    except KeyboardInterrupt:
        print ('\ncaught KeyboardInterrupt, exiting...')
        # Return code should be 1 if the user issues a SIGINT (control-C)
        # Clean up
        stopSSHQueue()
        stopOutputThread()
        return 1
    return 0


if __name__ == '__main__':
    main()
