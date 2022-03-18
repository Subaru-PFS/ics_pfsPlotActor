__author__ = 'alefur'

from PyQt5.QtWidgets import QWidget, QMessageBox
from pfsPlotActor.layout import GridLayout


class CentralWidget(QWidget):
    """Central widget of pfsPlot main window."""

    def __init__(self, pfsPlot):
        QWidget.__init__(self)
        self.pfsPlot = pfsPlot

        grid = GridLayout()
        grid.minimizeContentMargin()
        self.setLayout(grid)

    @property
    def actor(self):
        return self.pfsPlot.actor

    @property
    def isConnected(self):
        return self.pfsPlot.isConnected

    def sendMhsCommand(self, actor, cmdStr, callFunc):
        """Send mhs command."""
        import opscore.actor.keyvar as keyvar
        self.actor.cmdr.bgCall(**dict(actor=actor,
                                      cmdStr=cmdStr,
                                      timeLim=1600,
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
