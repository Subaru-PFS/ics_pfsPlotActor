__author__ = 'alefur'

from PyQt5.QtWidgets import QMainWindow, QAction
from pfsPlotActor.tabWidget import TabWidget


class PfsPlot(QMainWindow):
    """ PfsPlot QT5 mainWindow. """

    def __init__(self, reactor, actor, cmdrName, screen):
        QMainWindow.__init__(self)
        self.reactor = reactor
        self.actor = actor
        self.actor.connectionMade = self.connectionMade
        self.isConnected = False
        self.cmdrName = f'PfsPlotActor.{cmdrName}'
        self.screenWidth = screen.width()
        self.screenHeight = screen.height()
        # construct your main canvas.
        self.constructMainCanvas()
        # show, move and resize.
        self.show()
        self.move(int(round(self.screenWidth * 0.5)), int(round(self.screenHeight * 0.5)))
        self.resize(int(round(self.screenWidth * 0.2)), int(round(self.screenHeight * 0.2)))
        self.setConnected(False)

    def constructMainCanvas(self):
        """Construct your main canvas."""

        def setMenu():
            self.windowMenu = self.menuBar().addMenu('&Windows')
            self.helpMenu = self.menuBar().addMenu('&?')

        def setActions():
            addTab = QAction('Add tab', self)
            addTab.triggered.connect(self.centralWidget().newTabDialog)
            self.windowMenu.addAction(addTab)

        # our centralWidget is actually a TabWidget.
        self.setCentralWidget(TabWidget(self))
        setMenu()
        setActions()
        self.setWindowTitle(self.cmdrName)

    def setConnected(self, isConnected):
        """ activate main widget """
        self.isConnected = isConnected
        self.centralWidget().setEnabled(isConnected)

    def connectionMade(self):
        """ Connection made to the hub."""
        self.setConnected(True)
        self.actor.cmdr.connectionLost = self.connectionLost

    def connectionLost(self, reason):
        """Connection lost from the hub. display useful information to the user."""
        self.setConnected(False)
        if not self.actor.shuttingDown:
            self.centralWidget().showError("Connection Lost", f"Connection to tron has failed : \n{reason}")

    def closeEvent(self, QCloseEvent):
        """Catch close event and disconnect from the hub."""
        self.actor.disconnectActor()
        self.reactor.callFromThread(self.reactor.stop)
        QCloseEvent.accept()
