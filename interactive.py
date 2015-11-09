# -*- coding: utf-8 -*-
# ####################################################################
#
#  Jan. 2010 created by Juergen Thies (juspertor UG)
#  email: juergen.thies@juspertor.com
#  This file may free use used, copied, modified or published.
#  It can also be use under any open source license like GPL, ...
#
#####################################################################

# The pylayout software, which is called pylayout_current here, is distributed with versions of PyQt4 and sip. It
# seems to need these exact versions to run. This module is a template that can be executed from a project
# directory and modified to speed design. See README.md for instructions on getting the imports below to work correctly.
import sys
import IPython
import pylayout_current
sys.path.insert(0, pylayout_current.__path__[0])
from PyQt4 import QtCore, QtGui
from pylayout_current import pylayout

global pyLayoutNewWin
pyLayoutNewWin = {}


class layoutWindow(QtCore.QObject):

    def __init__(self, windowType):
        QtCore.QObject.__init__(self)
        self.layoutClose = True
        self.schematicClose = True
        self.textClose = True
        if windowType == "schematic":
            self.openSchematic()
        elif windowType == "text":
            self.openText()
        else:
            self.openLayout(windowType)

    def openLayout(self, windowType):
        if self.layoutClose == False:
            return
        if windowType == "layoutBasic":
            pylayout.project.defaultGui = False
        elif windowType == "layoutReduced":
            pylayout.project.defaultGui = False
        elif windowType == "layoutPure":
            pylayout.project.defaultGui = False
        if self.schematicClose == False:
            self.l = pylayout.project.getLayout(self.s)
        else:
            self.l = pylayout.project.newLayout()
        self.layoutClose = False
        self.l.closed.connect(self.layoutClosed)
        self.l.executePython.connect(self.pythonMacro, QtCore.Qt.DirectConnection)
        if windowType == "layoutBasic":
            self.l.guiSetupBasic()
        elif windowType == "layoutReduced":
            self.l.guiSetupReduced()
        elif windowType == "layoutPure":
            self.l.addMouseHelp()
        pylayout.project.defaultGui = True

    def layoutClosed(self):
        self.layoutClose = True

    def openSchematic(self):
        if self.schematicClose == False:
            return
        if self.layoutClose == False:
            self.s = pylayout.project.getSchematic(self.l)
        else:
            self.s = pylayout.project.newSchematic()
        self.schematicClose = False
        self.s.closed.connect(self.schematicClosed)
        self.s.executePython.connect(self.pythonMacro, QtCore.Qt.DirectConnection)

    def schematicClosed(self):
        self.schematicClose = True

    def textClosed(self):
        self.textClose = True

    def openText(self):
        if self.textClose == False:
            return
        self.t = pylayout.textEdit()
        self.textClose = False
        setupText(self.t)
        #self.t.closed.connect(self.textClosed)
        #self.t.executePython.connect(self.pythonMacro,QtCore.Qt.DirectConnection)

    def linkedSchematic(self):
        self.openSchematic()
        self.s.show()

    def linkedLayout(self):
        self.openLayout("layoutFull")
        self.l.show()

    #executor for python macros
    def pythonMacro(self, code):
        if self.layoutClose == False:
            layout = self.l
        if self.schematicClose == False:
            schematic = self.s
        if self.textClose == False:
            text = self.t
        try:
            exec ( code.toAscii().data() )
        except:
            self.openLayout("")
            error = sys.exc_info().__str__()
            self.l.showMessage("Python Error:", error)


def main():
    from layouteditor import interface
    app = QtGui.QApplication(sys.argv)
    app.quitOnLastWindowClosed = True
    pixmap = QtGui.QPixmap(":/splash")
    splashscreen = pylayout.splash(pixmap)
    splashscreen.show()

    win = layoutWindow("layoutFull")
    layout = win.l
    splashscreen.finish(layout)
    layout.show()

    # Create a Drawing object
    drawing = interface.Drawing(layout.drawing)

    # Create a clean scope.
    def clean_execfile(filename):
        execfile(filename, {'layout': layout})

    def show_latest():
        layout.drawing.currentCell = layout.drawing.firstCell.thisCell
        layout.guiUpdate()
        layout.drawing.scaleFull()

    # The next line prevents the function from exiting until the IPython session is ended, so exec_() is unnecessary and
    # actually will cause the IPython session to hang if it is closed before the window is closed.
    IPython.embed()


if __name__ == '__main__':
    main()
