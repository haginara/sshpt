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
# TODO:  Add the ability to pass command line arguments to uploaded/executed files
# TODO:  Add stderr handling
# TODO:  Add ability to specify the ownership and permissions of uploaded files (when sudo is used)
# TODO:  Add logging using the standard module
# TODO:  Supports Python3

# Docstring:
"""
SSH Power Tool (SSHPT): This program will attempt to login via SSH to a list of servers supplied in a text file (one host per line).  It supports multithreading and will perform simultaneous connection attempts to save time (10 by default).  Results are output to stdout in CSV format and optionally, to an outfile (-o).
If no username and/or password are provided as command line arguments or via a credentials file the program will prompt for the username and password to use in the connection attempts.
This program is meant for situations where shared keys are not an option.  If all your hosts are configured with shared keys for passwordless logins you don't need the SSH Power Tool.
"""


# Import built-in Python modules
import sys

from time import sleep
import logging

# Import Internal
from OutputThread import startOutputThread, stopOutputThread
from SSHQueue import startSSHQueue, stopSSHQueue

logger = logging.getLogger("sshpt")


def _parse_hostfile(host):
    keys = ['host', 'username', 'password']
    h = {'host': '', 'username': '', 'password': ''}
    values = host.split(":")
    for i, value in enumerate(values):
        h[keys[i]] = values[i]

    return h


def _normalize_hosts(hosts):
    if hosts is None:
        return []

    if isinstance(hosts, str):
        hosts = filter(lambda h: (not h.startswith("#") and h != ""), hosts.splitlines())
        hosts = [host.strip() for host in hosts]

    return [_parse_hostfile(host) if ':' in host else {
        'host': host, 'username': '', 'password': ''} for host in hosts]


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
        self._params = {}

        self.__dict__.update(**kwargs)

    def __call__(self):
        return self.run()

    def params(self, **kwargs):
        """
        """
        self._params.update(kwargs)

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
                        self.keyfile, self.keypass,
                        self.timeout,
                        self.commands, self.local_filepath, self.remote_filepath,
                        self.execute, self.remove, self.sudo, self.run_as, self.port)
                sleep(1)
        else:
            logging.error("Hosts are not given")
        # Wait until all jobs are done before exiting
        self.ssh_connect_queue.join()

        return self.output_queue

    def queueSSHConnection(self, host, username, password, keyfile, keypass, timeout,
        commands, local_filepath, remote_filepath, execute, remove, sudo, run_as, port):
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
