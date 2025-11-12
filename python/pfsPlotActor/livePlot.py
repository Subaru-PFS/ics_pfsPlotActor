import logging
from collections.abc import Iterable

import matplotlib as mpl
import psycopg2
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

mpl.rcParams.update({
    'font.size': 12,  # Default font size for everything
    'axes.titlesize': 14,  # Title of each subplot
    'axes.labelsize': 12,  # x and y labels
    'xtick.labelsize': 10,  # x-axis tick labels
    'ytick.labelsize': 10,  # y-axis tick labels
    'legend.fontsize': 11,  # Legend text
    'figure.titlesize': 16  # suptitle size
})


class LivePlot(object):
    # actor and key that to attach the callback to.
    actor = None
    key = None
    addCallback = True
    units = dict()

    def __init__(self, tabContainer, canvas):
        self.tabContainer = tabContainer
        self.canvas = canvas

        axes = self.initialize()
        self.axes = [axes] if not isinstance(axes, Iterable) else axes
        self.tweaks = dict()
        self.keyvar = None

    @property
    def fig(self):
        return self.canvas.figure

    @property
    def tweakDict(self):
        return dict([(k, w.getValue()) for k, w in self.tweaks.items()])

    @staticmethod
    def getConn():
        """
        Establishes a connection to the PostgreSQL database 'opdb'.

        Returns:
        conn: A PostgreSQL connection object.
        """
        return psycopg2.connect("dbname='opdb' host='db-ics' port=5432 user='pfs'")

    def initialize(self):
        """Initialize your axes"""
        return self.fig.add_subplot(111)

    def clear(self):
        """Clear your axes."""
        for ax in self.axes:
            ax.cla()

    def identify(self, keyvar, newValue):
        """Identify data from keyword current value"""
        return dict(dataId=keyvar.getValue(), newValue=newValue)

    def getDataIdFromKeyword(self, keyvar):
        newValue = keyvar is not None
        keyvar = self.keyvar if keyvar is None else keyvar

        # when you start and keyvar was not generated yet, you still want to be able to plot using visit box.
        if self.addCallback and keyvar is None:
            return dict(newValue=newValue, dataId=None)

        self.keyvar = keyvar

        # trying to get data from the keyword, newValue means that the keyword callback triggered that call.
        try:
            dataIdFromKeyword = self.identify(keyvar, newValue=newValue)
        except ValueError:
            dataIdFromKeyword = dict(newValue=newValue, dataId=None, skipPlotting=newValue)

        return dataIdFromKeyword

    def update(self, keyvar=None):
        """Callback called each time a new key is generated, basically clear previous axes and plot latest dataset."""
        dataIdFromKeyword = self.getDataIdFromKeyword(keyvar)
        print(dataIdFromKeyword)
        dataId = dataIdFromKeyword.get('dataId')
        skipPlotting = dataIdFromKeyword.get('skipPlotting', False)
        newValue = dataIdFromKeyword.get('newValue', False)

        if skipPlotting:
            return

        QApplication.setOverrideCursor(Qt.WaitCursor)  # ⏳ show busy cursor
        self.clear()
        try:
            plotted = self.plot(dataId, **self.tweakDict)
        except Exception as e:
            logging.warning(e)
            return
        finally:
            QApplication.restoreOverrideCursor()  # reset cursor no matter what

        self.canvas.draw()

        if newValue and plotted:
            self.tabContainer.tabWidget.newPlotAvailable(self.tabContainer)

    def plot(self, dataFromKeyword, **kwargs):
        """Plot prototype."""
        pass

    def attachTweaks(self, tweaks):
        """ """
        self.tweaks = tweaks
