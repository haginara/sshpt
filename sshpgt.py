#!/usr/bin/env python
"""PyQt4 port of the dialogs/findfiles example from Qt v4.x"""
from PySide import QtCore, QtGui
import logging
import json
import os
import sshpt


class Console(QtGui.QPlainTextEdit):
    def __init__(self, parent=None):
        super(Console, self).__init__(parent)

        localEchoEnable=False

        self.document().setMaximumBlockCount(100)
        p = QtGui.QPalette()
        p.setColor(QtGui.QPalette.Base, QtCore.Qt.black)
        p.setColor(QtGui.QPalette.Text, QtCore.Qt.green)
        self.setPalette(p)


class Window(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)

        console = Console()
        #console.setEnabled(False)
        self.setCentralWidget(console)
        
        self.setWindowTitle("SSH Power GUI Tool")
        self.resize(700, 500)
    
if __name__ == '__main__':
    import sys
    logging.basicConfig(format="%(asctime)-15s %(module)s %(levelname)s %(message)s", level=logging.DEBUG)
    logging.info("Start nsmon-dialog")

    app = QtGui.QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())

