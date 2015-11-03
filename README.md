sshpt -- SSH Power Tool
=======================

Dan Mcdougall wrote sshpt(SSH Power Tool) and maintained it.

This repo is a fork of sshpt 1.2.0

Copyright (C) 2011 Dan McDougall.

This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License (GPL) version 3 as published by the Free Software Foundation.

A copy of the GNU GPLv3 should have been distributed with this sofware. If a copy was not provided it may be downloaded at the following URL:

http://www.gnu.org/licenses/gpl-3.0.txt

Details
-------

Detailed information on sshpt as well as the latest version can be found at the following URL:

```
http://code.google.com/p/sshpt/
```

No installation is necessary to use sshpt but Python 2.5+ is required as well as the following Python modules:

```
Paramiko - Pythonic SSH implementation
URL: http://www.lag.net/paramiko/

pycrypto - Python Cryptography Toolkit
URL: http://www.amk.ca/python/code/crypto.html
```

If you want to use sshpt as a module in your Python program a setup.py has been provided:

```bash
sudo python setup.py install
```

Version
-------

## 1.3.7
 - Fixed the bugs on test codes
 - Supports the comments on hostfile using '#'
 - Added the --hosts option to specify a host list on the command line


Usage
-----

```
usage: usage: sshpt [options] "[command1]" "[command2]" ...

positional arguments:
    C                     Commands

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -f <file>, --file <file>
                        Location of the file containing the host list.
  -S, --stdin           Read hosts from standard input
  -k <file>, --key-file <file>
                        Location of the private key file
  -K <password>, --key-pass <password>
                        The password to be used when use the private key
                        file).
  -o <file>, --outfile <file>
                        Location of the file where the results will be saved.
  -a <file>, --authfile <file>
                        Location of the file containing the credentials to be
                        used for connections (format is "username:password").
  -T <int>, --threads <int>
                        Number of threads to spawn for simultaneous connection
                        attempts [default: 10].
  -P <port>, --port <port>
                        The port to be used when connecting. Defaults to 22.
  -u <username>, --username <username>
                        The username to be used when connecting. Defaults to
                        the currently logged-in user.
  -p <password>, --password <password>
                        The password to be used when connecting (not
                        recommended--use an authfile unless the username and
                        password are transient).
  -q, --quiet           Don't print status messages to stdout (only print
                        errors).
  -c <file>, --copy-file <file>
                        Location of the file to copy to and optionally execute
                        (-x) on hosts.
  -d <path>, --dest <path>
                        Path where the file should be copied on the remote
                        host (default: /tmp/).
  -x, --execute         Execute the copied file (just like executing a given
                        command).
  -r, --remove          Remove (clean up) the SFTP'd file after execution.
  -t <seconds>, --timeout <seconds>
                        Timeout (in seconds) before giving up on an SSH
                        connection (default: 30)
  -s, --sudo            Use sudo to execute the command (default: as root).
  -U <username>, --sudouser <username>
                        Run the command (via sudo) as this user.
```
