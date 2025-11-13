import numpy as np
import pandas as pd
from mpl_toolkits.axes_grid1 import make_axes_locatable
from pfsPlotActor.utils.sgfm import sgfm, fiducials


def getPerFiducialRMS(fidsData):
    """
    Calculate RMS and displacement for fiducials.

    Parameters
    ----------
    fidsData : DataFrame
        Fiducial data.

    Returns
    -------
    DataFrame
        Fiducial RMS, displacement, and metadata.
    """
    fidsData['dx'] = np.zeros(len(fidsData), dtype=float)
    fidsData['dy'] = np.zeros(len(fidsData), dtype=float)
    fidsData['FIDUCIALS_OK'] = False

    # Calculate displacements
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


def getPerBrokenCobraRMS(convergeData):
    """
    Calculate RMS and displacement for broken cobras.

    Parameters
    ----------
    convergeData : DataFrame
        Convergence data.

    Returns
    -------
    DataFrame
        Broken cobra RMS, displacement, and metadata.
    """
    brokenMask = sgfm[~sgfm.FIBER_BROKEN_MASK & ~sgfm.COBRA_OK_MASK].cobraId
    brokenCobras = convergeData[convergeData.cobra_id.isin(brokenMask)].copy()

    # Ensure dx/dy columns exist with float dtype
    brokenCobras['dx'] = 0.0
    brokenCobras['dy'] = 0.0

    # Calculate displacements
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


def plotFiducialRMS(convergencePlot, ax1, ax2, convergeData, fidsData, vmin=0, vmax=15, addBrokenCobras=False,
                    showDisplacementAsArrow=False, bins=20, arrowSize='auto'):
    [visitId] = convergeData.pfs_visit_id.unique()
    nIter = convergeData.iteration.max()
    fig = convergencePlot.fig

    # Calculate RMS for fiducials and broken cobras
    perFiducialRMS = getPerFiducialRMS(fidsData)
    perBrokenCobraRMS = getPerBrokenCobraRMS(convergeData)

    merged = [perFiducialRMS, perBrokenCobraRMS] if addBrokenCobras else [perFiducialRMS]

    vmin = min([rmsVal.rms.min() for rmsVal in merged]) if vmin == 'auto' else float(vmin)
    vmax = max([rmsVal.rms.max() for rmsVal in merged]) if vmax == 'auto' else float(vmax)

    # Scatter plot for fiducials
    sc = ax1.scatter(perFiducialRMS.x_mm, perFiducialRMS.y_mm, c=perFiducialRMS.rms, marker='D', s=40, vmin=vmin,
                     vmax=vmax)

    # Add arrows for displacement
    if showDisplacementAsArrow:
        maxDisplacement = int(np.percentile(np.concatenate([rmsVal.dist.to_numpy() for rmsVal in merged]), 90))
        arrowSize = maxDisplacement if arrowSize == 'auto' else int(arrowSize)
        scale = 1000 * arrowSize / 100

        # Add arrows for fiducials
        Q = ax1.quiver(perFiducialRMS.x_mm, perFiducialRMS.y_mm, perFiducialRMS.dx, perFiducialRMS.dy, alpha=0.5,
                       scale=scale)
        ax1.quiverkey(Q, X=0.85, Y=0.1, U=arrowSize, label=f'{arrowSize} microns', labelpos='E', coordinates='axes')

    # Update or create colorbar
    if convergencePlot.colorbar is None:
        divider = make_axes_locatable(ax1)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        convergencePlot.colorbar = fig.colorbar(sc, cax=cax)
    else:
        convergencePlot.colorbar.update_normal(sc)

    # Histogram of RMS
    fiducialMedianRMS = perFiducialRMS.rms.median()
    ax2.hist(perFiducialRMS.rms, bins=bins, range=(vmin, vmax), alpha=0.7)

    # Add a vertical line for the median RMS of fiducials
    ax2.axvline(fiducialMedianRMS, color='blue', linestyle='--', linewidth=2,
                label=f'Median Fiducial RMS = {fiducialMedianRMS:.1f} μm')

    # Add plots for broken cobras
    if addBrokenCobras:
        ax1.scatter(perBrokenCobraRMS.x, perBrokenCobraRMS.y, c=perBrokenCobraRMS.rms, marker='o', s=40,
                    vmin=vmin, vmax=vmax)
        if showDisplacementAsArrow:
            ax1.quiver(perBrokenCobraRMS.x, perBrokenCobraRMS.y, perBrokenCobraRMS.dx, perBrokenCobraRMS.dy,
                       alpha=0.5, scale=scale)

        brokenCobrasMedianRMS = perBrokenCobraRMS.rms.median()
        ax2.hist(perBrokenCobraRMS.rms, bins=bins, range=(vmin, vmax), alpha=0.7)

        # Add a vertical line for the median RMS of broken cobras
        ax2.axvline(brokenCobrasMedianRMS, color='orange', linestyle='--', linewidth=2,
                    label=f'Median Broken Cobra RMS = {brokenCobrasMedianRMS:.1f} μm')

    # Labels and titles
    ax1.set_xlabel("X (mm)")
    ax1.set_ylabel("Y (mm)")
    ax1.set_title(f'RMS of position: pfsVisitId = {visitId:d}, {nIter:d} iterations')
    ax1.set_aspect('equal')

    # Customize the histogram appearance
    ax2.legend()
    ax2.set_xlabel('RMS (microns)')
    ax2.set_ylabel("N")
    ax2.set_title("Distribution of RMS")
    ax2.grid(True, linestyle='--', alpha=0.6)  # Add grid for better readability

    fig.tight_layout()

    return True
