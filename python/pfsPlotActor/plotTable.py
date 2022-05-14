__author__ = 'alefur'

from functools import partial

import pfsPlotActor.misc as misc
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QPushButton, QTableWidget, QTableWidgetItem, QMessageBox


class AddPlotButton(QPushButton):
    """Simple button to select the plot class in the table."""

    def __init__(self, *args, **kwargs):
        QPushButton.__init__(self, *args, **kwargs)
        self.setMaximumWidth(50)
        self.setIcon(misc.Icon('add'))


class TableRow(object):
    """Object representing a single row in the tableWidget."""

    def __init__(self, plotTable, modPath, className, classType):
        self.classType = classType

        self.modPath = QTableWidgetItem(modPath)
        self.modPath.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.className = QTableWidgetItem(className)
        self.className.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        self.actor = QTableWidgetItem(classType.actor)
        self.key = QTableWidgetItem(classType.key)

        self.addButton = AddPlotButton()
        self.addButton.clicked.connect(partial(plotTable.addPlotClicked, self))

    @property
    def items(self):
        return [self.modPath, self.className, self.actor, self.key, self.addButton]


class PlotTable(QTableWidget):
    """Table containing the plot definition per row."""
    columns = ['module', 'className', 'actor', 'key', '']

    def __init__(self, plotDialog, plotDescription):
        QTableWidget.__init__(self, len(plotDescription), len(PlotTable.columns), parent=plotDialog)
        self.setHorizontalHeaderLabels(PlotTable.columns)

        for row, plotArgs in enumerate(plotDescription):
            tableRow = TableRow(self, *plotArgs)
            for col, item in enumerate(tableRow.items):
                setItemFunc = self.setItem if isinstance(item, QTableWidgetItem) else self.setCellWidget
                setItemFunc(row, col, item)

        self.itemChanged.connect(self.autoResize)
        self.autoResize()

    @property
    def actualWidth(self):
        # not very happy with that but...
        return sum([self.columnWidth(j) for j in range(len(PlotTable.columns))]) + 40

    def autoResize(self, item=None):
        """Resize all columns to fit content."""
        for j in list(range(len(PlotTable.columns))):
            self.resizeColumnToContents(j)

        self.parent().resize(self.actualWidth, self.parent().height())

    def addPlotClicked(self, tableRow, *args):
        """Called when the user click on the add plot button."""
        # updating default actor and key.
        tableRow.classType.actor = tableRow.actor.text()
        if not tableRow.classType.actor:
            QMessageBox.critical(self, "Add plot failed !", "Actor field needs to be filled in...", QMessageBox.Ok)
            return

        tableRow.classType.key = tableRow.key.text()
        if not tableRow.classType.key:
            QMessageBox.critical(self, "Add plot failed !", "Key field needs to be filled in...", QMessageBox.Ok)
            return

        # class plotDialog.setPlotClass
        self.parent().setPlotClass(tableRow.classType)
