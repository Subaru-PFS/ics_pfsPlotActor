__author__ = 'alefur'

import pfsPlotActor.layout as layout
from PyQt5.QtWidgets import QWidget, QMessageBox, QDialog, QDialogButtonBox, QSpinBox, QLineEdit, QLabel, QGroupBox
from pfsPlotActor.layout import GridLayout
from pfsPlotActor.tabwidget import TabWidget


class NewTabDialog(QDialog):
    def __init__(self, centralWidget):
        def spinBox(vmin=1, vmax=10):
            widget = QSpinBox()
            widget.setRange(vmin, vmax)
            return widget

        QDialog.__init__(self, centralWidget)
        self.setLayout(layout.VBoxLayout())

        gb = QGroupBox()
        gb.setTitle('Layout Definition')

        grid = layout.GridLayout()
        grid.setContentsMargins(1, 4, 1, 1)
        gb.setLayout(grid)

        self.nRows = spinBox()
        self.nCols = spinBox()
        self.title = QLineEdit('Untitled')

        grid.addWidget(QLabel('nRows'), 0, 0)
        grid.addWidget(self.nRows, 0, 1)

        grid.addWidget(QLabel('nColumns'), 1, 0)
        grid.addWidget(self.nCols, 1, 1)

        grid.addWidget(self.title, 2, 1)
        grid.addWidget(QLabel('Title'), 2, 0)

        self.layout().addWidget(gb)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Apply | QDialogButtonBox.Close)
        buttonBox.button(QDialogButtonBox.Apply).clicked.connect(self.apply)
        buttonBox.button(QDialogButtonBox.Close).clicked.connect(self.close)
        self.layout().addWidget(buttonBox)

        self.setWindowTitle('Add New Tab')

        self.setVisible(True)

    def apply(self):
        self.parent().tabWidget.newTab(self.title.text(), self.nRows.value(), self.nCols.value())


class CentralWidget(QWidget):
    """Central widget of pfsPlot main window."""

    def __init__(self, pfsPlot):
        QWidget.__init__(self)
        self.pfsPlot = pfsPlot

        grid = GridLayout()
        grid.minimizeContentMargin()

        self.tabWidget = TabWidget(self)
        grid.addWidget(self.tabWidget)
        self.setLayout(grid)

        # wid = QWidget()
        # wid.setLayout(VBoxLayout())

        # for cam in ['b1', 'r1']:
        #     w1 = MplWidget()
        #     camOs = ccdOverscan.CcdOverscan(w1.canvas, cam)
        #     # adding callbacks
        #     self.actor.requireModels([camOs.actor])
        #     self.actor.models[camOs.actor].keyVarDict[camOs.key].addCallback(camOs.update)
        #     wid.layout().addWidget(w1)
        #
        # self.tabWidget.addTab(wid, 'CCD Overscan')

    @property
    def actor(self):
        return self.pfsPlot.actor

    @property
    def isConnected(self):
        return self.pfsPlot.isConnected

    def newTabDialog(self):
        """ """
        return NewTabDialog(self)

    def sendMhsCommand(self, actor, cmdStr, callFunc, timeLim=120):
        """Send mhs command."""
        import opscore.actor.keyvar as keyvar
        self.actor.cmdr.bgCall(**dict(actor=actor,
                                      cmdStr=cmdStr,
                                      timeLim=timeLim,
                                      callFunc=callFunc,
                                      callCodes=keyvar.AllCodes))

    def showError(self, title, error):
        """Show error message."""
        return QMessageBox.critical(self, title, error, QMessageBox.Ok)

    def setEnabled(self, a0: bool) -> None:
        """Set widget and all children widgets enabled/disabled."""
        widgets = [self.layout().itemAt(i).widget() for i in range(self.layout().count())]

        for widget in widgets:
            widget.setEnabled(a0)
