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

# TODO:  Add the ability to have host-specific usernames/passwords in the hostlist file
# TODO:  Add the ability to log in within private key( without password )
# TODO:  Add the ability to pass command line arguments to uploaded/executed files
# TODO:  Add stderr handling
# TODO:  Add ability to specify the ownership and permissions of uploaded files (when sudo is used)
# TODO:  Add logging using the standard module
# TODO:  Add the ability to specify a host list on the command line.  Something like '--hosts="host1:host2:host3"'

# Docstring:
"""
SSH Power Tool (SSHPT): This program will attempt to login via SSH to a list of servers supplied in a text file (one host per line).  It supports multithreading and will perform simultaneous connection attempts to save time (10 by default).  Results are output to stdout in CSV format and optionally, to an outfile (-o).
If no username and/or password are provided as command line arguments or via a credentials file the program will prompt for the username and password to use in the connection attempts.
This program is meant for situations where shared keys are not an option.  If all your hosts are configured with shared keys for passwordless logins you don't need the SSH Power Tool.
"""

# Meta
__license__ = "GNU General Public License (GPL) Version 3"
__version_info__ = (1, 3, 6)
__version__ = ".".join(map(str, __version_info__))
__author__ = 'Dan McDougall <YouKnowWho@YouKnowWhat.com>'
__second_author__ = 'Jonghak Choi <haginara@gmail.com>'

# Import built-in Python modules
import sys
import getpass
import select
from argparse import ArgumentParser
from time import sleep
import logging

# Import Internal
from OutputThread import startOutputThread, stopOutputThread
from SSHQueue import startSSHQueue, stopSSHQueue

logging.getLogger("sshpt")


def _parse_hostfile(host):
    keys = ['host', 'username', 'password']
    values = host.split(":")
    h = {}
    for i, value in enumerate(values):
        h[keys[i]] = values[i]

    return h


def _normalize_hosts(hosts):
    if hosts is None:
        return []

    if isinstance(hosts, str):
        hosts = [host for host in hosts.splitlines()]

    return [_parse_hostfile(host) if ':' in host else {'host': host} for host in hosts]


class SSHPowerTool:
    def __init__(self, hosts=None, **kwargs):
        self.hosts = _normalize_hosts(hosts)
        self.username = ""
        self.password = ""
        self.keyfile = ""
        self.keypass = ""
        self.max_threads = 10# Maximum number of simultaneous connection attempts
        self.timeout = 30# Connection timeout
        self.commands = False# List - Commands to execute on hosts (if False nothing will be executed)
        self.local_filepath = False# Local path of the file to SFTP
        self.remote_filepath = "/tmp/"# Destination path where the file should end up on the host
        self.execute = False# Whether or not the SFTP'd file should be executed after it is uploaded
        self.remove = False# Whether or not the SFTP'd file should be removed after execution
        self.sudo = False# Whether or not sudo should be used for commands and file operations
        self.run_as = 'root'# User to become when using sudo
        self.verbose = True# Whether or not we should output connection results to stdout
        self.outfile = None# Path to the file where we want to store connection results
        self.output_queue = None# Queue.Queue() where connection results should be put().  If none is given it will use the OutputThread default (output_queue)
        self.port = 22# Port to use when connecting
        self.ssh_connect_queue = None

        self.__dict__.update(**kwargs)

    def __call__(self):
        return self.run()

    def run(self):
        if self.output_queue is None:
            self.output_queue = startOutputThread(self.verbose, self.outfile)
        # Start up the Output and SSH threads
        self.ssh_connect_queue = startSSHQueue(self.output_queue, self.max_threads)

        if not self.commands and not self.local_filepath:
            # Assume we're just doing a connection test
            self.commands = ['echo CONNECTION TEST', ]

        if self.hosts:
            for host in self.hosts:
                if self.ssh_connect_queue.qsize() <= self.max_threads:
                    if self.username:
                        host['username'] = self.username
                    if self.password:
                        host['password'] = self.password
                    self.queueSSHConnection(
                        host['host'], host['username'], host['password'],
                        self.keyfile, self.keypass, self.timeout,
                        self.commands, self.local_filepath, self.remote_filepath,
                        self.execute, self.remove, self.sudo, self.run_as, self.port)
            sleep(1)
        # Wait until all jobs are done before exiting
        self.ssh_connect_queue.join()

        return self.output_queue

    def queueSSHConnection(self,
        host, username, password, keyfile, keypass, timeout,
        commands, local_filepath, remote_filepath,
        execute, remove, sudo, run_as, port):
        """Add files to the SSH Queue (ssh_connect_queue)"""
        queueObj = {}
        queueObj['host'] = host
        queueObj['username'] = username
        queueObj['password'] = password
        queueObj['keyfile'] = keyfile
        queueObj['keypass'] = keypass
        queueObj['timeout'] = timeout
        queueObj['commands'] = commands
        queueObj['local_filepath'] = local_filepath
        queueObj['remote_filepath'] = remote_filepath
        queueObj['execute'] = execute
        queueObj['remove'] = remove
        queueObj['sudo'] = sudo
        queueObj['run_as'] = run_as
        queueObj['port'] = port

        self.ssh_connect_queue.put(queueObj)

        return True


