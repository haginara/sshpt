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
#import functool
import getpass
if sys.version_info[0] == 2:
    from ConfigParser import SafeConfigParser
else:
    from configparser import SafeConfigParser
from argparse import ArgumentParser
import logging
logging.basicConfig(level=logging.INFO)

from . import version
from .SSHQueue import startSSHQueue
from .SSHQueue import stopSSHQueue
from .OutputThread import startOutputThread
from .OutputThread import stopOutputThread

from .Generic import Password
from .hosts import read_hosts


def create_argument():
    usage = 'usage: sshpt [options] <host> "[command1]" "[command2]" ...'
    parser = ArgumentParser(usage=usage)
    parser.add_argument('-v', '--version', action='version', version=version.__version__)

    parser.add_argument("-f", "--hosts", dest="host_path", default=None,
        help="Location of the file containing the host list."\
        "Specify a host list on the command line. ex)--hosts=host1,host2,host3")
    options, argv = parser.parse_known_args(sys.argv[1:])
    if options.host_path:
        options.host = read_hosts(options.host_path)
    options.target = argv[0]
    options.commands = argv[1:]
    print("Options: {}, argv: {}".format(options, argv))
    return options


def main():
    """Main program function:  Grabs command-line arguments, starts up threads, and runs the program.
    """
    # Grab command line arguments and the command to run (if any)
    options = create_argument()

    output_queue = startOutputThread(options.verbose, options.outfile, options.output_format)
    # Start up the Output and SSH threads
    ssh_connect_queue = startSSHQueue(output_queue, options.max_threads)
    if not options.commands and not options.local_filepath:
        # Assume we're just doing a connection test
        options.commands = ['echo CONNECTION TEST', ]

    for host in options.hosts:
        if ssh_connect_queue.qsize() <= options.max_threads:
            queueObj = dict(
                host=host.get('host'),
                username=host.get('username', options.username),
                password=host.get('password', options.password).password,
                keyfile=options.keyfile, keypass=options.keypass,
                timeout=options.timeout,
                commands=options.commands,
                local_filepath=options.local_filepath, remote_filepath=options.remote_filepath,
                execute=options.execute, remove=options.remove, sudo=options.sudo, port=options.port)
            ssh_connect_queue.put(queueObj)
    
    try:
        # Wait until all jobs are done before exiting
        

        # This wierd little sequence of loops allows us to hit control-C
        # in the middle of program execution and get immediate results
        ssh_connect_queue.join()
        # Just to be safe we wait for the OutputThread to finish before moving on
        output_queue.join()
    except KeyboardInterrupt:
        print ('caught KeyboardInterrupt, exiting...')
        # Return code should be 1 if the user issues a SIGINT (control-C)
        # Clean up
        stopSSHQueue()
        stopOutputThread()
        return 1
    return 0


if __name__ == '__main__':
    main()
