#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This script is demonstrates how to import and use the SSH Power Tool (sshpt) in a Python program.
"""

# Import some basic built-in modules
import getpass
import Queue

# Import the module du jour
import sshpt

# Obtain the basic information necessary to use sshpt
hostlist = raw_input('Host(s) (use spaces for multiple): ').split(' ')
username = raw_input('Username: ')
password = getpass.getpass('Password: ')
command = raw_input('Command: ')
# 'commands' has to be a list
commands = [command, ]


# Give ourselves an output queue to store results
results_queue = Queue.Queue()

ssh = sshpt.SSHPowerTool(
    hosts=hostlist, username=username, password=password,
    commands=commands, output_queue=results_queue)
ssh.run()

# This is the simplest way of grabbing the data that sshpt returns.  The other way would be to write your own version of the OutputThread
for host in results_queue.queue:
    print "host: %s" % host['host']
    print "command_output: %s" % host['command_output']
    print "commands: %s" % host['commands']
    # ...and here's the rest of what you can use
    #print "username: %s" % host['username']
    #print "password: %s" % host['password'] # Do you REALLY this output to the console?
    #print "timeout: %s" % host['timeout']
    #print "local_filepath: %s" % host['local_filepath']
    #print "remote_filepath: %s" % host['remote_filepath']
    #print "execute: %s" % host['execute']
    #print "remove: %s" % host['remove']
    #print "sudo: %s" % host['sudo']
    #print "run_as: %s" % host['run_as']
    #print "port: %s" % host['port']
    print
