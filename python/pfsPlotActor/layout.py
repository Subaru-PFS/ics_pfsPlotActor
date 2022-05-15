__author__ = 'alefur'

from PyQt5.QtWidgets import QGridLayout, QVBoxLayout, QHBoxLayout

spacing = 1


class GridLayout(QGridLayout):
    """Overdefine Qt QGridLayout."""

    def __init__(self, *args, **kwargs):
        QGridLayout.__init__(self, *args, **kwargs)
        self.setSpacing(spacing)

    def minimizeContentMargin(self, left=0, top=0, right=0, bottom=0):
        """ minimize content margin as much as you can."""
        self.setContentsMargins(left, top, right, bottom)


class GBoxValue(GridLayout):
    def __init__(self):
        GridLayout.__init__(self)
        self.minimizeContentMargin(top=1)


class VBoxLayout(QVBoxLayout):
    """Overdefine Qt QVBoxLayout."""

    def __init__(self, *args, **kwargs):
        QVBoxLayout.__init__(self, *args, **kwargs)
        self.setSpacing(spacing)

    def minimizeContentMargin(self, left=0, top=0, right=0, bottom=0):
        """ minimize content margin as much as you can."""
        self.setContentsMargins(left, top, right, bottom)


class HBoxLayout(QHBoxLayout):
    """Overdefine Qt QHBoxLayout."""

    def __init__(self, *args, **kwargs):
        QHBoxLayout.__init__(self, *args, **kwargs)
        self.setSpacing(spacing)

    def minimizeContentMargin(self, left=0, top=0, right=0, bottom=0):
        """ minimize content margin as much as you can."""
        self.setContentsMargins(left, top, right, bottom)
