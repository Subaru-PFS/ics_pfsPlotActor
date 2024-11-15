import matplotlib

matplotlib.use('Qt5Agg')

import matplotlib

matplotlib.use('Qt5Agg')

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from PyQt5.QtWidgets import QWidget, QSizePolicy, QGridLayout
from PyQt5.QtCore import Qt
from matplotlib.figure import Figure
import inspect
import pfsPlotActor.layout as layout
import pfsPlotActor.tweaks as tweaks

from PyQt5.QtWidgets import QMenu


class MplWidget(QWidget):
    """
    Widget to embed a Matplotlib canvas with an optional toolbar and dynamically generated
    parameter controls based on a plot function's signature.

    Attributes
    ----------
    maxNumCols : int
        Maximum number of columns to arrange tweak widgets in the grid.
    canvas : MplCanvas
        The Matplotlib canvas instance for plotting.
    toolbar : NavigationToolbar2QT
        Toolbar for Matplotlib interactions.
    tweakGridLayout : QGridLayout
        Layout to hold dynamically generated tweaking widgets.
    """

    maxNumCols = 10  # Maximum number of columns in the tweak widgets grid

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialize the main plotting canvas and toolbar
        self.canvas = MplCanvas()
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        # Initialize tweak widgets visibility state
        self.tweakWidgetsVisible = False

        # Use a custom vertical box layout for the main widget structure
        vbox = layout.VBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.toolbar)

        # Create and add tweaking widgets grid layout, set to visible by default
        self.tweakGridLayout = QGridLayout()
        self.tweakGridLayout.setContentsMargins(0, 0, 0, 0)

        # Add tweak widgets grid layout in a separate widget (initially hidden)
        self.tweakGridWidget = QWidget()
        self.tweakGridWidget.setLayout(self.tweakGridLayout)
        self.tweakGridWidget.setVisible(self.tweakWidgetsVisible)
        vbox.insertWidget(0, self.tweakGridWidget)

        self.setLayout(vbox)

        # Connect context menu event in MplCanvas
        self.canvas.setContextMenuPolicy(Qt.CustomContextMenu)
        self.canvas.customContextMenuRequested.connect(self.showContextMenu)

    def addTweakingWidgets(self, livePlot):
        """
        Generates and adds dynamic tweaking widgets based on the `livePlot.plot` function parameters.

        Parameters
        ----------
        livePlot : object
            An object with a plot method whose parameters are inspected to generate
            controls for adjusting plot settings.

        Notes
        -----
        Widgets are created based on parameter types: `CheckBox` for bool, `Int` for int,
        `Float` for float, and `String` for str. Widgets are arranged in a grid layout.
        """
        tweakDict = dict()
        signature = inspect.signature(livePlot.plot)

        widgets = []

        # Generate widgets based on the plot function's parameters and their default values
        for paramName, paramValue in signature.parameters.items():
            if paramValue.default is inspect._empty:
                continue

            # Determine widget class based on parameter type
            widgetClass = {
                bool: tweaks.CheckBox,
                int: tweaks.Int,
                float: tweaks.Float,
                str: tweaks.String
            }.get(type(paramValue.default), None)

            if widgetClass is None:
                continue

            unit = livePlot.units.get(paramName, None)

            # Initialize and configure the widget
            widget = widgetClass(paramName, unit=unit)
            widget.setValue(paramValue.default)
            widget.attachCallback(livePlot.update)
            tweakDict[paramName] = widget
            widgets.append(widget)

        # Attach tweak controls to the livePlot instance
        livePlot.attachTweaks(tweakDict)

        # Arrange widgets in a grid layout with a maximum number of columns
        for i, widget in enumerate(widgets):
            row, col = divmod(i, MplWidget.maxNumCols)
            self.tweakGridLayout.addWidget(widget, row, col)

        self.toggleTweakWidgets()

    def showContextMenu(self, pos):
        """Display the context menu to toggle tweak parameters."""
        menu = QMenu(self)
        toggleAction = menu.addAction(
            "Show Tweak Parameters" if not self.tweakWidgetsVisible else "Hide Tweak Parameters")
        action = menu.exec_(self.canvas.mapToGlobal(pos))

        if action == toggleAction:
            self.toggleTweakWidgets()

    def toggleTweakWidgets(self):
        """Toggle the visibility of tweak widgets."""
        self.tweakWidgetsVisible = not self.tweakWidgetsVisible
        self.tweakGridWidget.setVisible(self.tweakWidgetsVisible)


class MplCanvas(FigureCanvasQTAgg):
    """
    Canvas for embedding a Matplotlib figure in a PyQt application.
    """

    def __init__(self, *args, **kwargs):
        fig = Figure(*args, **kwargs)
        super().__init__(fig)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
