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
from __future__ import absolute_import
import sys

from time import sleep
import logging

# Import Internal
from .OutputThread import startOutputThread, stopOutputThread
from .SSHQueue import startSSHQueue, stopSSHQueue

logger = logging.getLogger("sshpt")


class SSHPowerTool(object):
    #def __init__(self, **kwargs):
    def __init__(self, options):
        self.options = options
        self.hosts = ""
        self.username = ""
        self.password = ""
        self.keyfile = ""
        self.keypass = ""
        self.max_threads = 10 # Maximum number of simultaneous connection attempts
        self.timeout = 30 # Connection timeout
        self.commands = False # List - Commands to execute on hosts (if False nothing will be executed)
        self.local_filepath = False # Local path of the file to SFTP
        self.remote_filepath = "/tmp/" # Destination path where the file should end up on the host
        self.execute = False # Whether or not the SFTP'd file should be executed after it is uploaded
        self.remove = False # Whether or not the SFTP'd file should be removed after execution
        self.sudo = 'root' # Whether or not sudo should be used for commands and file operations
        self.verbose = True # Whether or not we should output connection results to stdout
        self.outfile = None # Path to the file where we want to store connection results
        self.output_queue = None # Queue.Queue() where connection results should be put().  If none is given it will use the OutputThread default (output_queue)
        self.port = 22 # Port to use when connecting
        self.ssh_connect_queue = None
        self._params = {}

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

        for host in self.options.hosts:
            if self.ssh_connect_queue.qsize() <= self.max_threads:
                queueObj = dict(
                    host=host.get('host'), username=host.get('username', self.options.username), password=host.get('password', self.options.password),
                    keyfile=self.options.keyfile, keypass=self.options.keypass,
                    timeout=self.options.timeout,
                    commands=self.options.commands,
                    local_filepath=self.options.local_filepath, remote_filepath=self.options.local_filepath,
                    execute=self.options.execute, remove=self.options.remove, sudo=self.options.sudo, port=self.options.port)
                self.ssh_connect_queue.put(queueObj)
            sleep(0.1)
        # Wait until all jobs are done before exiting
        self.ssh_connect_queue.join()

        return self.output_queue
