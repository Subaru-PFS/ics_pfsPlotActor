__author__ = 'alefur'

from PyQt5.QtWidgets import QGridLayout, QVBoxLayout, QHBoxLayout

spacing = 1


class GridLayout(QGridLayout):
    def __init__(self, *args, **kwargs):
        QGridLayout.__init__(self, *args, **kwargs)
        self.setSpacing(spacing)


class VBoxLayout(QVBoxLayout):
    def __init__(self, *args, **kwargs):
        QVBoxLayout.__init__(self, *args, **kwargs)
        self.setSpacing(spacing)


class HBoxLayout(QHBoxLayout):
    def __init__(self, *args, **kwargs):
        QHBoxLayout.__init__(self, *args, **kwargs)
        self.setSpacing(spacing)
