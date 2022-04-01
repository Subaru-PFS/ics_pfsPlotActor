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
        gs = self.fig.add_gridspec(8, hspace=0.2)
        return gs.subplots(sharex=True)

    def identify(self, keyvar):
        """ """
        [root, night, fname] = keyvar.getValue()
        args = [root, night, 'sps', fname]
        filepath = os.path.join(*args)
        return dict(filepath=filepath)

    def plot(self, filepath):
        """ """
        exp = geom.Exposure(filepath)
        ampIms, osIms, _ = exp.splitImage()
        clipped = sigma_clip(osIms, axis=2)
        levelPerRow = clipped.mean(axis=2)

        self.fig.suptitle(f'Serial Overscan {filepath}')

        for nAmp in range(8):
            ax = self.axes[nAmp]
            yi = levelPerRow[nAmp] + np.random.normal(size=levelPerRow.shape[1])
            medLevel, stdLevel = np.median(yi), np.std(yi)

            ax.plot(yi, label=f'l={round(medLevel)} +- {round(stdLevel, 2)}')
            ax.grid()
            ax.legend()
            ax.set_xlabel('Rows')
            ax.set_ylabel(f'a{nAmp}')
            ax.set_xlim(-10, 4600)
            ax.set_ylim(medLevel - 3, medLevel + 3)
