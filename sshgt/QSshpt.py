#!/usr/bin/python
"""PyQt4 port of the richtext/syntaxhighlighter example from Qt v4.x"""
from PySide import QtCore, QtGui
import os, sys

__version__ = "0.1"

class MainWindow(QtGui.QMainWindow):
    MaxRecentFiles = 5
    windowList = []
    filetype = None

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        
        mainWidget = self.setUI()
        self.setCentralWidget(mainWidget)
        self.setWindowTitle("LoCo Viewer")

    def setUI(self):
        """ """
        main_widget = QtGui.QWidget()

        model = QtGui.QFileSystemModel()
        model.setRootPath(QtCore.QDir.currentPath())
        tree = QtGui.QTreeView()
        tree.setModel(model)
        tree.setRootIndex(model.index(QtCore.QDir.currentPath()))

        layout = QtGui.QHBoxLayout()
        layout.addWidget(tree)

        main_widget.setLayout(layout)

        return main_widget


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    window.resize(700, 512)
    window.show()
    sys.exit(app.exec_())