def option_parse(options):
    if not ( options.hostfile or options.stdin ):
        print "\nError:  At a minimum you must supply an input hostfile (-f) or pipe in the hostlist (--stdin)."
        return 1

    if options.hostfile == None and not options.stdin :
        print "Error: You must supply a file (-f <file>, -F <file>) containing the host list to check "
        print "or use the --stdin option to provide them via standard input"
        print "Use the -h option to see usage information."
        return 2

    if options.hostfile and options.stdin:
        print "Error: --file, --stdin and --host-auth-file are mutually exclusive.  Exactly one must be provided."
        return 2

    #if options.hostfile:
    #    print "Error: --file and --host-auth-file are mutually exclusive.  Exactly one must be provided."
    #    return 2

    if options.hostfile and options.stdin:
        print "Error: --file and --stdin are mutually exclusive.  Exactly one must be provided."
        return 2

    #if options.host_auth_file and options.stdin:
    #    print "Error: --host-auth-file and --stdin are mutually exclusive.  Exactly one must be provided."
    #    return 2

    if options.outfile is None and options.verbose is False:
        print "Error: You have not specified any mechanism to output results."
        print "Please don't use quite mode (-q) without an output file (-o <file>)."
        return 2

    #if local_filepath is not None and commands is not False:
    if options.copy_file is not None and options.commands is not False:
        print "Error: You can either run commands or execute a file.  Not both."
        return 2

    return 0


