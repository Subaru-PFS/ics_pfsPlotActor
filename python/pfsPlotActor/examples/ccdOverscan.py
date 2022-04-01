import os

import fpga.geom as geom
import numpy as np
import pfsPlotActor.livePlot as livePlot
from astropy.stats import sigma_clip


class CcdOverscan(livePlot.LivePlot):
    label = 'CCD Overscan'
    key = 'filepath'

    def __init__(self, canvas, cam):
        self.actor = f'ccd_{cam}'
        livePlot.LivePlot.__init__(self, canvas)

    def initialize(self):
        """ """
        gs = self.fig.add_gridspec(8, 5, wspace=0.05, hspace=0.05)

        self.ax1 = [self.fig.add_subplot(gs[nAmp, :-1]) for nAmp in range(8)]
        self.ax2 = [self.fig.add_subplot(gs[nAmp, -1]) for nAmp in range(8)]
        return self.ax1 + self.ax2

    def identify(self, keyvar):
        """ """
        [root, night, fname] = keyvar.getValue()
        args = [root, night, 'sps', fname]
        filepath = os.path.join(*args)
        return dict(filepath=filepath)

    def plot(self, filepath, nSigma=5):
        """ """
        exp = geom.Exposure(filepath)
        ampIms, osIms, _ = exp.splitImage()
        clipped = sigma_clip(osIms, axis=2)
        levelPerRow = clipped.mean(axis=2)

        self.fig.suptitle(f'Serial Overscan {filepath}')

        for nAmp in range(8):
            ax1 = self.ax1[nAmp]
            ax2 = self.ax2[nAmp]

            yi = levelPerRow[nAmp] + np.random.normal(size=levelPerRow.shape[1])
            xi = np.arange(len(levelPerRow[nAmp]))
            p = np.polyfit(xi, yi, deg=2)
            model = np.polyval(p, xi)
            resid = yi - model
            mask = sigma_clip(resid.ravel(), sigma=nSigma)

            ax1.plot(yi, alpha=0.6)
            ax1.plot(model, alpha=0.8)
            ax1.grid()

            ax1.set_ylabel(f'a{nAmp}')
            ax1.set_xlim(-10, 4200)
            ax1.set_ylim(model.min() - nSigma * mask.std(), model.max() + nSigma * mask.std())

            ax2.hist(mask, label=f'{round(mask.mean(), 2)} +- {round(mask.std(), 2)}', bins=15)
            ax2.legend()

            ax2.grid()
            ax2.set_yticks([])
