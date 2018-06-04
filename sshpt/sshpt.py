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
try:
    import queue as Queue
except ImportError:
    import Queue

import paramiko

# Import Internal
from .Generic import Password
from .Generic import normalizeString

from .OutputThread import startOutputThread, stopOutputThread
from .SSHQueue import startSSHQueue, stopSSHQueue

logger = logging.getLogger(__name__)


class SSHPowerTool(object):
    #def __init__(self, **kwargs):
    def __init__(self, options):
        self.options = options
        self.output_queue = Queue.Queue() # Queue.Queue() where connection results should be put().  If none is given it will use the OutputThread default (output_queue)
        self.ssh_connect_queue = Queue.Queue()

    def __call__(self):
        return self.run()

    def run(self):
        if self.output_queue is None:
            self.output_queue = startOutputThread(self.options.verbose, self.options.outfile, self.options.output_format)
        # Start up the Output and SSH threads
        self.ssh_connect_queue = startSSHQueue(self.output_queue, self.options.max_threads)
        if not self.options.commands and not self.options.local_filepath:
            # Assume we're just doing a connection test
            self.options.commands = ['echo CONNECTION TEST', ]

        for server in self.options.servers():
            if self.ssh_connect_queue.qsize() <= self.options.max_threads:
                self.ssh_connect_queue.put(server)
        self.ssh_connect_queue.join()

        return self.output_queue


