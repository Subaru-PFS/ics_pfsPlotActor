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

    specNums = [i + 1 for i in range(4)]

    viscamNames = [f'b{specNum}' for specNum in specNums] + [f'r{specNum}' for specNum in specNums]
    nircamNames = [f'n{specNum}' for specNum in specNums]

    xcus = [f'xcu_{cam}' for cam in viscamNames + nircamNames]
    ccds = [f'ccd_{cam}' for cam in viscamNames]
    hxs = [f'hx_{cam}' for cam in nircamNames]
    enus = [f'enu_sm{specNum}' for specNum in specNums]

    sps = ['sps'] + enus + xcus + ccds + hxs
    pfi = ['mcs', 'fps', 'ag', 'agcc']

    listenActors = ['hub'] + sps + pfi
    actor = miniActor.connectActor(listenActors)

    try:
        ex = mainWindow.PfsPlot(reactor, actor, args.name, screen)

        # resizing to sensible resolution.
        ex.resize(1024, 768)

        # Center the window on the screen
        qr = ex.frameGeometry()
        cp = app.desktop().availableGeometry().center()
        qr.moveCenter(cp)
        ex.move(qr.topLeft())
    except:
        actor.disconnectActor()
        raise

    reactor.run()
    actor.disconnectActor()


if __name__ == "__main__":
    main()
