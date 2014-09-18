#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       sshpt.py
#
#       Copyright 2011 Dan McDougall <YouKnowWho@YouKnowWhat.com>
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

"""
SSH Power Tool (SSHPT): This script/module will attempt to login (via ssh) to a number of servers in parallel.  It supports multithreading and will perform simultaneous connection attempts to save time (10 by default).  Results are output to stdout unless overrided (see demos).

This module is meant for situations where shared keys are not an option.  If all your hosts are configured with shared keys for passwordless logins you don't need the SSH Power Tool.
"""

from sshpt import *
