#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SSHPT CherryPy Example - Demonstrates how to use sshpt with cherrypy to execute commands via a web page.
"""
import sys
try:
    import cherrypy
except ImportError:
    print("Install cheryypy first")
    sys.exit(2)
import Queue
import sshpt


class SSHPTClass(object):
    """Setup a basic CherryPy web page where the user can select from a pre-defined list of servers to run commands on"""
    def __init__(self):
        """This example includes a pre-defined hostlist.  You could grab yours from a file/DB or just have the user enter them in by hand."""
        self.hostlist = ['10.8.248.25', '10.8.248.19', '10.8.248.7', '10.8.248.21']

    def index(self):
        """The index page - The user selects the hosts to run commands on, enters their credentials, and provides a command to run."""
        page = "<html><head><title>SSHPT Via Web Example</title></head><body>"
        page += """
        <form action="doSSHPT" method="post">
            <p>Select Hosts</p>
            <select name="hosts" multiple="yes" size="4">"""
        for host in self.hostlist:
            page += "<option>%s</option>" % host
        page += """
            </select><table border='0'>
            <tr><td>Username:</td>
            <td><input type="text" name="username" value="" size="15" maxlength="40"/></td></tr>
            <tr><td>Password:</td>
            <td><input type="password" name="password" value="" size="15" maxlength="40"/></td></tr>
            <tr><td>Command to run</td>
            <td><input type="text" name="command" value="" size="15" maxlength="100"/></td></tr></table>
            <p><input type="submit" value="Login"/>
            <input type="reset" value="Clear"/></p>
        </form></body></html>"""
        return page

    def doSSHPT(self, hosts, username, password, command):
        """The results page"""
        # Give ourselves an output queue to save results into
        results_queue = Queue.Queue()
        commands = [command, ] # Has to be a list
        ssh = sshpt.SSHPowerTool(
            hosts=hosts, username=username, password=password,
            commands=commands, output_queue=results_queue)
        ssh.run()
        page = "<html><head><title>SSHPT Via Web Example</title></head><body>"
        # Print a table header
        page += "<table border='1'><tr><td><b>Host</b></td><td><b>Command</b></td><td><b>Command Output</b></td></tr>"
        for host in results_queue.queue:
            page += "<tr>"
            page += "<td>%s</td>" % host['host']
            page += "<td>%s</td>" % "".join(host['commands'])
            page += "<td><pre>%s</pre></td>" % "".join(host['command_output'])
            page += "</tr>"

        page += "</table>"
        page += "</body></html>"
        return page

    index.exposed = True
    doSSHPT.exposed = True

cherrypy.quickstart(SSHPTClass())
