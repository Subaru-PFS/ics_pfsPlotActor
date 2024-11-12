import matplotlib

matplotlib.use('Qt5Agg')

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT

from PyQt5.QtWidgets import QWidget, QSizePolicy
from matplotlib.figure import Figure

import inspect
import pfsPlotActor.layout as layout
import pfsPlotActor.tweaks as tweaks

from PyQt5.QtWidgets import QGridLayout


class MplWidget(QWidget):
    maxNumCols = 8  # Number of columns (you can adjust this if needed)

    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)

        self.canvas = MplCanvas()
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        vbox = layout.VBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.toolbar)

        self.setLayout(vbox)

    def addTweakingWidgets(self, livePlot):
        """
        Inspect livePlot.plot function arguments and dynamically add editable fields.

        If the number of widgets exceeds 6, they are arranged in two rows.
        """
        tweakDict = dict()
        signature = inspect.signature(livePlot.plot)

        widgets = []
        # Generate all the widgets based on function signature.
        for paramName, paramValue in signature.parameters.items():
            if paramValue.default is inspect._empty:
                continue

            # Determine the widget class based on the parameter type.
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
            widgets.append(widget)  # Collect all widgets

        # Attach the tweak dictionary to the live plot.
        livePlot.attachTweaks(tweakDict)

        # Create a grid layout to arrange widgets.
        gridLayout = QGridLayout()

        # Arrange widgets in the grid.

        for i, widget in enumerate(widgets):
            row = i // MplWidget.maxNumCols  # Calculate the row number
            col = i % MplWidget.maxNumCols  # Calculate the column number
            gridLayout.addWidget(widget, row, col)

        # Insert the grid layout at the top of the main layout.
        self.layout().insertLayout(0, gridLayout)


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, *args, **kwargs):
        fig = Figure(*args, **kwargs)
        super(MplCanvas, self).__init__(fig)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
