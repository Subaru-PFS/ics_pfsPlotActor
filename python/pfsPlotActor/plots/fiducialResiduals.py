from importlib import reload

import numpy as np
import pandas as pd
import pfsPlotActor.utils.pfi as pfiUtils
from pfsPlotActor.utils.sgfm import fiducials, sgfm

reload(pfiUtils)


def perFiducialRMS(fidsData):
    """RMS, mean displacement and metadata per fiducial, in microns."""
    fidsData['dx'] = np.zeros(len(fidsData), dtype=float)
    fidsData['dy'] = np.zeros(len(fidsData), dtype=float)
    fidsData['FIDUCIALS_OK'] = False

    for iteration, dfi in fidsData.groupby('iteration'):
        dfi = dfi.sort_values('fiducial_fiber_id')
        index = dfi.fiducial_fiber_id.to_numpy() - 1

        fidsData.loc[dfi.index, 'dx'] = fiducials.x_mm.to_numpy()[index] - dfi.pfi_center_x_mm.to_numpy()
        fidsData.loc[dfi.index, 'dy'] = fiducials.y_mm.to_numpy()[index] - dfi.pfi_center_y_mm.to_numpy()
        fidsData.loc[dfi.index, 'FIDUCIALS_OK'] = fiducials.FIDUCIALS_OK.to_numpy()[index]

    fidsData['dist'] = np.hypot(fidsData.dx.to_numpy(), fidsData.dy.to_numpy())

    rmsVal = pd.DataFrame([(fid, 1000 * np.std(dfi.dist, ddof=1), 1000 * np.mean(dfi.dx), 1000 * np.mean(dfi.dy),
                            1000 * np.mean(dfi.dist)) for fid, dfi in fidsData.groupby('fiducial_fiber_id')],
                          columns=['fiducialId', 'rms', 'dx', 'dy', 'dist'])

    return pd.merge(rmsVal, fiducials, on='fiducialId', how='inner')


def perBrokenCobraRMS(convergeData):
    """RMS, mean displacement and metadata per broken cobra, in microns."""
    brokenMask = sgfm[~sgfm.FIBER_BROKEN_MASK & ~sgfm.COBRA_OK_MASK].cobraId
    brokenCobras = convergeData[convergeData.cobra_id.isin(brokenMask)].copy()

    brokenCobras['dx'] = 0.0
    brokenCobras['dy'] = 0.0

    for iteration, dfi in brokenCobras.groupby('iteration'):
        cobraIndices = dfi.cobra_id.to_numpy() - 1
        xDiff = sgfm.x.to_numpy()[cobraIndices] - dfi.pfi_center_x_mm.to_numpy()
        yDiff = sgfm.y.to_numpy()[cobraIndices] - dfi.pfi_center_y_mm.to_numpy()

        brokenCobras.loc[dfi.index, 'dx'] = xDiff
        brokenCobras.loc[dfi.index, 'dy'] = yDiff

    brokenCobras['dist'] = np.hypot(brokenCobras['dx'], brokenCobras['dy'])

    rmsVal = pd.DataFrame(
        [(cobraId,
          1000 * np.std(dfi.dist, ddof=1),
          1000 * np.mean(dfi.dx),
          1000 * np.mean(dfi.dy),
          1000 * np.mean(dfi.dist))
         for cobraId, dfi in brokenCobras.groupby('cobra_id')],
        columns=['cobraId', 'rms', 'dx', 'dy', 'dist']
    )

    return pd.merge(rmsVal, sgfm[['cobraId', 'fiberId', 'x', 'y']], on='cobraId', how='inner')


