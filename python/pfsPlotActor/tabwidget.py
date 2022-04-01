__author__ = 'alefur'

from PyQt5.QtWidgets import QTabWidget


class TabWidget(QTabWidget):
    def __init__(self, centralWidget):
        QTabWidget.__init__(self)
        self.centralWidget = centralWidget
        #self.setTabsClosable(False)

        self.tabCloseRequested.connect(self.closeTab)
        self.currentChanged.connect(self.changeTab)

    def closeTab(self):
        """ close tab callback"""
        pass

    def changeTab(self):
        """ change tab callback"""
        pass
