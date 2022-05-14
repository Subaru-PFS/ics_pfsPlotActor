__author__ = 'alefur'

import inspect
import pkgutil
from functools import partial
from importlib import reload
from importlib.util import find_spec

import pfsPlotActor.layout as layout
import pfsPlotActor.livePlot as livePlot
import pfsPlotActor.misc as misc
import pfsPlotActor.plots as plots
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QPushButton, QDialog, QTableWidget, QTableWidgetItem, QMessageBox


class AddPlotButton(QPushButton):
    """Simple button to select the plot class in the table."""

    def __init__(self, *args, **kwargs):
        QPushButton.__init__(self, *args, **kwargs)
        self.setMaximumWidth(50)
        self.setIcon(misc.Icon('add'))


class RefreshPlotTableButton(QPushButton):
    """Simple button to select the plot class in the table."""

    def __init__(self, *args, **kwargs):
        QPushButton.__init__(self, *args, **kwargs)
        self.setMaximumWidth(50)
        self.setIcon(misc.Icon('refresh'))


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


class PlotBrowserDialog(QDialog):
    """Dialog to choose which plotClass/plotWindow to add in the selected space."""

    def __init__(self):
        QDialog.__init__(self)
        self.plotTable = None
        self.clickedFrom = None
        self.setLayout(layout.VBoxLayout())

        refreshButton = RefreshPlotTableButton()
        refreshButton.clicked.connect(self.refreshPlotTableButton)
        self.layout().addWidget(refreshButton)

        self.refreshPlotTableButton()
        self.setWindowTitle('Add New Plot')
        # self.setVisible(True)
        # self.hide()

    def refreshPlotTableButton(self):
        """"""
        if self.plotTable is not None:
            self.layout().removeWidget(self.plotTable)
            self.plotTable.deleteLater()

        self.plotTable = PlotTable(self, self.inspectPlotDefinition())
        self.layout().addWidget(self.plotTable)

    def inspectPlotDefinition(self):
        """Inspect pfsPlotActor.plots and look for livePlot subclasses."""
        reload(plots)
        livePlots = []

        for __, modName, __ in pkgutil.iter_modules(plots.__path__):
            modPath = f'pfsPlotActor.plots.{modName}'
            spec = find_spec(modPath)
            module = spec.loader.load_module()
            livePlots.extend([(modPath, className, classType) for className, classType in inspect.getmembers(module) if
                              inspect.isclass(classType) and issubclass(classType, livePlot.LivePlot)])

        return livePlots

    def setPlotClass(self, classType):
        """Call tabContainer with classType and the button to be replaced."""
        browseButton = self.clickedFrom
        tabContainer = browseButton.parent()
        tabContainer.setPlotWidget(classType, browseButton)
        self.close()

    def browse(self, browseButton):
        """ """
        self.clickedFrom = browseButton
        self.show()

    def close(self) -> bool:
        self.hide()


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
        self.parent().tabWidget.plotBrowserDialog.browse(self)
