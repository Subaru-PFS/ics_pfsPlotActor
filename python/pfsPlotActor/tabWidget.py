__author__ = 'alefur'

import pfsPlotActor.layout as layout
import pfsPlotActor.plotBrowser as plotBrowser
import pfsPlotActor.tabContainer as tabContainer
from PyQt5.QtCore import Qt, QEvent, QTimer, QDateTime
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QSpinBox, QLineEdit, QLabel, QGroupBox, QMessageBox, QTabBar, \
    QTabWidget


class NewTabDialog(QDialog):
    """Dialog to design your plot container."""

    def __init__(self, tabWidget):
        def spinBox(vmin=1, vmax=10):
            widget = QSpinBox()
            widget.setRange(vmin, vmax)
            return widget

        QDialog.__init__(self, tabWidget)
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
        """Call tabWidget.newTab with given title, nRows and nCols."""
        self.parent().newTab(self.title.text(), self.nRows.value(), self.nCols.value())


class EditableTabBar(QTabBar):
    """Just an editable tab title."""

    def __init__(self, parent):
        QTabBar.__init__(self, parent)
        self._editor = QLineEdit(self)
        self._editor.setWindowFlags(Qt.Popup)
        self._editor.setFocusProxy(self)
        self._editor.editingFinished.connect(self.handleEditingFinished)
        self._editor.installEventFilter(self)
        self.setTabsClosable(True)

    def eventFilter(self, widget, event):
        if ((event.type() == QEvent.MouseButtonPress and not self._editor.geometry().contains(event.globalPos())) or (
                event.type() == QEvent.KeyPress and event.key() == Qt.Key_Escape)):
            self._editor.hide()
            return True
        return QTabBar.eventFilter(self, widget, event)

    def mouseDoubleClickEvent(self, event):
        index = self.tabAt(event.pos())
        if index >= 0:
            self.editTab(index)

    def editTab(self, index):
        rect = self.tabRect(index)
        self._editor.setFixedSize(rect.size())
        self._editor.move(self.parent().mapToGlobal(rect.topLeft()))
        self._editor.setText(self.tabText(index))
        if not self._editor.isVisible():
            self._editor.show()

    def handleEditingFinished(self):
        index = self.currentIndex()
        if index >= 0:
            self._editor.hide()
            self.setTabText(index, self._editor.text())


class TabWidget(QTabWidget):
    """Our central Widget, which handle all tabs, how they are created, edited, closed... etc"""

    def __init__(self, pfsPlot):
        self.pfsPlot = pfsPlot
        self.plotBrowserDialog = plotBrowser.PlotBrowserDialog()

        QTabWidget.__init__(self)
        self.setTabsClosable(True)
        self.setTabBar(EditableTabBar(self))
        self.tabCloseRequested.connect(self.closeTab)
        self.currentChanged.connect(self._userChangedTab)

        # doAutoFocus tweak.
        self.autoFocusGracePeriod = 60  # seconds
        self.doAutoFocus = True
        self.pendingFocusQueue = []
        self.lastAutoFocusTime = QDateTime.currentDateTime().addSecs(-9999)
        self.autoFocusTimer = QTimer(self)
        self.autoFocusTimer.setSingleShot(True)
        self.autoFocusTimer.timeout.connect(self._focusNextPendingTab)

    @property
    def actor(self):
        return self.pfsPlot.actor

    @property
    def isConnected(self):
        return self.pfsPlot.isConnected

    def newTabDialog(self):
        """Just create the dialog class."""
        return NewTabDialog(self)

    def newTab(self, title, nRows, nCols):
        """Create a new tabContainer with a given nRows and nCols to receive plotWidget."""
        container = tabContainer.TabContainer(self, nRows, nCols)
        self.addTab(container, title)
        # set the new tab active is what the user usually expect.
        self.setCurrentWidget(container)

    def closeTab(self, index):
        """Close tab callback/"""
        reply = QMessageBox.question(self, 'Message', 'Are you sure to close this window?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.removeTab(index)

    def _userChangedTab(self):
        """Tab was changed manually — reset autofocus timer and clean pending queue."""
        currentTab = self.currentWidget()
        self.lastAutoFocusTime = QDateTime.currentDateTime()

        # Remove current tab if it was waiting in the queue
        if currentTab in self.pendingFocusQueue:
            self.pendingFocusQueue.remove(currentTab)

        if not self.pendingFocusQueue:
            self.autoFocusTimer.stop()

    def setEnabled(self, a0: bool) -> None:
        """Set widget and all children widgets enabled/disabled."""
        for index in range(self.count()):
            self.widget(index).setEnabled(a0)

    def showError(self, title, error):
        reply = QMessageBox.critical(self, title, error, QMessageBox.Ok)

    def setAutofocus(self, state):
        self.doAutoFocus = state

    def newPlotAvailable(self, tabContainer):
        if not self.doAutoFocus:
            return

        now = QDateTime.currentDateTime()
        delta = self.lastAutoFocusTime.secsTo(now)

        if delta > self.autoFocusGracePeriod:
            self.setCurrentWidget(tabContainer)
            self.lastAutoFocusTime = now
        else:
            if tabContainer not in self.pendingFocusQueue:
                self.pendingFocusQueue.append(tabContainer)

            if not self.autoFocusTimer.isActive():
                self.autoFocusTimer.start((self.autoFocusGracePeriod - delta) * 1000)  # in ms

    def _focusNextPendingTab(self):
        if self.pendingFocusQueue:
            nextTab = self.pendingFocusQueue.pop(0)
            self.setCurrentWidget(nextTab)
            self.lastAutoFocusTime = QDateTime.currentDateTime()

        # If more tabs are still pending, restart the timer
        if self.pendingFocusQueue:
            self.autoFocusTimer.start(self.autoFocusGracePeriod * 1000)

    def setAutoFocusGracePeriod(self, seconds):
        self.autoFocusGracePeriod = seconds
