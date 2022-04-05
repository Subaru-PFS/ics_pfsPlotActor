__author__ = 'alefur'

import argparse
import os
import pwd
import sys

import pfsPlotActor.mainWindow as mainWindow
from PyQt5.QtWidgets import QApplication


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', default=pwd.getpwuid(os.getuid()).pw_name, type=str, nargs='?', help='cmdr name')
    parser.add_argument('--fontsize', default=8, type=int, nargs='?', help='application font size')
    args = parser.parse_args()

    app = QApplication(sys.argv)
    screen = app.desktop().screenGeometry()

    # setting user fontsize for Qt
    font = app.font()
    font.setPointSize(args.fontsize)
    app.setFont(font)

    # setting user fontsize for matplotlib
    import matplotlib
    matplotlib.rcParams.update({'font.size': args.fontsize})

    import qt5reactor
    qt5reactor.install()
    from twisted.internet import reactor

    import miniActor
    actor = miniActor.connectActor(['hub'])

    try:
        ex = mainWindow.PfsPlot(reactor, actor, args.name, screen)
    except:
        actor.disconnectActor()
        raise

    reactor.run()
    actor.disconnectActor()


if __name__ == "__main__":
    main()
