from Generic import GenericThread

import datetime
import threading
import Queue

class OutputThread(GenericThread):
    """ Genreric -> OutputThread
        This thread is here to prevent SSHThreads from simultaneously writing to the same file and mucking it all up.  Essentially, it allows sshpt to write results to an outfile as they come in instead of all at once when the program is finished.  This also prevents a 'kill -9' from destroying report resuls and also lets you do a 'tail -f <outfile>' to watch results in real-time.

        output_queue: Queue.Queue(): The queue to use for incoming messages.
        verbose - Boolean: Whether or not we should output to stdout.
        outfile - String: Path to the file where we'll store results.
    """
    def __init__(self, output_queue, verbose=True, outfile=None):
        """Name ourselves and assign the variables we were instanciated with."""
        threading.Thread.__init__(self, name="OutputThread")
        self.output_queue = output_queue
        self.verbose = verbose
        self.outfile = outfile
        self.quitting = False

    def printToStdout(self, string):
        """Prints 'string' if self.verbose is set to True"""
        if self.verbose == True:
            print string

    def writeOut(self, queueObj):
        """Write relevant queueObj information to stdout and/or to the outfile (if one is set)"""
        if queueObj['local_filepath']:
            queueObj['commands'] = "sshpt: sftp.put %s %s:%s" % (queueObj['local_filepath'], queueObj['host'], queueObj['remote_filepath'])
        elif queueObj['sudo'] is False:
            if len(queueObj['commands']) > 1: # Only prepend 'index: ' if we were passed more than one command
                queueObj['commands'] = "\n".join(["%s: %s" % (index, command) for index, command in enumerate(queueObj['commands'])])
            else:
                queueObj['commands'] = "".join(queueObj['commands'])
        else:
            if len(queueObj['commands']) > 1: # Only prepend 'index: ' if we were passed more than one command
                queueObj['commands'] = "\n".join(["%s: sudo -u %s %s" % (index, queueObj['run_as'], command) for index, command in enumerate(queueObj['commands'])])
            else:
                queueObj['commands'] = "sudo -u %s %s" % (queueObj['run_as'], "".join(queueObj['commands']))
        if isinstance(queueObj['command_output'], str):
            pass # Since it is a string we'll assume it is already formatted properly
        elif len(queueObj['command_output']) > 1: # Only prepend 'index: ' if we were passed more than one command
            queueObj['command_output'] = "\n".join(["%s: %s" % (index, command) for index, command in enumerate(queueObj['command_output'])])
        else:
            queueObj['command_output'] = "\n".join(queueObj['command_output'])
        csv_out = "\"%s\",\"%s\",\"%s\",\"%s\",\"%s\"" % (queueObj['host'], queueObj['connection_result'], datetime.datetime.now(), queueObj['commands'], queueObj['command_output'])
        self.printToStdout(csv_out)
        if self.outfile is not None:
            csv_out = "%s\n" % csv_out
            output = open(self.outfile, 'a')
            output.write(csv_out)
            output.close()

    def run(self):
        while not self.quitting:
            queueObj = self.output_queue.get()
            if queueObj == "quit":
                self.quit()
            self.writeOut(queueObj)
            self.output_queue.task_done()

def startOutputThread(verbose, outfile):
    """Starts up the OutputThread (which is used by SSHThreads to print/write out results)."""
    output_queue = Queue.Queue()
    output_thread = OutputThread(output_queue, verbose, outfile)
    output_thread.setDaemon(True)
    output_thread.start()
    return output_queue

def stopOutputThread():
    """Shuts down the OutputThread"""
    for t in threading.enumerate():
        if t.getName().startswith('OutputThread'):
            t.quit()
    return True
