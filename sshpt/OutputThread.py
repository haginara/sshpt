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

from __future__ import print_function
from .Generic import GenericThread

import sys
import pprint
import json
import datetime
import threading
if sys.version_info[0] == 3:
    import queue as Queue
else:
    import Queue

import logging
logger = logging.getLogger(__name__)


class OutputThread(GenericThread):
    """
    Genreric -> OutputThread
    This thread is here to prevent SSHThreads from simultaneously writing to the same file and mucking it all up.
    Essentially, it allows sshpt to write results to an outfile as they come in instead of all at once when the program is finished.
    This also prevents a 'kill -9' from destroying report resuls and also lets you do a 'tail -f <outfile>' to watch results in real-time.

    output_queue: Queue.Queue(): The queue to use for incoming messages.
    verbose - Boolean: Whether or not we should output to stdout.
    outfile - String: Path to the file where we'll store results.
    """
    def __init__(self, output_queue, verbose=True, outfile=None, output_format='csv'):
        """Name ourselves and assign the variables we were instanciated with."""
        super(OutputThread, self).__init__(name="OutputThread")
        self.output_queue = output_queue
        self.verbose = verbose
        self.outfile = outfile
        self.quitting = False
        self.output_format = output_format

    def printToStdout(self, output):
        """Prints output if self.verbose is set to True"""
        if self.verbose is True:
            if self.output_format == 'csv':
                print(output)
            elif self.output_format == 'json':
                pprint.pprint(output, width=100)
                output = json.dumps(output)

        if self.outfile:
            with open(self.outfile, 'a') as f:
                f.write("%s\n" % output)

    def writeOut(self, queueObj):
        """Write relevant queueObj information to stdout and/or to the outfile (if one is set)"""
        if queueObj['local_filepath']:
            queueObj['commands'] = "sshpt: sftp.put %s %s:%s" % (queueObj['local_filepath'], queueObj['host'], queueObj['remote_filepath'])
        elif queueObj['sudo'] is False:
            if len(queueObj['commands']) > 1:
                # Only prepend 'index: ' if we were passed more than one command
                queueObj['commands'] = "\n".join(["%s: %s" % (index, command) for index, command in enumerate(queueObj['commands'])])
            else:
                queueObj['commands'] = "".join(queueObj['commands'])
        else:
            if len(queueObj['commands']) > 1:
                # Only prepend 'index: ' if we were passed more than one command
                queueObj['commands'] = "\n".join(["%s: sudo -u %s %s" % (index, queueObj['sudo'], command) for index, command in enumerate(queueObj['commands'])])
            else:
                queueObj['commands'] = "sudo -u %s %s" % (queueObj['sudo'], "".join(queueObj['commands']))
        if isinstance(queueObj['command_output'], str):
            # Since it is a string we'll assume it is already formatted properly
            pass
        elif len(queueObj['command_output']) > 1:
            # Only prepend 'index: ' if we were passed more than one command
            queueObj['command_output'] = "\n".join(["%s: %s" % (index, command) for index, command in enumerate(queueObj['command_output'])])
        else:
            queueObj['command_output'] = "\n".join(queueObj['command_output'])
        if self.output_format == 'csv':
            output = "\"%s\",\"%s\",\"%s\",\"%s\",\"%s\"" % (queueObj['host'], queueObj['connection_result'], datetime.datetime.now(), queueObj['commands'], queueObj['command_output'])
        elif self.output_format == 'json':
            output = {'host': queueObj['host'], 'connection_result': queueObj['connection_result'], 'timestamp': str(datetime.datetime.now()), 'commands': queueObj['commands'], 'command_output': queueObj['command_output']}

        self.printToStdout(output)

    def run(self):
        while not self.quitting:
            queueObj = self.output_queue.get()
            if queueObj == "quit":
                self.quit()
                break
            self.writeOut(queueObj)
            self.output_queue.task_done()
        logger.info("Completed to run OutputThread: %d", self.output_queue.qsize())


def startOutputThread(verbose, outfile, output_format):
    """
    Starts up the OutputThread (which is used by SSHThreads to print/write out results).
    """
    output_queue = Queue.Queue()
    output_thread = OutputThread(output_queue, verbose, outfile, output_format)
    output_thread.setDaemon(True)
    output_thread.start()
    return output_queue


def stopOutputThread():
    """
    Shuts down the OutputThread
    """
    for t in threading.enumerate():
        if t.getName().startswith('OutputThread'):
            t.quit()
    return True
