import pfsPlotActor.layout as layout
from PyQt5.QtWidgets import QCheckBox, QGroupBox, QSizePolicy, QLineEdit, QComboBox


class Tweak(QGroupBox):
    """Editable field to be parsed to updatePlot function."""
    valueType = QLineEdit

    def __init__(self, title, unit=None):
        QGroupBox.__init__(self)
        title = f'{title} ({unit})' if unit else title
        self.setTitle('%s' % title)

        grid = layout.GBoxValue()
        self.value = self.valueType()
        grid.addWidget(self.value, 0, 0)
        self.setLayout(grid)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)

    def attachCallback(self, callback):
        self.updateCallback = callback
        self.value.returnPressed.connect(self.updatePlot)

    def updatePlot(self, *args, **kwargs):
        self.updateCallback()


class Float(Tweak):
    def getValue(self):
        return float(self.value.text())

    def setValue(self, value):
        return self.value.setText(str(float(value)))


class Int(Tweak):
    def getValue(self):
        return int(self.value.text())

    def setValue(self, value):
        self.value.setText(str(int(value)))


class CheckBox(Tweak):
    valueType = QCheckBox

    def getValue(self):
        return bool(self.value.isChecked())

    def setValue(self, value):
        self.value.setChecked(bool(value))

    def attachCallback(self, callback):
        self.updateCallback = callback
        self.value.stateChanged.connect(self.updatePlot)


class String(Tweak):
    def getValue(self):
        return self.value.text()

    def setValue(self, value):
        self.value.setText(str(value))


class ComboBox(Tweak):
    valueType = QComboBox

    def __init__(self, title, unit=None, choices=()):
        super().__init__(title, unit=unit)
        self.value.addItems([str(choice) for choice in choices])
        self.choices = choices  # Keep reference for getValue

    def getValue(self):
        return self.choices[self.value.currentIndex()]

    def setValue(self, value):
        if value in self.choices:
            self.value.setCurrentIndex(self.choices.index(value))

    def attachCallback(self, callback):
        self.updateCallback = callback
        self.value.currentIndexChanged.connect(self.updatePlot)
