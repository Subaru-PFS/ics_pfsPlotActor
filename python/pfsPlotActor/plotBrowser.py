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

    def __init__(self, pfsPlot):
        QDialog.__init__(self)
        self.pfsPlot = pfsPlot
        self.plotTable = None
        self.clickedFrom = None
        self.setLayout(layout.VBoxLayout())

        refreshButton = RefreshPlotTableButton()
        refreshButton.clicked.connect(self.refreshPlotTable)
        self.layout().addWidget(refreshButton)

        self.refreshPlotTable()
        self.setWindowTitle('Add New Plot')

    @property
    def config(self):
        return self.pfsPlot.actor.actorConfig

    def refreshPlotTable(self):
        """Dynamically refresh the available plots table."""
        if self.plotTable is not None:
            self.layout().removeWidget(self.plotTable)
            self.plotTable.deleteLater()

        self.plotTable = plotTable.PlotTable(self, self.inspectPlotDefinition())
        self.layout().addWidget(self.plotTable)

        self.resize(self.plotTable.actualWidth + 20, self.height())

    def inspectPlotDefinition(self):
        """Inspect pfsPlotActor.plots and look for livePlot subclasses."""
        reload(plots)
        ignorePlots = self.config.get('ignorePlots', [])

        livePlots = []

        for __, modName, __ in pkgutil.iter_modules(plots.__path__):
            modPath = f'pfsPlotActor.plots.{modName}'
            spec = find_spec(modPath)
            module = spec.loader.load_module()

            for className, classType in inspect.getmembers(module):
                if className in ignorePlots:
                    continue

                if inspect.isclass(classType) and issubclass(classType, livePlot.LivePlot):
                    livePlots.append((modPath, className, classType))

        return livePlots

    def setPlotClass(self, **plotClassKwargs):
        """Call tabContainer with classType and the button to be replaced."""
        browseButton = self.clickedFrom
        tabContainer = browseButton.parent()
        tabContainer.setPlotWidget(browseButton, **plotClassKwargs)
        self.close()

    def browse(self, browseButton):
        """Temporary reference browseButton to the dialog."""
        self.clickedFrom = browseButton
        self.show()

    def close(self) -> bool:
        """For performance sake, dont close it, just hide it."""
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
