from importlib import reload

import pfsPlotActor.utils.pfi as pfiUtils
from pfsPlotActor.utils.convergence import plotConvergenceScatterAndHist

reload(pfiUtils)


class ConvergenceMapHist(pfiUtils.ConvergencePlot):
    units = dict(vmin='microns', vmax='microns')

    def initialize(self):
        """Initialize your axes and colorbar"""
        ax1 = [self.fig.add_subplot(121)]
        ax2 = [self.fig.add_subplot(122)]
        return ax1 + ax2

    def plot(self, latestVisitId, visitId=-1, nIter=-1, vmin=0, vmax=30, bins=30, minIter=3, showPercentiles='75,95'):
        """Plot the latest dataset."""
        ax1 = self.axes[0]
        ax2 = self.axes[1]

        # Get convergence dataframe default is latest.
        convergeData = self.selectData(latestVisitId, visitId=visitId)
        if not len(convergeData):
            return

        nIter = convergeData.iteration.max() if nIter == -1 else nIter

        # filter the dataframe for the iteration value.
        iterData = convergeData.query(f'iteration=={nIter}').reset_index(drop=True)
        if iterData.empty:
            return

        return plotConvergenceScatterAndHist(self, ax1, ax2, convergeData, iterData,
                                             vmin=vmin, vmax=vmax,
                                             bins=bins,
                                             minIter=minIter,
                                             showPercentiles=showPercentiles)
