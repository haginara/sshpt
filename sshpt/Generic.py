import re
import threading
import logging

### ---- Private Functions ----
def normalizeString(string):
    """Removes/fixes leading/trailing newlines/whitespace and escapes double quotes with double quotes (to comply with CSV format)"""
    string = re.sub(r'(\r\n|\r|\n)', '\n', string) # Convert all newlines to unix newlines
    string = string.strip() # Remove leading/trailing whitespace/blank lines
    srting = re.sub(r'(")', '""', string) # Convert double quotes to double double quotes (e.g. 'foo "bar" blah' becomes 'foo ""bar"" blah')
    return string



class GenericThread(threading.Thread):
    """A baseline thread that includes the functions we want for all our threads so we don't have to duplicate code."""
    def quit(self):
        self.quitting = True
