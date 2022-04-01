__author__ = 'alefur'

from PyQt5.QtWidgets import QWidget, QMessageBox
from pfsPlotActor.examples import ccdOverscan
from pfsPlotActor.layout import GridLayout, VBoxLayout
from pfsPlotActor.mplCanvas import MplWidget
from pfsPlotActor.tabwidget import TabWidget


class CentralWidget(QWidget):
    """Central widget of pfsPlot main window."""

    def __init__(self, pfsPlot):
        QWidget.__init__(self)
        self.pfsPlot = pfsPlot

        grid = GridLayout()
        grid.minimizeContentMargin()

        self.tabWidget = TabWidget(self)
        grid.addWidget(self.tabWidget)

        wid = QWidget()
        wid.setLayout(VBoxLayout())

        for cam in ['b1', 'r1']:
            w1 = MplWidget()
            camOs = ccdOverscan.CcdOverscan(w1.canvas, cam)
            # adding callbacks
            self.actor.requireModels([camOs.actor])
            self.actor.models[camOs.actor].keyVarDict[camOs.key].addCallback(camOs.update)
            wid.layout().addWidget(w1)

        self.tabWidget.addTab(wid, 'CCD Overscan')

        self.setLayout(grid)

    @property
    def actor(self):
        return self.pfsPlot.actor

    @property
    def isConnected(self):
        return self.pfsPlot.isConnected

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
