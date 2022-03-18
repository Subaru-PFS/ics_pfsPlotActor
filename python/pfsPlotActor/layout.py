__author__ = 'alefur'

from PyQt5.QtWidgets import QGridLayout, QVBoxLayout, QHBoxLayout

spacing = 2


class GridLayout(QGridLayout):
    """Overdefine Qt QGridLayout."""

    def __init__(self, *args, **kwargs):
        QGridLayout.__init__(self, *args, **kwargs)
        self.setSpacing(spacing)

    def minimizeContentMargin(self):
        """ minimize content margin as much as you can."""
        self.setSpacing(1)
        self.setContentsMargins(0, 0, 0, 0)


class VBoxLayout(QVBoxLayout):
    """Overdefine Qt QVBoxLayout."""

    def __init__(self, *args, **kwargs):
        QVBoxLayout.__init__(self, *args, **kwargs)
        self.setSpacing(spacing)


class HBoxLayout(QHBoxLayout):
    """Overdefine Qt QHBoxLayout."""

    def __init__(self, *args, **kwargs):
        QHBoxLayout.__init__(self, *args, **kwargs)
        self.setSpacing(spacing)