def create_argument():
    usage = 'usage: sshpt [options] "[command1]" "[command2]" ...'
    parser = ArgumentParser(usage=usage, version=__version__)
    #parser.disable_interspersed_args()
    parser.add_argument("-f", "--file", dest="hostfile", default=None, help="Location of the file containing the host list.", metavar="<file>")
    parser.add_argument("-S", "--stdin", dest="stdin", default=False, action="store_true", help="Read hosts from standard input")
    #parser.add_argument("-F", "--host-auth-file", dest="host_auth_file", default=None, help="Location of the file containing the host and credentials list.", metavar="<file>")
    parser.add_argument("-k", "--key-file", dest="keyfile", default=None, help="Location of the private key file", metavar="<file>")
    parser.add_argument("-K", "--key-pass", dest="keypass", default=None, help="The password to be used when use the private key file).", metavar="<password>")
    parser.add_argument("-o", "--outfile", dest="outfile", default=None, help="Location of the file where the results will be saved.", metavar="<file>")
    parser.add_argument("-a", "--authfile", dest="authfile", default=None, help='Location of the file containing the credentials to be used for connections (format is "username:password").', metavar="<file>")
    parser.add_argument("-T", "--threads", dest="max_threads", type=int, default=10, help="Number of threads to spawn for simultaneous connection attempts [default: 10].", metavar="<int>")
    parser.add_argument("-P", "--port", dest="port", type=int, default=22, help="The port to be used when connecting.  Defaults to 22.", metavar="<port>")
    parser.add_argument("-u", "--username", dest="username", default='root', help="The username to be used when connecting.  Defaults to the currently logged-in user.", metavar="<username>")
    parser.add_argument("-p", "--password", dest="password", default=None, help="The password to be used when connecting (not recommended--use an authfile unless the username and password are transient).", metavar="<password>")
    parser.add_argument("-q", "--quiet", action="store_false", dest="verbose", default=True, help="Don't print status messages to stdout (only print errors).")
    parser.add_argument("-c", "--copy-file", dest="copy_file", default=None, help="Location of the file to copy to and optionally execute (-x) on hosts.", metavar="<file>")
    parser.add_argument("-d", "--dest", dest="destination", default="/tmp/", help="Path where the file should be copied on the remote host (default: /tmp/).", metavar="<path>")
    parser.add_argument("-x", "--execute", action="store_true", dest="execute", default=False, help="Execute the copied file (just like executing a given command).")
    parser.add_argument("-r", "--remove", action="store_true", dest="remove", default=False, help="Remove (clean up) the SFTP'd file after execution.")
    parser.add_argument("-t", "--timeout", dest="timeout", default=30, help="Timeout (in seconds) before giving up on an SSH connection (default: 30)", metavar="<seconds>")
    parser.add_argument("-s", "--sudo", action="store_true", dest="sudo", default=False, help="Use sudo to execute the command (default: as root).")
    parser.add_argument("-U", "--sudouser", dest="run_as", default="root", help="Run the command (via sudo) as this user.", metavar="<username>")
    parser.add_argument('commands', metavar='C', type=str, nargs='*', help='Commands', default=False)

    options = parser.parse_args()

    return options


def main():
    """Main program function:  Grabs command-line arguments, starts up threads, and runs the program.
    """
    # Grab command line arguments and the command to run (if any)
    options = create_argument()
    if 0 != option_parse(options):
        return 2

    sshpt = SSHPowerTool()
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

    # Read in the host list to check
    ## host_auth_file format
    ## credential@host
    ## user:pass@host
    if options.hostfile:
        # add username and password as well
        # Format:
        # <user:password>@<host>
        hostlist = open(options.hostfile).read()

    elif options.stdin:
        # if stdin wasn't piped in, prompt the user for it now
        from platform import system
        if not select.select([sys.stdin, ], [], [], 0.0)[0]:
            sys.stdout.write("Enter list of hosts (one entry per line). ")
            sys.stdout.write("Ctrl-D to end input.\n")
        # in either case, read data from stdin
        hostlist = sys.stdin.read()

    if options.authfile is not None:
        credentials = open(options.authfile).readline()
        username, password = credentials.split(":")
        password = password.rstrip('\n') # Get rid of trailing newline

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

    hostlist_list = []
    try: # This wierd little sequence of loops allows us to hit control-C in the middle of program execution and get immediate results
        for host in hostlist.split("\n"): # Turn the hostlist into an actual list
            if host != "":
                if not host.startswith('#'):
                    hostlist_list.append(host)
        output_queue = sshpt(hostlist_list)
        output_queue.join() # Just to be safe we wait for the OutputThread to finish before moving on
    except KeyboardInterrupt:
        print 'caught KeyboardInterrupt, exiting...'
        return_code = 1 # Return code should be 1 if the user issues a SIGINT (control-C)
        # Clean up
        stopSSHQueue()
        stopOutputThread()
    except Exception, detail:
        print 'caught Exception...'
        print(sys.exc_info())
        print detail
        return_code = 2
        # Clean up
        stopSSHQueue()
        stopOutputThread()
    return return_code

if __name__ == '__main__':
    main()
