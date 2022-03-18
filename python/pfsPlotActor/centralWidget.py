__author__ = 'alefur'

from PyQt5.QtWidgets import QWidget, QMessageBox
from pfsPlotActor.layout import GridLayout


class CentralWidget(QWidget):
    def __init__(self, mainWindow):
        QWidget.__init__(self)
        self.mainWindow = mainWindow

        self.mainLayout = GridLayout()
        self.mainLayout.setSpacing(1)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(self.mainLayout)

    @property
    def actor(self):
        return self.pfsGUI.actor

    @property
    def isConnected(self):
        return self.pfsGUI.isConnected

    def sendCommand(self, actor, cmdStr, callFunc):
        import opscore.actor.keyvar as keyvar
        self.actor.cmdr.bgCall(**dict(actor=actor,
                                      cmdStr=cmdStr,
                                      timeLim=1600,
                                      callFunc=callFunc,
                                      callCodes=keyvar.AllCodes))

    def heartBeat(self):
        self.tronLayout.tronStatus.dial.heartBeat()

    def showError(self, title, error):
        reply = QMessageBox.critical(self, title, error, QMessageBox.Ok)

    def setEnabled(self, a0: bool) -> None:
        widgets = [self.mainLayout.itemAt(i).widget() for i in range(self.mainLayout.count())]

        for widget in widgets:
            widget.setEnabled(a0)
