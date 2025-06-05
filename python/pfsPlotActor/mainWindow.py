__author__ = 'alefur'

import os

import yaml
from PyQt5.QtWidgets import QMainWindow, QAction, QDialog, QDialogButtonBox, QVBoxLayout, QLabel, QSpinBox, QFileDialog
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

        autoTabFocusDefault = self.actor.actorConfig.get('setAutoTabFocus', False)
        autoTabDelayDefault = self.actor.actorConfig.get('setAutoTabDelay', 30)

        def setMenu():
            self.windowMenu = self.menuBar().addMenu('&Windows')
            self.configMenu = self.menuBar().addMenu('&Configuration')
            self.helpMenu = self.menuBar().addMenu('&?')

        def setActions():
            addTabAction = QAction('Add Tab', self)
            addTabAction.triggered.connect(self.centralWidget().newTabDialog)
            self.windowMenu.addAction(addTabAction)

            clearTabsAction = QAction('Clear All Tabs', self)
            clearTabsAction.triggered.connect(self.clearAllTabs)
            self.windowMenu.addAction(clearTabsAction)

            loadLayoutAction = QAction('Load Layout', self)
            loadLayoutAction.triggered.connect(self.loadLayoutFromFile)
            self.windowMenu.addAction(loadLayoutAction)

            saveLayoutAction = QAction('Save Layout', self)
            saveLayoutAction.triggered.connect(self.saveLayoutToFile)
            self.windowMenu.addAction(saveLayoutAction)

            setAutoTabFocusAction = QAction('Set Auto-Tab Focus', self)
            setAutoTabFocusAction.setCheckable(True)
            setAutoTabFocusAction.setChecked(autoTabFocusDefault)
            self.centralWidget().autoTabFocus = autoTabFocusDefault
            self.centralWidget().autoTabDelay = autoTabDelayDefault
            setAutoTabFocusAction.toggled.connect(self.centralWidget().setAutoTabFocus)
            self.configMenu.addAction(setAutoTabFocusAction)

            setAutoTabDelayAction = QAction('Set Auto-Tab Delay', self)
            setAutoTabDelayAction.triggered.connect(self.setAutoTabDelay)
            self.configMenu.addAction(setAutoTabDelayAction)

        # our centralWidget is actually a TabWidget.
        self.setCentralWidget(TabWidget(self))
        setMenu()
        setActions()

        # adding label for Auto-Tab focus and connect signal.
        self.autoTabFocusStatus = QLabel()
        self.updateAutoTabFocusStatus(autoTabFocusDefault)
        self.statusBar().addPermanentWidget(self.autoTabFocusStatus)
        self.centralWidget().autoTabFocusChanged.connect(self.updateAutoTabFocusStatus)

        self.statusBar().showMessage('ready')  # initial status
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

    def setAutoTabDelay(self):
        """Open a dialog to set the delay for Auto-Tab Focus."""
        dlg = QDialog(self)
        dlg.setWindowTitle("Auto-Tab Config")

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Set Auto-Tab delay (seconds):"))

        spinBox = QSpinBox()
        spinBox.setRange(5, 600)
        spinBox.setValue(self.centralWidget().autoTabDelay)
        layout.addWidget(spinBox)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(buttons)

        dlg.setLayout(layout)

        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)

        if dlg.exec_():
            self.centralWidget().setAutoTabDelay(spinBox.value())

    def updateAutoTabFocusStatus(self, isOn):
        """Update the Auto-Tab Focus status label's text and style based on state."""
        if isOn:
            self.autoTabFocusStatus.setText("Auto-Tab Focus: ON")
            self.autoTabFocusStatus.setStyleSheet("color: green; font-weight: bold; font-size: 11pt;")
        else:
            self.autoTabFocusStatus.setText("Auto-Tab Focus: OFF")
            self.autoTabFocusStatus.setStyleSheet("color: red; font-weight: bold; font-size: 11pt;")

    def clearAllTabs(self):
        """Clear all open tabs in the TabWidget."""
        self.centralWidget().clear()
        self.statusBar().showMessage("all tabs cleared", 5000)

    def loadLayoutFromFile(self):
        """Open a file dialog to load a YAML file and restore the layout."""
        homeDir = os.path.expanduser('~')
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(
            self,
            "Load Layout YAML",
            homeDir,
            "YAML Files (*.yaml *.yml);;All Files (*)",
            options=options
        )
        if not fileName:
            return  # User canceled

        try:
            with open(fileName, 'r') as f:
                layout = yaml.safe_load(f)
        except Exception as e:
            self.centralWidget().showError("Load Layout Error", f"Failed to load layout:\n{e}")
            return

        # Let the TabWidget load the layout
        try:
            self.centralWidget().loadLayout(layout)
            self.statusBar().showMessage(f"layout loaded from: {fileName}", 5000)
        except Exception as e:
            self.centralWidget().showError("Load Layout Error", f"Failed to apply layout:\n{e}")

    def saveLayoutToFile(self):
        """Open a file dialog to save the current tab layout as a YAML file, and show a status bar message."""
        homeDir = os.path.expanduser('~')
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(
            self,
            "Save Layout as YAML",
            homeDir,
            "YAML Files (*.yaml *.yml);;All Files (*)",
            options=options
        )
        if not fileName:
            return  # User canceled

        if not fileName.lower().endswith(('.yaml', '.yml')):
            fileName += '.yaml'

        layout = self.centralWidget().saveLayout()

        with open(fileName, 'w') as f:
            yaml.dump(layout, f, default_flow_style=False)

        # Show transient message in the status bar for 5 seconds
        self.statusBar().showMessage(f"layout saved to: {fileName}", 5000)
