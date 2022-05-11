from collections.abc import Iterable


class LivePlot(object):
    # actor and key that to attach the callback to.
    actor = None
    key = None

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

    def initialize(self):
        """Initialize your axes"""
        return self.fig.add_subplot(111)

    def clear(self):
        """Clear your axes."""
        for ax in self.fig.get_axes():
            ax.cla()

    def identify(self, keyvar):
        """Identify data from keyword current value"""
        values = keyvar.getValue()
        return dict(values=values)

    def update(self, keyvar=None):
        """Callback called each time a new key is generated, basically clear previous axes and plot latest dataset."""
        keyvar = self.keyvar if keyvar is None else keyvar
        if keyvar is None:
            return
        try:
            dataId = self.identify(keyvar)
        except ValueError:
            return

        self.keyvar = keyvar

        self.clear()
        self.plot(**dataId, **self.tweakDict)
        self.canvas.draw()

    def plot(self, *args, **kwargs):
        """Plot prototype."""
        pass

    def attachTweaks(self, tweaks):
        """ """
        self.tweaks = tweaks
