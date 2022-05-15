__author__ = 'alefur'

import pfsPlotActor.layout as layout
import pfsPlotActor.mplCanvas as mplCanvas
import pfsPlotActor.plotBrowser as plotBrowser
from PyQt5.QtWidgets import QWidget


class TabContainer(QWidget):
    """Widget which contain the plot(s) grid for a given tab."""

    def __init__(self, tabWidget, nRows, nCols):
        self.tabWidget = tabWidget
        QWidget.__init__(self)
        grid = layout.GridLayout()
        # Just add the plotBrowserButton(s) for a start, the user is invited to replace tjem with actual plots.
        for row in range(nRows):
            for col in range(nCols):
                grid.addWidget(plotBrowser.PlotBrowserButton(self, row, col), row, col)

        self.setLayout(grid)

    def setPlotWidget(self, classType, plotBrowserButton):
        """Set new plot widget in-place of the plotBrowserButton."""
        # creating the object with a canvas.
        w1 = mplCanvas.MplWidget()
        obj = classType(w1.canvas)
        # add dedicated widgets to tweak the plots.
        w1.addTweakingWidgets(obj)
        # adding callbacks
        self.tabWidget.actor.requireModels([obj.actor])
        self.tabWidget.actor.models[obj.actor].keyVarDict[obj.key].addCallback(obj.update)
        # adding the plotWidget in the layout and remove the button.
        self.layout().addWidget(w1, plotBrowserButton.row, plotBrowserButton.col)
        self.layout().removeWidget(plotBrowserButton)
        plotBrowserButton.deleteLater()
