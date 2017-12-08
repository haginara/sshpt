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

from .Generic import GenericThread, normalizeString

import sys
import os
import threading
if sys.version_info[0] == 3:
    import queue as Queue
    basestring = str
else:
    import Queue
import getpass
import logging

logger = logging.getLogger("sshpt")

# Import 3rd party modules
try:
    import paramiko
    logging.getLogger("paramiko").setLevel(logging.WARNING)
except ImportError:
    print("ERROR: The Paramiko module required to use sshpt.")
    print("Download it here: http://www.lag.net/paramiko/")
    sys.exit(1)
#paramiko.util.log_to_file("debug.log")


class SSHThread(GenericThread):
    """Connects to a host and optionally runs commands or copies a file over SFTP.
    Must be instanciated with:
      id                    A thread ID
      ssh_connect_queue     Queue.Queue() for receiving orders
      output_queue          Queue.Queue() to output results

    Here's the list of variables that are added to the output queue before it is put():
        queueObj['host']
        queueObj['port']
        queueObj['username']
        queueObj['password']
        queueObj['commands'] - List: Commands that were executed
        queueObj['local_filepath'] - String: SFTP local file path
        queueObj['remote_filepath'] - String: SFTP file destination path
        queueObj['execute'] - Boolean
        queueObj['remove'] - Boolean
        queueObj['sudo'] - Boolean
        queueObj['connection_result'] - String: 'SUCCESS'/'FAILED'
        queueObj['command_output'] - String: Textual output of commands after execution
    """
    def __init__(self, id, ssh_connect_queue, output_queue):
        super(SSHThread, self).__init__(name="SSHThread-%d" % (id))
        self.ssh_connect_queue = ssh_connect_queue
        self.output_queue = output_queue
        self.id = id
        self.quitting = False

    def run(self):
        try:
            while not self.quitting:
                queueObj = self.ssh_connect_queue.get()
                if queueObj == 'quit':
                    self.quit()
                success, command_output = self.attemptConnection(**queueObj)
                queueObj['connection_result'] = "SUCCESS" if success else "FAILED"
                queueObj['command_output'] = command_output
                self.output_queue.put(queueObj)
                self.ssh_connect_queue.task_done()
        except Exception as e:
            print ("Failed to run SSH Thread reason: %s" % e)
            self.quit()

    def create_key(self, key_file, key_passwd):
        try:
            key = paramiko.RSAKey.from_private_key_file(key_file)
        except paramiko.PasswordRequiredException:
            if not key_passwd:
                key_passwd = getpass.getpass("Enter passphrase for %s: " % key_file)
            key = paramiko.RSAKey.from_private_key_file(key_file, password=key_passwd)
        except Exception as detail:
            logger.error("Error: Create_key: %s", detail)
        return key

    def paramikoConnect(self, host, username, password, timeout, port=22, key_file="", key_pass=""):
        """Connects to 'host' and returns a Paramiko transport object to use in further communications"""
        # Uncomment this line to turn on Paramiko debugging (good for troubleshooting why some servers report connection failures)
        #paramiko.util.log_to_file('paramiko.log')
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        logger.debug("paramikoConnect:connect, %s:%s", username, host)

        try:
            if key_file:
                key = self.create_key(key_file, key_pass)
                ssh.connect(host, port=port, username=username, timeout=timeout, pkey=key)
            else:
                ssh.connect(host, port=port, username=username, password=password, timeout=timeout)
        except paramiko.SSHException as detail:
            logger.error('Could not read private key; bad password?, %s', detail)
            ssh = str(detail)
        except Exception as detail:
            logger.error('Connecting failed (for whatever reason: %s)', detail)
            ssh = str(detail)
        return ssh

    def sftpPut(self, ssh, local_filepath, remote_filepath):
        """Uses SFTP to transfer a local file (local_filepath) to a remote server at the specified path (remote_filepath) using the given Paramiko transport object."""
        sftp = ssh.open_sftp()
        filename = os.path.basename(local_filepath)
        if filename not in remote_filepath:
            remote_filepath = os.path.normpath(remote_filepath + "/")
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
            stdout, stderr = self.sudoExecute(transport=ssh, command=command, password=password, sudo=sudo)
        else:
            stdin, stdout, stderr = ssh.exec_command(command)
        command_output = stdout.readlines()
        command_output = "".join(command_output)

        return command_output

    def attemptConnection(self, host, username="", password="", keyfile="", keypass="", timeout=30, commands=[],
        local_filepath=False, remote_filepath='/tmp', execute=False, remove=False, sudo=False, port=22):
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
        ssh = self.paramikoConnect(host, username, password=password, timeout=timeout, port=port, key_file=keyfile, key_pass=keypass)
        if isinstance(ssh, basestring):
            # If ssh is a string that means the connection failed and 'ssh' is the details as to why
            connection_result = False
            command_output = ssh
            return connection_result, command_output

        command_output = []
        if local_filepath:
            remote_filepath = remote_filepath.rstrip('/')
            local_short_filename = local_filepath.split("/")[-1] or "sshpt_temp"
            remote_fullpath = "%s/%s" % (remote_filepath, local_short_filename)
            try:
                if sudo:
                    temp_path = "/tmp/%s" % local_short_filename
                    self.sftpPut(ssh, local_filepath, temp_path)
                    command_output.append(self.executeCommand(ssh, "mv %s %s" % (temp_path, remote_fullpath), sudo, run_as, password))
                else:
                    self.sftpPut(ssh, local_filepath, remote_fullpath)
            except IOError as details:
                # i.e. permission denied
                # Make sure the error is included in the command output
                command_output.append(str(details))
        try:
            if execute:
                # Make it executable (a+x in case we run as another user via sudo)
                chmod_command = "chmod a+x %s" % remote_fullpath
                self.executeCommand(transport=ssh, command=chmod_command, sudo=sudo, password=password)
                # The command to execute is now the uploaded file
                commands = [remote_fullpath, ]
            else:
                # We're just copying a file (no execute) so let's return it's details
                commands = ["ls -l %s" % remote_fullpath, ]

            for command in commands:
                # This makes a list of lists (each line of output in command_output is it's own item in the list)
                command_output.append(self.executeCommand(transport=ssh, command=command, sudo=sudo, password=password))
            elif commands is False and execute is False:
                # If we're not given anything to execute run the uptime command to make sure that we can execute *something*
                command_output = self.executeCommand(transport=ssh, command='uptime', sudo=sudo, password=password)
            if local_filepath and remove:
                # Clean up/remove the file we just uploaded and executed
                rm_command = "rm -f %s" % remote_fullpath
                self.executeCommand(transport=ssh, command=rm_command, sudo=sudo, password=password)

            command_count = 0
            for output in command_output:
                # Clean up the command output
                command_output[command_count] = normalizeString(output)
                command_count = command_count + 1
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


def startSSHQueue(output_queue, max_threads):
    """Setup concurrent threads for testing SSH connectivity.  Must be passed a Queue (output_queue) for writing results."""
    ssh_connect_queue = Queue.Queue()
    for thread_num in range(max_threads):
        ssh_thread = SSHThread(thread_num, ssh_connect_queue, output_queue)
        ssh_thread.setDaemon(True)
        ssh_thread.start()
    return ssh_connect_queue


def stopSSHQueue():
    """Shut down the SSH Threads"""
    for t in threading.enumerate():
        if t.getName().startswith('SSHThread'):
            t.quit()
    return True