class ServerConnection:
    def __init__(self, host, port=22, username=None, sudo=False, password=None, keyfile=None, timeout=30):
        self.host = host
        self.port = port
        self.username = username
        self.sudo = sudo
        self.password = password
        self.timeout = timeout
        self.subcommand = None
        self.subcommand_args = None
        self.connection_result = None
        self.command_output = None
        self.connect_data = {
            'port': self.port,
            'username': self.username,
            'timeout': self.timeout
        }
        if keyfile:
            self.connect_data['pkey'] = self.create_key(keyfile, self.password)
        else:
            self.connect_data['password'] = self.password

    def __getattr__(self, key):
        if key not in self.__dict__:
            return getattr(self.subcommand_args, key)
        return getattr(self, key)

    def create_key(self, key_file, keypass=None):
        try:
            key = paramiko.RSAKey.from_private_key_file(key_file, password=keypass)
            return key
        except Exception as ex:
            logger.error("Error: Create_key: %s", ex)
        return None

    def get_connection(self):
        """Connects to 'host' and returns a Paramiko transport object to use in further communications"""
        # Uncomment this line to turn on Paramiko debugging (good for troubleshooting why some servers report connection failures)
        #paramiko.util.log_to_file('paramiko.log')
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            logger.debug("paramikoConnect:connect, %s:%s", self.host, self.username)
            ssh.connect(self.host, **self.connect_data)
        except paramiko.SSHException as detail:
            raise Exception(detail)
        except Exception as detail:
            raise Exception(detail)
        return ssh

    def attemptConnection(self):
        """Attempt to login to 'host' using 'username'/'password' and execute 'commands'.
        Will excute commands via sudo if 'sudo' is set to True (as root by default) and optionally as a given user (sudo).
        Returns connection_result as a boolean and command_output as a string."""
        # Connection timeout
        # Either False for no commnads or a list
        # Local path of the file to SFTP
        # Destination path where the file should end up on the host
        # Whether or not the SFTP'd file should be executed after it is uploaded
        # Whether or not the SFTP'd file should be removed after execution
        # Whether or not sudo should be used for commands and file operations
        # User to become when using sudo
        # Port to use when connecting

        connection_result = True
        command_output = []
        ssh = self.get_connection()

        ## Check scp or cmd or both(?)
        if self.subcommand == 'scp':
            logger.info("sudo: %s, local_filepath: %s, remote_filepath: %s",
                self.sudo, self.subcommand_args.local, self.subcommand_args.remote)
            self.sftpPut(ssh, local=self.subcommand_args.local, remote=elf.subcommand_args.remote, sudo=self.sudo)
            local_short_filename = os.path.basename(self.subcommand_args.local)
            remote_fullpath = os.path.join(self.subcommand_args.remote + '/', local_short_filename)
            if self.sudo:
                temp_path = os.path.join('/tmp/', local_short_filename)
                logger.info("Put the file temp first %s to %s", self.subcommand_args.local, temp_path)
                self.sftpPut(ssh, self.subcommand_args.local, temp_path)
                self.executeCommand(ssh, command="mv %s %s" % (temp_path, self.subcommand_args.remote),
                    sudo=self.sudo, password=self.password)
            else:
                self.sftpPut(ssh, self.subcommand_args.local, self.subcommand_args.remote)

            if self.subcommand_args.execute:
                # Make it executable (a+x in case we run as another user via sudo)
                chmod_command = "chmod a+x %s" % remote_fullpath
                self.executeCommand(ssh=ssh, command=chmod_command, sudo=self.sudo, password=self.password)
                # The command to execute is now the uploaded file
                commands = [remote_fullpath, ]
                if self.subcommand_args.remove:
                    # Clean up/remove the file we just uploaded and executed
                    rm_command = "rm -f %s" % remote_fullpath
                    self.executeCommand(ssh=ssh, command=rm_command, sudo=self.sudo, password=self.password)
            else:
                # We're just copying a file (no execute) so let's return it's details
                commands = ["ls -l %s" % remote_fullpath, ]
        elif self.subcommand == 'cmd':
            for command in self.subcommand_args.commands:
                # This makes a list of lists (each line of output in command_output is it's own item in the list)
                command_output.append(self.executeCommand(ssh=ssh, command=command, sudo=self.sudo, password=self.password))
            command_output = [normalizeString(output) for output in command_output]
            ssh.close()
            return connection_result, command_output

    def sftpPut(self, ssh, local, remote, sudo=False):
        """Uses SFTP to transfer a local file (local_filepath) to a remote server at the specified path (remote_filepath) using the given Paramiko transport object."""
        sftp = ssh.open_sftp()
        local_short_filename = os.path.basename(local)
        remote_fullpath = remote + '/' + local_short_filename
        if sudo:
            logger.info("Put the file temp first %s to %s", local, temp_path)
            temp_path = os.path.join('/tmp/', local_short_filename)
            command_output.append(
                self.executeCommand(ssh, command="mv %s %s" % (temp_path, remote_fullpath), sudo=sudo, password=password))
        filename = os.path.basename(local_filepath)
        if filename not in remote_filepath:
            remote_filepath = os.path.normpath(remote_filepath + "/")
        logger.info("Put file from %s to %s", local_filepath, remote_filepath)
        sftp.put(local_filepath, remote_filepath)

    def sudoExecute(self, ssh, command, password, sudo):
        """Executes the given command via sudo as the specified user (sudo) using the given Paramiko transport object.
        Returns stdout, stderr (after command execution)"""
        logger.debug("Run sudoExecute: %s, %s", sudo, command)
        stdin, stdout, stderr = ssh.exec_command("sudo -S -u %s %s" % (sudo, command))
        if stdout.channel.closed is False:
            # If stdout is still open then sudo is asking us for a password
            stdin.write('%s\n' % password)
            stdin.flush()
        return stdout, stderr

    def executeCommand(self, ssh, command, sudo, password=None):
        """Executes the given command via the specified Paramiko transport object.  Will execute as sudo if passed the necessary variables (sudo=True, password, sudo).
        Returns stdout (after command execution)"""
        host = ssh.get_host_keys().keys()[0]
        if sudo:
            stdout, stderr = self.sudoExecute(ssh=ssh, command=command, password=password, sudo=sudo)
        else:
            stdin, stdout, stderr = ssh.exec_command(command)
        command_output = stdout.readlines()
        command_output = "".join(command_output)
        return command_output

    @classmethod
    def from_dict(cls, data):
        return cls(**data)
