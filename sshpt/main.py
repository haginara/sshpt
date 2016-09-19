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

import select
import getpass
from ConfigParser import ConfigParser
from argparse import ArgumentParser

from . import version
from .sshpt import SSHPowerTool


def option_parse(options):
    if options.outfile is None and options.verbose is False:
        print "Error: You have not specified any mechanism to output results."
        print "Please don't use quite mode (-q) without an output file (-o <file>)."
        return 2

    return 0


def create_argument():
    usage = 'usage: sshpt [options] "[command1]" "[command2]" ...'
    parser = ArgumentParser(usage=usage, version=version.__version__)

    host_group = parser.add_mutually_exclusive_group(required=True)
    host_group.add_argument("-f", "--file", dest="hostfile", default=None,
        help="Location of the file containing the host list.", type=open)
    host_group.add_argument("-S", "--stdin", dest="stdin", default=False,
        action="store_true", help="Read hosts from standard input")
    host_group.add_argument("--hosts", dest='hosts', default=None,
        help='Specify a host list on the command line. ex)--hosts="host1:host2:host3"')

    host_group.add_argument("-i", "--ini", default=None, nargs=3,
        help="Configuration file with INI Format. ini path, server, command")
    host_group.add_argument("-j", "--json", default=None,
        help="Configuration file with JSON Format")

    parser.add_argument("-k", "--key-file", dest="keyfile", default=None,
        help="Location of the private key file", metavar="<file>")
    parser.add_argument("-K", "--key-pass", dest="keypass", default=None,
        help="The password to be used when use the private key file).",
        metavar="<password>")
    parser.add_argument("-o", "--outfile", dest="outfile", default=None,
        help="Location of the file where the results will be saved.", metavar="<file>")
    parser.add_argument("-a", "--authfile", dest="authfile", default=None,
        help='Location of the file containing the credentials to be used for connections (format is "username:password").', metavar="<file>")
    parser.add_argument("-T", "--threads", dest="max_threads", type=int, default=10,
        help="Number of threads to spawn for simultaneous connection attempts [default: 10].", metavar="<int>")
    parser.add_argument("-P", "--port", dest="port", type=int, default=22,
        help="The port to be used when connecting.  Defaults to 22.", metavar="<port>")
    parser.add_argument("-u", "--username", dest="username", default='root',
        help="The username to be used when connecting.  Defaults to the currently logged-in user.", metavar="<username>")
    parser.add_argument("-p", "--password", dest="password", default=None,
        help="The password to be used when connecting (not recommended--use an authfile unless the username and password are transient).", metavar="<password>")
    parser.add_argument("-q", "--quiet", action="store_false", dest="verbose",
        default=True, help="Don't print status messages to stdout (only print errors).")
    parser.add_argument("-d", "--dest", dest="destination", default="/tmp/",
        help="Path where the file should be copied on the remote host (default: /tmp/).", metavar="<path>")
    parser.add_argument("-x", "--execute", action="store_true", dest="execute",
        default=False, help="Execute the copied file (just like executing a given command).")
    parser.add_argument("-r", "--remove", action="store_true", dest="remove",
        default=False, help="Remove (clean up) the SFTP'd file after execution.")
    parser.add_argument("-t", "--timeout", dest="timeout", default=30,
        help="Timeout (in seconds) before giving up on an SSH connection (default: 30)", metavar="<seconds>")
    parser.add_argument("-s", "--sudo", action="store_true", dest="sudo", default=False,
        help="Use sudo to execute the command (default: as root).")
    parser.add_argument("-U", "--sudouser", dest="run_as", default="root",
        help="Run the command (via sudo) as this user.", metavar="<username>")

    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument("-c", "--copy-file", dest="copy_file", default=None,
        help="Location of the file to copy to and optionally execute (-x) on hosts.",
        metavar="<file>")
    action_group.add_argument('commands', metavar='Commands', type=str, nargs='*',
        help='Commands', default=False)

    options = parser.parse_args()

    return options


def main():
    """Main program function:  Grabs command-line arguments, starts up threads, and runs the program.
    """
    # Grab command line arguments and the command to run (if any)
    try:
        options = create_argument()
        if 0 != option_parse(options):
            return 2

        # Read in the host list to check
        ## host_auth_file format
        ## credential@host
        ## user:pass@host
        if options.hostfile:
            # Format:
            # <user:password>@<host>
            hosts = options.hostfile.read()
        elif options.stdin:
            # if stdin wasn't piped in, prompt the user for it now
            if not select.select([sys.stdin, ], [], [], 0.0)[0]:
                sys.stdout.write("Enter list of hosts (one entry per line). ")
                sys.stdout.write("Ctrl-D to end input.\n")
            # in either case, read data from stdin
            hosts = sys.stdin.read()
        elif options.hosts:
            hosts = options.hosts.split(":")
        elif options.ini:
            ini_config = ConfigParser()
            ini_config.readfp(open(options.ini))

        sshpt = SSHPowerTool(hosts=hosts)
        sshpt.commands = options.commands

        # Check to make sure we were passed at least one command line argument
        return_code = 0

        # Assign the options to more readable variables
        sshpt.username = options.username
        sshpt.password = options.password
        sshpt.keyfile = options.keyfile
        sshpt.keypass = options.keypass
        sshpt.port = options.port
        sshpt.local_filepath = options.copy_file
        sshpt.remote_filepath = options.destination
        sshpt.execute = options.execute
        sshpt.remove = options.remove
        sshpt.sudo = options.sudo
        sshpt.max_threads = options.max_threads
        sshpt.timeout = options.timeout
        sshpt.run_as = options.run_as
        sshpt.verbose = options.verbose
        sshpt.outfile = options.outfile

        if options.authfile is not None:
            credentials = open(options.authfile).readline()
            username, password = credentials.split(":")
            # Get rid of trailing newline
            password = password.rstrip('\n')

        # Get the username and password to use when checking hosts
        if sshpt.username is None:
            sshpt.username = raw_input('Username: ')
        if sshpt.keyfile:
            if sshpt.keypass is None:
                sshpt.keypass = getpass.getpass('Passphrase: ')
        elif sshpt.password is None:
            sshpt.password = getpass.getpass('Password: ')
            if sshpt.password == '':
                print '\nPleas type the password'
                return 2
        # This wierd little sequence of loops allows us to hit control-C
        # in the middle of program execution and get immediate results
        output_queue = sshpt()
        # Just to be safe we wait for the OutputThread to finish before moving on
        output_queue.join()
    except KeyboardInterrupt:
        print 'caught KeyboardInterrupt, exiting...'
        # Return code should be 1 if the user issues a SIGINT (control-C)
        return_code = 1
        # Clean up
        stopSSHQueue()
        stopOutputThread()
    except Exception, detail:
        print(str(detail))
        return_code = 2
        # Clean up
        stopSSHQueue()
        stopOutputThread()
    return return_code
