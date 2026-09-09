from importlib import reload

import pfsPlotActor.plots.convergenceMapHist as convergenceMapHist
import pfsPlotActor.plots.fiducialResiduals as fiducialResiduals

reload(convergenceMapHist)
reload(fiducialResiduals)


class ConvergenceAndFiducials(convergenceMapHist.ConvergenceMapHist):
    """Convergence map and histogram alongside the fiducial RMS map and histogram.

    The two are almost always looked at together, so this shows all four panels in one figure.
    It reuses ConvergenceMapHist.drawConvergence for the left pair and fiducialResiduals'
    drawFiducialRMS for the right pair, leaving both standalone plots untouched.
    """

    units = dict(vmin='microns', vmax='microns', vminRMS='microns', vmaxRMS='microns',
                 arrowSize='microns')

    def initialize(self):
        """Four panels in a row: convergence map and histogram, then fiducial RMS map and histogram.

        Maps get more width than the histograms (16:9 screen).
        """
        self.cumAxis = None
        gridSpec = self.fig.add_gridspec(1, 4, width_ratios=[1.0, 0.75, 1.0, 0.75])
        return [self.fig.add_subplot(gridSpec[0, i]) for i in range(4)]

    def plot(self, latestVisitId, visitId=-1, nIter=-1, vmin=0, vmax=30, bins=30, minIter=3,
             showPercentiles='75,95', showCumulative=False,
             vminRMS=0, vmaxRMS=15, binsRMS=20, addBrokenCobras=False,
             showDisplacementAsArrow=False, arrowSize='auto'):
        """Plot the latest dataset."""
        convergence = self.drawConvergence(self.axes[0], self.axes[1], latestVisitId, visitId=visitId,
                                           nIter=nIter, vmin=vmin, vmax=vmax, bins=bins, minIter=minIter,
                                           showPercentiles=showPercentiles, showCumulative=showCumulative)
        fiducials = fiducialResiduals.drawFiducialRMS(self, self.axes[2], self.axes[3], latestVisitId,
                                                      visitId=visitId, vmin=vminRMS, vmax=vmaxRMS,
                                                      addBrokenCobras=addBrokenCobras,
                                                      showDisplacementAsArrow=showDisplacementAsArrow,
                                                      bins=binsRMS, arrowSize=arrowSize)
        self.fig.tight_layout()
        return bool(convergence or fiducials)
