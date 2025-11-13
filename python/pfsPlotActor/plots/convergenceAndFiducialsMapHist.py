from importlib import reload

import pfsPlotActor.utils.pfi as pfiUtils
from pfsPlotActor.utils.convergence import plotConvergenceScatterAndHist
from pfsPlotActor.utils.fiducials import plotFiducialRMS

reload(pfiUtils)


class ConvergenceAndFiducialsMapHist(pfiUtils.ConvergencePlot):
    units = dict(vmin='microns', vmax='microns', rmsMin='microns', rmsMax='microns', arrowSize='microns')

    def initialize(self):
        """Initialize your axes and colorbar"""
        axes = [self.fig.add_subplot(141),
                self.fig.add_subplot(142),
                self.fig.add_subplot(143),
                self.fig.add_subplot(144)]
        return axes

    def plot(self, latestVisitId, visitId=-1, nIter=-1, vmin=0, vmax=30, bins=30, minIter=3, showPercentiles='75,95',
             rmsMin=0, rmsMax=15, rmsBins=20, addBrokenCobras=False, showDisplacementAsArrow=False, arrowSize='auto'):
        """Plot the latest dataset."""
        ax1, ax2, ax3, ax4 = self.axes

        # Get convergence dataframe default is latest.
        convergeData = self.selectData(latestVisitId, visitId=visitId)
        if not len(convergeData):
            return

        nIter = convergeData.iteration.max() if nIter == -1 else nIter

        # filter the dataframe for the iteration value.
        iterData = convergeData.query(f'iteration=={nIter}').reset_index(drop=True)
        if iterData.empty:
            return

        doPlot1 = plotConvergenceScatterAndHist(self, ax1, ax2, convergeData, iterData,
                                                vmin=vmin, vmax=vmax,
                                                bins=bins,
                                                minIter=minIter,
                                                showPercentiles=showPercentiles)

        # Get fiducial data
        fidsData = self.getFiducialData(visitId)

        if not len(fidsData):
            return

        doPlot2 = plotFiducialRMS(self, ax3, ax4, convergeData, fidsData,
                                  vmin=rmsMin, vmax=rmsMax,
                                  addBrokenCobras=addBrokenCobras,
                                  showDisplacementAsArrow=showDisplacementAsArrow,
                                  bins=rmsBins,
                                  arrowSize=arrowSize)

        return doPlot1 or doPlot2
