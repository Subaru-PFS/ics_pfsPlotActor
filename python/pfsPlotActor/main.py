__author__ = 'alefur'

import argparse
import os
import pwd
import sys

from PyQt5.QtWidgets import QApplication, QMainWindow, QAction
from pfsPlotActor.centralWidget import CentralWidget





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
        # construct your main canvas
        self.constructMainCanvas()
        #
        self.show()
        self.move(self.screenWidth * 0.5, self.screenHeight * 0.5)
        self.resize(self.screenWidth * 0.2, self.screenHeight * 0.2)
        self.setConnected(False)

    def constructMainCanvas(self):
        """Construct your main canvas."""

        def setMenu():
            self.windowMenu = self.menuBar().addMenu('&Windows')
            self.helpMenu = self.menuBar().addMenu('&?')

        def setActions():
            addTab = QAction('add Tab', self)
            addTab.triggered.connect(self.centralWidget().newTabDialog)
            self.windowMenu.addAction(addTab)

        self.setCentralWidget(CentralWidget(self))
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', default=pwd.getpwuid(os.getuid()).pw_name, type=str, nargs='?', help='cmdr name')
    parser.add_argument('--fontsize', default=8, type=int, nargs='?', help='application font size')
    args = parser.parse_args()

    app = QApplication(sys.argv)
    screen = app.desktop().screenGeometry()

    # setting user fontsize for Qt
    font = app.font()
    font.setPointSize(args.fontsize)
    app.setFont(font)

    # setting user fontsize for matplotlib
    import matplotlib
    matplotlib.rcParams.update({'font.size': args.fontsize})

    import qt5reactor
    qt5reactor.install()
    from twisted.internet import reactor

    import miniActor
    actor = miniActor.connectActor(['hub'])

    try:
        ex = PfsPlot(reactor, actor, args.name, screen)
    except:
        actor.disconnectActor()
        raise

    reactor.run()
    actor.disconnectActor()


if __name__ == "__main__":
    main()
