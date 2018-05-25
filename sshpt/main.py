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
from .SSHQueue import stopSSHQueue
from .OutputThread import stopOutputThread

from .Generic import Password

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
        self.commands = []
        self.connect_data = {
            'port': self.port,
            'username': self.username,
            'timeout': self.timeout
        }
        if keyfile:
            self.connect_data['pkey'] = self.create_key(keyfile, self.password)
        else:
            self.connect_data['password'] = self.password

    def create_key(self, key_file, key_pass=None):
        try:
            key = paramkio.RSAKey.from_private_key_file(key_file, password=key_pass)
        except Exception as ex:
            logger.error("Error: Create_key: %s", ex)
        return key

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
        if local_filepath:
            logger.info("sudo: %s, local_filepath: %s, remote_filepath: %s", sudo, local_filepath, remote_filepath)
            local_short_filename = os.path.basename(local_filepath)
            remote_fullpath = os.path.join(remote_filepath + '/', local_short_filename)
            try:
                if sudo:
                    temp_path = os.path.join('/tmp/', local_short_filename)
                    logger.info("Put the file temp first %s to %s", local_filepath, temp_path)
                    self.sftpPut(ssh, local_filepath, temp_path)
                    command_output.append(self.executeCommand(ssh, command="mv %s %s" % (temp_path, remote_fullpath), sudo=sudo, password=password))
                else:
                    self.sftpPut(ssh, local_filepath, remote_fullpath)

                if execute:
                    # Make it executable (a+x in case we run as another user via sudo)
                    chmod_command = "chmod a+x %s" % remote_fullpath
                    self.executeCommand(ssh=ssh, command=chmod_command, sudo=sudo, password=password)
                    # The command to execute is now the uploaded file
                    commands = [remote_fullpath, ]
                else:
                    # We're just copying a file (no execute) so let's return it's details
                    commands = ["ls -l %s" % remote_fullpath, ]
            except IOError as details:
                # i.e. permission denied
                # Make sure the error is included in the command output
                command_output.append(str(details))
        try:
            remove = False
            if commands:
                for command in commands:
                    # This makes a list of lists (each line of output in command_output is it's own item in the list)
                    command_output.append(self.executeCommand(ssh=ssh, command=command, sudo=sudo, password=password))
                    remove = True
            if local_filepath is False and commands is False and execute is False:
                # If we're not given anything to execute run the uptime command to make sure that we can execute *something*
                command_output = self.executeCommand(ssh=ssh, command='uptime', sudo=sudo, password=password)
            if local_filepath and remove:
                # Clean up/remove the file we just uploaded and executed
                rm_command = "rm -f %s" % remote_fullpath
                self.executeCommand(ssh=ssh, command=rm_command, sudo=sudo, password=password)
            command_output = [normalizeString(output) for output in command_output]
        except Exception as detail:
            # Connection failed
            print (sys.exc_info())
            print("Exception: %s" % detail)
            connection_result = False
            command_output = detail
        finally:
            if not isinstance(ssh, basestring):
                ssh.close()
        return connection_result, command_output

    def sftpPut(self, ssh, local_filepath, remote_filepath):
        """Uses SFTP to transfer a local file (local_filepath) to a remote server at the specified path (remote_filepath) using the given Paramiko transport object."""
        sftp = ssh.open_sftp()
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
        parser = ArgumentParser(usage=usage)
        parser.add_argument('-v', '--version', action='version', version=version.__version__)
        parser.add_argument("-f", "--conf-file", dest="hostfile", default='servers.yaml', type=read_conf_file,
            help="Location of the file containing the host list.")
        parser.add_argument("-T", "--threads", dest="max_threads", type=int, default=10, metavar="<int>",
            help="Number of threads to spawn for simultaneous connection attempts [default: 10].")
        parser.add_argument("group",
            help="Group of servers that you want to command remotely")
        parser.add_argument("-q", "--quiet", action="store_false", dest="verbose", default=True,
            help="Don't print status messages to stdout (only print errors).")
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
        logger.info("%s", self.options)

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
        parser.add_argument("-o", "--outfile", dest="outfile", default=None, metavar="<file>",
            help="Location of the file where the results will be saved.")
        parser.add_argument("-of", "--output-format", dest="output_format", choices=['csv', 'json'], default="csv",
            help="Ouptut format")
        parser.add_argument('commands', metavar='Commands', type=str, nargs='*', default=False,
            help='Commands')
        args = parser.parse_args(argument)
        return args

    def servers(self):
        servers = self.hostfile['servers']
        if self.group == '*':
            servers = [ServerConnection.from_dict(server) for server in servers]
        elif 'ip:' in self.group:
            _ip = self.group[3:]
            servers = [ServerConnection.from_dict(server) for server in servers if fnmatch.fnmatch(_ip, server['host'])]
        else:
            servers = [ServerConnection.from_dict(server) for server in servers if fnmatch.fnmatch(self.group, server)]

        for server in servers:
            server.subcommand = self.options.subcommand
            server.subcommand_args = self.options.subcommand_args
            yield server

def main():
    """Main program function:  Grabs command-line arguments, starts up threads, and runs the program.
    """
    # Grab command line arguments and the command to run (if any)
    args = ArgParser()
    options = args.options
    sys.exit(2)
    #options = create_argument()
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
        logger.error ('caught KeyboardInterrupt, exiting...')
        # Return code should be 1 if the user issues a SIGINT (control-C)
        # Clean up
        stopSSHQueue()
        stopOutputThread()
        return 1
    return 0


if __name__ == '__main__':
    main()
