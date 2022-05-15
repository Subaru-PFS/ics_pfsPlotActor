import matplotlib

matplotlib.use('Qt5Agg')

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT

from PyQt5.QtWidgets import QWidget, QSizePolicy
from matplotlib.figure import Figure

import inspect
import pfsPlotActor.layout as layout
import pfsPlotActor.tweaks as tweaks


class MplWidget(QWidget):
    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)

        self.canvas = MplCanvas()
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        vbox = layout.VBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.toolbar)

        self.setLayout(vbox)

    def addTweakingWidgets(self, livePlot):
        """ """
        hbox = layout.HBoxLayout()
        tweakDict = dict()
        signature = inspect.signature(livePlot.plot)

        for paramName, paramValue in signature.parameters.items():
            if paramValue.default is inspect._empty:
                continue

            if isinstance(paramValue.default, bool):
                widgetClass = tweaks.CheckBox
            elif isinstance(paramValue.default, int):
                widgetClass = tweaks.Int
            elif isinstance(paramValue.default, float):
                widgetClass = tweaks.Float
            elif isinstance(paramValue.default, str):
                widgetClass = tweaks.String
            else:
                continue

            widget = widgetClass(paramName)
            widget.setValue(paramValue.default)
            widget.attachCallback(livePlot.update)
            tweakDict[paramName] = widget
            hbox.addWidget(widget)

        livePlot.attachTweaks(tweakDict)
        self.layout().insertLayout(0, hbox)


class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, *args, **kwargs):
        fig = Figure(*args, **kwargs)
        super(MplCanvas, self).__init__(fig)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