def drawFiducialRMS(plot, ax1, ax2, latestVisitId, visitId=-1, vmin=0, vmax=15, addBrokenCobras=False,
                    showDisplacementAsArrow=False, bins=20, arrowSize='auto'):
    """Draw the fiducial RMS map on ax1 and the RMS histogram on ax2.

    A free function so both FiducialResiduals and the combined plot can call it; ``plot`` is the
    LivePlot providing selectData, getFiducialData, updateColorbar and cobraIdFiberIdFormatter.
    The caller owns the figure and its layout.

    vmin, vmax : colorbar limits (microns). addBrokenCobras: also show broken cobras.
    showDisplacementAsArrow: overlay displacement vectors. bins: histogram bins. arrowSize:
    arrow scale in microns, or 'auto'.
    """
    convergeData = plot.selectData(latestVisitId, visitId=visitId)
    if not len(convergeData):
        return

    [visitId] = convergeData.pfs_visit_id.unique()
    nIter = convergeData.iteration.max()

    fidsData = plot.getFiducialData(visitId)
    if not len(fidsData):
        return

    fiducialRMS = perFiducialRMS(fidsData)
    brokenCobraRMS = perBrokenCobraRMS(convergeData)

    merged = [fiducialRMS, brokenCobraRMS] if addBrokenCobras else [fiducialRMS]

    vmin = min([rmsVal.rms.min() for rmsVal in merged]) if vmin == 'auto' else float(vmin)
    vmax = max([rmsVal.rms.max() for rmsVal in merged]) if vmax == 'auto' else float(vmax)

    sc = ax1.scatter(fiducialRMS.x_mm, fiducialRMS.y_mm, c=fiducialRMS.rms, marker='D', s=40, vmin=vmin, vmax=vmax)

    if showDisplacementAsArrow:
        maxDisplacement = int(np.percentile(np.concatenate([rmsVal.dist.to_numpy() for rmsVal in merged]), 90))
        arrowSize = maxDisplacement if arrowSize == 'auto' else int(arrowSize)
        scale = 1000 * arrowSize / 100

        Q = ax1.quiver(fiducialRMS.x_mm, fiducialRMS.y_mm, fiducialRMS.dx, fiducialRMS.dy, alpha=0.5, scale=scale)
        ax1.quiverkey(Q, X=0.85, Y=0.1, U=arrowSize, label=f'{arrowSize} microns', labelpos='E', coordinates='axes')

    plot.updateColorbar('fiducial', ax1, sc)

    fiducialMedianRMS = fiducialRMS.rms.median()
    ax2.hist(fiducialRMS.rms, bins=bins, range=(vmin, vmax), alpha=0.7)
    ax2.axvline(fiducialMedianRMS, color='blue', linestyle='--', linewidth=2,
                label=f'Median Fiducial RMS = {fiducialMedianRMS:.1f} μm')

    if addBrokenCobras:
        ax1.scatter(brokenCobraRMS.x, brokenCobraRMS.y, c=brokenCobraRMS.rms, marker='o', s=40, vmin=vmin, vmax=vmax)
        if showDisplacementAsArrow:
            ax1.quiver(brokenCobraRMS.x, brokenCobraRMS.y, brokenCobraRMS.dx, brokenCobraRMS.dy,
                       alpha=0.5, scale=scale)

        brokenCobrasMedianRMS = brokenCobraRMS.rms.median()
        ax2.hist(brokenCobraRMS.rms, bins=bins, range=(vmin, vmax), alpha=0.7)
        ax2.axvline(brokenCobrasMedianRMS, color='orange', linestyle='--', linewidth=2,
                    label=f'Median Broken Cobra RMS = {brokenCobrasMedianRMS:.1f} μm')

    ax1.set_xlabel("X (mm)")
    ax1.set_ylabel("Y (mm)")
    ax1.set_title(f'Fiducial RMS: visit {visitId:d}, {nIter:d} iter')
    ax1.set_aspect('equal')
    ax1.format_coord = plot.cobraIdFiberIdFormatter

    ax2.legend()
    ax2.set_xlabel('RMS (microns)')
    ax2.set_ylabel("N")
    ax2.set_title("RMS distribution")
    ax2.grid(True, linestyle='--', alpha=0.6)

    return True


class FiducialResiduals(pfiUtils.ConvergencePlot):
    """Plot fiducial and broken cobra residuals for PFS data."""

    units = dict(vmin='microns', vmax='microns', arrowSize='microns')

    def initialize(self):
        """Initialize plot axes and colorbar."""
        ax1 = self.fig.add_subplot(121)  # Scatter plot of residuals
        ax2 = self.fig.add_subplot(122)  # Histogram of RMS
        return [ax1, ax2]

    def plot(self, latestVisitId, visitId=-1, vmin=0, vmax=15, addBrokenCobras=False,
             showDisplacementAsArrow=False, bins=20, arrowSize='auto'):
        """Plot the latest dataset."""
        plotted = drawFiducialRMS(self, self.axes[0], self.axes[1], latestVisitId, visitId=visitId,
                                  vmin=vmin, vmax=vmax, addBrokenCobras=addBrokenCobras,
                                  showDisplacementAsArrow=showDisplacementAsArrow, bins=bins, arrowSize=arrowSize)
        self.fig.tight_layout()
        return plotted
