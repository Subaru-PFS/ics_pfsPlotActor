from collections.abc import Iterable


class LivePlot(object):
    def __init__(self, canvas):
        self.canvas = canvas

        axes = self.initialize()
        self.axes = [axes] if not isinstance(axes, Iterable) else axes

    @property
    def fig(self):
        return self.canvas.figure

    def initialize(self):
        """Initialize your axes"""
        return self.fig.add_subplot(111)

    def clear(self):
        """Clear your axes."""
        for ax in self.axes:
            ax.cla()

    def identify(self, keyvar):
        """Identify data from keyword current value"""
        values = keyvar.getValue()
        return dict(values=values)

    def update(self, keyvar):
        """Callback called each time a new key is generated, basically clear previous axes and plot latest dataset."""
        try:
            dataId = self.identify(keyvar)
        except ValueError:
            return

        self.clear()
        self.plot(**dataId)
        self.canvas.draw()

    def plot(self, *args, **kwargs):
        """Plot prototype."""
        pass
