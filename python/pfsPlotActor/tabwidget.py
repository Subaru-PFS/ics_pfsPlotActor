__author__ = 'alefur'

import pfsPlotActor.layout as layout
import pfsPlotActor.misc as misc
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtWidgets import QTabBar, QTabWidget, QLineEdit, QWidget, QPushButton


class EditableTabBar(QTabBar):
    def __init__(self, parent):
        QTabBar.__init__(self, parent)
        self._editor = QLineEdit(self)
        self._editor.setWindowFlags(Qt.Popup)
        self._editor.setFocusProxy(self)
        self._editor.editingFinished.connect(self.handleEditingFinished)
        self._editor.installEventFilter(self)

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


class PlotBrowser(QPushButton):
    def __init__(self, *args, **kwargs):
        QPushButton.__init__(self, *args, **kwargs)
        self.setMaximumWidth(50)
        self.setIcon(misc.Icon('graph'))


class TabContainer(QWidget):
    def __init__(self, nRows, nCols):
        QWidget.__init__(self)
        grid = layout.GridLayout()
        for row in range(nRows):
            for col in range(nCols):
                grid.addWidget(PlotBrowser(), row, col)

        self.setLayout(grid)


class TabWidget(QTabWidget):
    def __init__(self, centralWidget):
        QTabWidget.__init__(self)
        self.setTabBar(EditableTabBar(self))
        self.centralWidget = centralWidget

        self.tabCloseRequested.connect(self.closeTab)
        self.currentChanged.connect(self.changeTab)

    def newTab(self, title, nRows, nCols):
        container = TabContainer(nRows, nCols)
        self.addTab(container, title)

    def closeTab(self):
        """ close tab callback"""
        pass

    def changeTab(self):
        """ change tab callback"""
        pass
