__author__ = 'alefur'

import importlib

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

    def setPlotWidget(self, plotBrowserButton, **plotClassKwargs):
        """Adding the plotWidget in the layout and remove the button"""
        self.setPlotWidgetInGrid(row=plotBrowserButton.row, col=plotBrowserButton.col, **plotClassKwargs)
        self.layout().removeWidget(plotBrowserButton)
        plotBrowserButton.deleteLater()

    def setPlotWidgetInGrid(self, modulePath, className, actor, key, row, col):
        """Create new plot widget and set in the grid."""
        # load the module and get the class.
        module = importlib.import_module(modulePath)
        classType = getattr(module, className)
        # updating class attribute.
        classType.actor = actor
        classType.key = key

        # creating the object with a canvas.
        w1 = mplCanvas.MplWidget(modulePath=modulePath, className=className, actor=actor, key=key, row=row, col=col)
        obj = classType(self, w1.canvas)
        # connecting event
        w1.canvas.mpl_connect('motion_notify_event', self.tabWidget.on_mouse_move)
        # add dedicated widgets to tweak the plots.
        w1.addTweakingWidgets(obj)

        # adding callbacks
        if obj.addCallback:
            self.tabWidget.actor.requireModels([obj.actor])
            self.tabWidget.actor.models[obj.actor].keyVarDict[obj.key].addCallback(obj.update)

        # adding the plotWidget in the layout
        self.layout().addWidget(w1, row, col)
