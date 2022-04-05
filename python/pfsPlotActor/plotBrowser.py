__author__ = 'alefur'

import glob
import inspect
import os
from importlib.util import find_spec

import pfsPlotActor.layout as layout
import pfsPlotActor.livePlot as livePlot
import pfsPlotActor.misc as misc
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QPushButton, QDialog, QTableWidget, QTableWidgetItem, QMessageBox


class AddPlotButton(QPushButton):
    """Simple button to select the plot class in the table."""

    def __init__(self):
        QPushButton.__init__(self)
        self.setMaximumWidth(50)
        self.setIcon(misc.Icon('add'))


class TableRow(object):
    """Object representing a single row in the tableWidget."""

    def __init__(self, plotTable, modPath, className, classType):
        self.plotTable = plotTable
        self.classType = classType

        self.modPath = QTableWidgetItem(modPath)
        self.modPath.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.className = QTableWidgetItem(className)
        self.className.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        self.actor = QTableWidgetItem(classType.actor)
        self.key = QTableWidgetItem(classType.key)

        self.addButton = AddPlotButton()
        self.addButton.clicked.connect(self.addPlotClicked)

    @property
    def items(self):
        return [self.modPath, self.className, self.actor, self.key, self.addButton]

    def addPlotClicked(self):
        # updating default param
        self.classType.actor = self.actor.text()
        if not self.classType.actor:
            QMessageBox.critical(self.plotTable, "Add plot failed !", "Actor field needs to be filled in...",
                                 QMessageBox.Ok)
            return

        self.classType.key = self.key.text()
        if not self.classType.key:
            QMessageBox.critical(self.plotTable, "Add plot failed !", "key field needs to be filled in...",
                                 QMessageBox.Ok)
            return

        # class plotDialog.setPlotClass
        self.plotTable.parent().setPlotClass(self.classType)


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
        return sum([self.columnWidth(j) for j in range(len(PlotTable.columns))]) + 60

    def autoResize(self, item=None):
        """Resize all columns to fit content."""
        for j in list(range(len(PlotTable.columns))):
            self.resizeColumnToContents(j)

        self.parent().resize(self.actualWidth, self.parent().height())


class PlotBrowserDialog(QDialog):
    """Dialog to choose which plotClass/plotWindow to add in the selected space."""

    def __init__(self, browseButton):
        QDialog.__init__(self, browseButton)
        self.setLayout(layout.VBoxLayout())

        plotTable = PlotTable(self, self.inspectPlotDefinition())
        self.layout().addWidget(plotTable)
        self.setWindowTitle('Add New Plot')
        self.setVisible(True)

    def inspectPlotDefinition(self):
        """Inspect pfsPlotActor.plots and look for livePlot subclasses."""
        livePlots = []
        mods = glob.glob(os.path.join(os.path.expandvars('$ICS_PFSPLOTACTOR_DIR'), 'python', 'pfsPlotActor',
                                      'plots', '*.py'))

        for modulePath in mods:
            __, mod = os.path.split(modulePath)
            modName, __ = os.path.splitext(mod)
            modPath = f'pfsPlotActor.plots.{modName}'
            spec = find_spec(modPath)
            module = spec.loader.load_module()
            livePlots.extend([(modPath, className, classType) for className, classType in inspect.getmembers(module) if
                              inspect.isclass(classType) and issubclass(classType, livePlot.LivePlot)])

        return livePlots

    def setPlotClass(self, classType):
        """Call tabContainer with classType and the button to be replaced."""
        browseButton = self.parent()
        tabContainer = browseButton.parent()
        tabContainer.setPlotWidget(classType, browseButton)
        self.close()


class PlotBrowserButton(QPushButton):
    """Simple button which create PlotBrowserDialog. it actually knows its position in the tabContainer grid."""

    def __init__(self, tabContainer, row, col):
        QPushButton.__init__(self, tabContainer)
        self.row = row
        self.col = col
        self.setMaximumWidth(50)
        self.setIcon(misc.Icon('graph'))
        self.clicked.connect(self.browse)

    def browse(self):
        """Just create plotBrowserDialog."""
        dialog = PlotBrowserDialog(self)
