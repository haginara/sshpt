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

import re
from itertools import cycle
import base64
import threading


### ---- Private Functions ----
def normalizeString(string):
    """Removes/fixes leading/trailing newlines/whitespace and escapes double quotes with double quotes (to comply with CSV format)"""
    string = re.sub(r'(\r\n|\r|\n)', '\n', string) # Convert all newlines to unix newlines
    string = string.strip() # Remove leading/trailing whitespace/blank lines
    srting = re.sub(r'(")', '""', string) # Convert double quotes to double double quotes (e.g. 'foo "bar" blah' becomes 'foo ""bar"" blah')
    return string


class Password(object):
    def __init__(self, s):
        self.password = s

    def __str__(self):
        return self.password

    def __repr__(self):
        return self.__str__()

    @property
    def password(self):
        return Password.decode(self.__password)

    @password.setter
    def password(self, p):
        self.__password = Password.encode(p)

    @staticmethod
    def encode(s, key='sshpt256'):
        enc = [chr((ord(s[i]) + ord(key[i % len(key)])) % 256) for i in range(len(s))]
        enc_str = base64.urlsafe_b64encode("".join(enc))
        return enc_str

    @staticmethod
    def decode(s, key='sshpt256'):
        s = base64.urlsafe_b64decode(s)
        dec = [chr(abs(ord(s[i]) - ord(key[i % len(key)])) % 256) for i in xrange(len(s))]
        return "".join(dec)

class GenericThread(threading.Thread):
    """A baseline thread that includes the functions we want for all our threads so we don't have to duplicate code."""
    def quit(self):
        self.quitting = True
