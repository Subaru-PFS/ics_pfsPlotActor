__author__ = 'alefur'

from PyQt5.QtWidgets import QMainWindow, QAction, QDialog, QDialogButtonBox, QVBoxLayout, QLabel, QSpinBox

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
            self.configMenu = self.menuBar().addMenu('&Configuration')
            self.helpMenu = self.menuBar().addMenu('&?')

        def setActions():
            addTab = QAction('Add Tab', self)
            addTab.triggered.connect(self.centralWidget().newTabDialog)
            self.windowMenu.addAction(addTab)

            setAutofocus = QAction('Set Autofocus', self)
            setAutofocus.setCheckable(True)  # make it a checkbox-style toggle
            setAutofocus.setChecked(False)  # default unchecked (optional)
            setAutofocus.toggled.connect(self.centralWidget().setAutofocus)
            self.configMenu.addAction(setAutofocus)

            setGrace = QAction('Set AutoFocus Grace Period…', self)
            setGrace.triggered.connect(self.showSetGraceDialog)
            self.configMenu.addAction(setGrace)

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

    def showSetGraceDialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Set AutoFocus Grace Period")

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Auto-focus delay (seconds):"))

        spinBox = QSpinBox()
        spinBox.setRange(5, 600)
        spinBox.setValue(self.centralWidget().autoFocusGracePeriod)
        layout.addWidget(spinBox)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(buttons)

        dlg.setLayout(layout)

        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)

        if dlg.exec_():
            self.centralWidget().setAutoFocusGracePeriod(spinBox.value())
