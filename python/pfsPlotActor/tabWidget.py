__author__ = 'alefur'

import pfsPlotActor.layout as layout
import pfsPlotActor.misc as misc
import pfsPlotActor.mplCanvas as mplCanvas
import pfsPlotActor.plotBrowser as plotBrowser
import pfsPlotActor.tabContainer as tabContainer
from PyQt5.QtCore import Qt, QEvent, QTimer, QDateTime
from PyQt5.QtGui import QIcon
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
        super().__init__(parent)
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
        return super().eventFilter(widget, event)

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
    """Main tab widget managing tab layout and auto-focus logic."""

    def __init__(self, pfsPlot):
        super().__init__()
        self.pfsPlot = pfsPlot
        self.plotBrowserDialog = plotBrowser.PlotBrowserDialog(pfsPlot)

        self.setTabsClosable(True)
        self.setTabBar(EditableTabBar(self))
        self.tabCloseRequested.connect(self.closeTab)
        self.currentChanged.connect(self._currentTabChanged)

        # setting event filter tracking user activities.
        self.installEventFilter(self)

        self.iconInfo = misc.Icon('information')

        # doAutoFocus tweak.
        self.autoFocusGracePeriod = 30  # seconds
        self.doAutoFocus = False
        self.pendingFocusQueue = []
        self.lastUserActivityTime = QDateTime.currentDateTime()

        self.autoFocusTimer = QTimer(self)
        self.autoFocusTimer.setInterval(1000)  # check every second
        self.autoFocusTimer.timeout.connect(self._checkAutoFocus)
        self.autoFocusTimer.start()

        self.setMouseTracking(True)

    @property
    def actor(self):
        return self.pfsPlot.actor

    @property
    def isConnected(self):
        return self.pfsPlot.isConnected

    def on_mouse_move(self, *args, **kwargs):
        """Update last user activity time when mouse moves."""
        self.lastUserActivityTime = QDateTime.currentDateTime()

    def eventFilter(self, obj, event):
        """Filter events to detect user activity events and update the activity time."""
        if event.type() in (QEvent.MouseMove, QEvent.KeyPress, QEvent.Wheel, QEvent.MouseButtonPress):
            self.on_mouse_move()
        return super().eventFilter(obj, event)

    def newTabDialog(self):
        """Launch new tab creation dialog."""
        return NewTabDialog(self)

    def newTab(self, title, nRows, nCols):
        """Create a new tabContainer with a given nRows and nCols to receive plotWidget."""
        container = tabContainer.TabContainer(self, nRows, nCols)
        self.addTab(container, title)
        # set the new tab active is what the user usually expect.
        self.setCurrentWidget(container)

    def closeTab(self, index):
        """Prompt before closing a tab."""
        reply = QMessageBox.question(self, 'Message', 'Are you sure to close this window?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.removeTab(index)

    def setEnabled(self, a0: bool) -> None:
        """Set all tabs enabled/disabled."""
        for index in range(self.count()):
            self.widget(index).setEnabled(a0)

    def showError(self, title, error):
        """Show an error dialog."""
        QMessageBox.critical(self, title, error, QMessageBox.Ok)

    def setAutofocus(self, state: bool):
        """Enable or disable auto-focus."""
        self.doAutoFocus = state

    def setAutoFocusGracePeriod(self, seconds: int):
        """Set the idle threshold for auto-focus in seconds."""
        self.autoFocusGracePeriod = seconds

    def newPlotAvailable(self, tabContainer):
        """Called when a new plot is available in a tab."""
        if tabContainer == self.currentWidget():
            return

        # Find the index of the tabContainer in the tabs
        index = self.indexOf(tabContainer)
        if index >= 0:
            # Set the information icon
            self.setTabIcon(index, self.iconInfo)

        if not self.doAutoFocus:
            return

        if tabContainer not in self.pendingFocusQueue:
            self.pendingFocusQueue.append(tabContainer)

    def loadLayout(self, layoutList):
        """Restore layout from a saved list of tab/plot definitions."""
       #  self.clear()  # Remove any existing tabs

        for tab in layoutList:
            tabName = tab["name"]
            plots = tab["plots"]
            # Create a new container with enough rows and columns
            nRows, nCols = 1, 1  # default to 1x1; or calculate based on plots if needed
            container = tabContainer.TabContainer(self, nRows, nCols)

            for plotKwargs in plots:
                # For each plot, add it directly in the grid
                container.setPlotWidgetInGrid(**plotKwargs)

            self.addTab(container, tabName)

        self.setCurrentIndex(0)

    def saveLayout(self):
        """Save the current layout of all tabs."""
        layoutList = []

        for i in range(self.count()):
            tab = self.widget(i)
            tabName = self.tabText(i)
            plots = []

            # Iterate over all widgets in the tab's layout grid
            layout = tab.layout()
            for row in range(layout.rowCount()):
                for col in range(layout.columnCount()):
                    item = layout.itemAtPosition(row, col)
                    if item is not None:
                        widget = item.widget()
                        if isinstance(widget, mplCanvas.MplWidget):
                            plots.append(widget.plotKwargs)

            layoutList.append({"name": tabName, "plots": plots})

        return layoutList

    def _currentTabChanged(self):
        """Update last activity and remove tab from queue if needed."""
        self.lastUserActivityTime = QDateTime.currentDateTime()
        currentTab = self.currentWidget()

        if currentTab in self.pendingFocusQueue:
            self.pendingFocusQueue.remove(currentTab)

        # Clear the icon when the user views this tab
        index = self.indexOf(currentTab)
        if index >= 0:
            self.setTabIcon(index, QIcon())

    def _checkAutoFocus(self):
        """Check if the user has been idle long enough to focus next tab."""
        if not self.doAutoFocus or not self.pendingFocusQueue:
            return

        idleSecs = self.lastUserActivityTime.secsTo(QDateTime.currentDateTime())

        if idleSecs >= self.autoFocusGracePeriod:
            nextTab = self.pendingFocusQueue.pop(0)
            self.setCurrentWidget(nextTab)
            self.lastUserActivityTime = QDateTime.currentDateTime()
