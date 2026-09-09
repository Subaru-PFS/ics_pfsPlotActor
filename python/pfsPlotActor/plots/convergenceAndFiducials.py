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
        """Convergence map and histogram over the full height, fiducial RMS pair stacked beside.

        One subfigure per quantity, so each carries its own heading and matplotlib keeps the two
        pairs apart. The fiducial RMS is the sparser measurement, so it is stacked into a narrow
        column and the convergence pair takes the width that frees. The constrained layout engine
        re-runs on every draw, so the panels follow a window resize instead of holding the
        geometry they were first drawn with.
        """
        self.cumAxis = None
        self.fig.set_layout_engine('constrained')
        self.subFigs = self.fig.subfigures(1, 2, width_ratios=[3.0, 1.0], wspace=0.02)

        axes = list(self.subFigs[0].subplots(1, 2, width_ratios=[1.0, 0.85]))
        axes.extend(self.subFigs[1].subplots(2, 1, height_ratios=[1.6, 1.0]))
        return axes

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
        # the convergence panels set the run on display; the fiducial RMS spans the whole run.
        self.decorateTitles(("Distance to target", "Position RMS"), convergence)
        return bool(convergence or fiducials)
