import logging
from collections.abc import Iterable

import psycopg2


class LivePlot(object):
    # actor and key that to attach the callback to.
    actor = None
    key = None
    noCallback = False
    units = dict()

    def __init__(self, canvas):
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
        return dict(dataId=keyvar.getValue())

    def getDataIdFromKeyword(self, keyvar):
        newValue = keyvar is not None
        keyvar = self.keyvar if keyvar is None else keyvar

        # I think that's the equivalent.
        if self.noCallback or keyvar is None:
            return dict()

        self.keyvar = keyvar

        # trying to get data from the keyword, newValue means that the keyword callback triggered that call.
        try:
            dataIdFromKeyword = self.identify(keyvar, newValue=newValue)
        except ValueError:
            dataIdFromKeyword = dict()

        return dataIdFromKeyword

    def update(self, keyvar=None):
        """Callback called each time a new key is generated, basically clear previous axes and plot latest dataset."""
        dataIdFromKeyword = self.getDataIdFromKeyword(keyvar)

        skipPlotting = dataIdFromKeyword.get('skipPlotting', False)
        dataId = dataIdFromKeyword.get('dataId', None)

        if skipPlotting:
            return

        self.clear()
        try:
            self.plot(dataId, **self.tweakDict)
        except Exception as e:
            logging.warning(e)

        self.canvas.draw()

    def plot(self, dataFromKeyword, **kwargs):
        """Plot prototype."""
        pass

    def attachTweaks(self, tweaks):
        """ """
        self.tweaks = tweaks
