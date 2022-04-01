import matplotlib

matplotlib.use('Qt5Agg')

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT

from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.figure import Figure


class MplWidget(QWidget):
    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)

        self.canvas = MplCanvas()
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.addWidget(self.toolbar)

        self.setLayout(layout)


class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, *args, **kwargs):
        fig = Figure(*args, **kwargs)
        super(MplCanvas, self).__init__(fig)
