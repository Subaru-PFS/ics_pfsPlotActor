from importlib import reload

import pfsPlotActor.utils.pfi as pfiUtils

reload(pfiUtils)

from importlib import reload

import pfsPlotActor.utils.pfi as pfiUtils
from pfsPlotActor.utils.fiducials import plotFiducialRMS

reload(pfiUtils)


class FiducialResiduals(pfiUtils.ConvergencePlot):
    """
    Plot fiducial and broken cobra residuals for PFS data.
    """

    units = dict(vmin='microns', vmax='microns', arrowSize='microns')

    def initialize(self):
        """
        Initialize plot axes and colorbar.
        """
        ax1 = self.fig.add_subplot(121)  # Scatter plot of residuals
        ax2 = self.fig.add_subplot(122)  # Histogram of RMS
        return [ax1, ax2]

    def plot(self, latestVisitId, visitId=-1, vmin=0, vmax=15, addBrokenCobras=False,
             showDisplacementAsArrow=False, bins=20, arrowSize='auto'):
        """
        Plot fiducial and cobra residuals with optional arrows and histogram.

        Parameters
        ----------
        convergeData : DataFrame
            Dataframe with convergence information.
        visitId : int
            Visit ID to filter data.
        vmin, vmax : float
            Colorbar limits.
        addBrokenCobras : bool
            Include broken cobras in the plot.
        showDisplacementAsArrow : bool
            Display displacement vectors as arrows.
        bins : int
            Number of bins for histogram.
        arrowSize : float
            Size of the arrows in microns.
        """
        ax1, ax2 = self.axes

        # Get convergence dataframe default is latest.
        convergeData = self.selectData(latestVisitId, visitId=visitId)

        if not len(convergeData):
            return

        # Get fiducial data
        fidsData = self.getFiducialData(visitId)

        if not len(fidsData):
            return

        return plotFiducialRMS(self, ax1, ax2, convergeData, fidsData,
                               vmin=vmin, vmax=vmax,
                               addBrokenCobras=addBrokenCobras,
                               showDisplacementAsArrow=showDisplacementAsArrow,
                               bins=bins,
                               arrowSize=arrowSize)
