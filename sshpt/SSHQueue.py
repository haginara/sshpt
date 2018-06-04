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
    """
    Connects to a host and optionally runs commands or copies a file over SFTP.
    Must be instanciated with:
      id                    A thread ID
      ssh_connect_queue     Queue.Queue() for receiving orders
      output_queue          Queue.Queue() to output results
     """
    def __init__(self, id, ssh_connect_queue, output_queue):
        super(SSHThread, self).__init__(name="SSHThread-%d" % (id))
        self.ssh_connect_queue = ssh_connect_queue
        self.output_queue = output_queue
        self.id = id
        self.quitting = False

    def run(self):
        while not self.quitting:
            queueObj = self.ssh_connect_queue.get()
            logger.info("SSH Queue: %s", queueObj)
            if queueObj == 'quit':
                self.quit()
            success, command_output = queueObj.attemptConnection()
            queueObj.connection_result = "SUCCESS" if success else "FAILED"
            queueObj.command_output = command_output
            self.output_queue.put(queueObj)
            self.ssh_connect_queue.task_done()


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
    logger.info("Completed to stop SSHThreads")
    return True
