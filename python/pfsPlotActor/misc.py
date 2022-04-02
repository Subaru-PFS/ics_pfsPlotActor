import os

from PyQt5.QtGui import QPixmap, QIcon


class Icon(QIcon):
    def __init__(self, iconName):
        absPath = os.path.join(os.path.expandvars('$ICS_PFSPLOTACTOR_DIR'), 'icons', f'{iconName}.png')
        pix = QPixmap()
        pix.load(absPath)
        QIcon.__init__(self, pix)
