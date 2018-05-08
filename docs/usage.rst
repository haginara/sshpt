Usage
=====

.. code-block:: guess

  usage: usage: sshpt [options] "[command1]" "[command2]" ...

  positional arguments:
    Commands              Commands

  optional arguments:
    -h, --help            show this help message and exit
    -v, --version         show program's version number and exit
    -f HOSTFILE, --file HOSTFILE
                          Location of the file containing the host list.
    -S, --stdin           Read hosts from standard input
    --hosts HOSTS         Specify a host list on the command line.
                          ex)--hosts="host1:host2:host3"
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
    -c <file>, --copy-file <file>
                          Location of the file to copy to and optionally execute
                          (-x) on hosts.
