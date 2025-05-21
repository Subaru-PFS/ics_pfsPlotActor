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

    def identify(self, keyvar):
        """Identify data from keyword current value"""
        # if no callback just return.
        if self.noCallback:
            return dict()

        values = keyvar.getValue()
        return dict(values=values)

    def update(self, keyvar=None):
        """Callback called each time a new key is generated, basically clear previous axes and plot latest dataset."""
        keyvar = self.keyvar if keyvar is None else keyvar

        try:
            dataId = self.identify(keyvar)
        except ValueError:
            dataId = dict()

        self.keyvar = keyvar

        self.clear()
        try:
            self.plot(**dataId, **self.tweakDict)
        except Exception as e:
            raise
            logging.warning(e)

        self.canvas.draw()

    def plot(self, *args, **kwargs):
        """Plot prototype."""
        pass

    def attachTweaks(self, tweaks):
        """ """
        self.tweaks = tweaks
