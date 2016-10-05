from __future__ import print_function

import os
import sys
import logging
from os.path import dirname
from os.path import abspath
root_path = dirname(dirname(abspath(__file__)))
sys.path.append(root_path)

logging.basicConfig(level=logging.DEBUG)

if __name__ == '__main__':
    from sshpt import main
    main.main()
