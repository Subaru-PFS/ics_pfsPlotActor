__author__ = 'alefur'

import inspect
import pkgutil
from importlib import reload
from importlib.util import find_spec

import pfsPlotActor.layout as layout
import pfsPlotActor.livePlot as livePlot
import pfsPlotActor.misc as misc
import pfsPlotActor.plotTable as plotTable
import pfsPlotActor.plots as plots
from PyQt5.QtWidgets import QPushButton, QDialog


class RefreshPlotTableButton(QPushButton):
    """Simple button to select the plot class in the table."""

    def __init__(self, *args, **kwargs):
        QPushButton.__init__(self, *args, **kwargs)
        self.setMaximumWidth(50)
        self.setIcon(misc.Icon('refresh'))


class PlotBrowserDialog(QDialog):
    """Dialog to choose which plotClass/plotWindow to add in the selected space."""

    def __init__(self):
        QDialog.__init__(self)
        self.plotTable = None
        self.clickedFrom = None
        self.setLayout(layout.VBoxLayout())

        refreshButton = RefreshPlotTableButton()
        refreshButton.clicked.connect(self.refreshPlotTable)
        self.layout().addWidget(refreshButton)

        self.refreshPlotTable()
        self.setWindowTitle('Add New Plot')

    def refreshPlotTable(self):
        """"""
        if self.plotTable is not None:
            self.layout().removeWidget(self.plotTable)
            self.plotTable.deleteLater()

        self.plotTable = plotTable.PlotTable(self, self.inspectPlotDefinition())
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
