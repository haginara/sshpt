from __future__ import print_function

import os
import sys
import logging
import unittest
from unittest import mock
import pytest
import argparse
from subprocess import Popen, PIPE

from os.path import dirname
from os.path import abspath
root_path = dirname(dirname(abspath(__file__)))
sys.path.append(root_path)

from sshpt import version
from sshpt import main

def test_version(capsys):
    with mock.patch('sys.argv', ['sshpt', '-v']):
        with pytest.raises(SystemExit) as exc:
            ret = main.main()
        out, err = capsys.readouterr()
        assert(out.strip() == version.__version__)
        assert(exc.value.code == 0)