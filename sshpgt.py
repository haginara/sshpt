#!/usr/bin/env python
"""PyQt4 port of the dialogs/findfiles example from Qt v4.x"""
from PySide import QtCore, QtGui
import logging
import json
import os
import sshpt


class Console(QtGui.QPlainTextEdit):
    __pyqtSignals__ = ("pythonOutput(const QString &)",)

    def __init__(self, parent=None):
        super(Console, self).__init__(parent)

        self.history = []
        self.current = -1

        self.document().setMaximumBlockCount(100)
        p = QtGui.QPalette()
        p.setColor(QtGui.QPalette.Base, QtCore.Qt.black)
        p.setColor(QtGui.QPalette.Text, QtCore.Qt.green)
        self.setPalette(p)

        self.connect(self, QtCore.SIGNAL("returnPressed()"), self.execute)

    def putData(self, data):
        """ InsertData """
        self.insertPlainText(data)

        bar = self.verticalScrollBar()
        bar.setValue(bar.maximum())

    def keyReleaseEvent(self, event):
        if event.type() == QtCore.QEvent.KeyRelease:
            if event.key() == QtCore.Qt.Key_Up:
                current = max(0, self.current - 1)
                if 0 <= current < len(self.history):
                    self.setText(self.history[current])
                    self.current = current
                event.accept()
            elif event.key() == QtCore.Qt.Key_Down:
                current = min(len(self.history), self.current + 1)
                if 0 <= current < len(self.history):
                    self.setText(self.history[current])
                else:
                    self.clear()
                self.current = current

                event.accept()
    def mousePressEvent(self, e):
        self.setFocus()

    def execute(self):
        qApp = QtGui.qApp

        self.expression = self.text()
        try:
            result = str(eval(unicode(self.expression)))

            self.emit(QtCore.SIGNAL("pythonOutput(const QString &)"),
                    QtCore.QString(result))

            self.clear()
            self.history.append(self.expression)
            self.current = len(self.history)
        except:
            pass






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

