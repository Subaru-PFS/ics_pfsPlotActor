import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.axes_grid1 import make_axes_locatable
from pfsPlotActor.utils.sgfm import calibModel


def plotConvergenceScatterAndHist(convergencePlot, ax1, ax2, convergeData, iterData, vmin=0, vmax=30, bins=30,
                                  minIter=3, showPercentiles='75,95'):
    fig = convergencePlot.fig
    [visitId] = convergeData.pfs_visit_id.unique()
    nIter = convergeData.iteration.max()
    pfsConfigDf = convergencePlot.loadPfsConfigFromDB(visitId)
    iterData = convergencePlot.addPfsConfigInfo(iterData, pfsConfigDf)

    # show broken cobras.
    bad = iterData.loc[convergencePlot.badIdx]
    ax1.scatter(calibModel.centers.real[bad['cobra_id'].values - 1],
                calibModel.centers.imag[bad['cobra_id'].values - 1], marker='x', color='k', s=20,
                alpha=0.5)

    # show moving cobras.
    iterData = convergencePlot.selectMovingCobras(iterData)

    # calculate distance from targets at this iteration.
    dx = iterData.pfi_center_x_mm - iterData.pfi_target_x_mm
    dy = iterData.pfi_center_y_mm - iterData.pfi_target_y_mm
    dist = np.hypot(dx, dy)

    # converting to microns
    dist *= 1000

    vmin = min(dist) if vmin == 'auto' else float(vmin)
    vmax = max(dist) if vmax == 'auto' else float(vmax)

    sc = ax1.scatter(calibModel.centers.real[iterData['cobra_id'].values - 1],
                     calibModel.centers.imag[iterData['cobra_id'].values - 1],
                     c=dist, marker='o', s=20, vmin=vmin, vmax=vmax)

    # Update or create colorbar
    colorbar = convergencePlot.colorbars.get(ax1, None)

    if colorbar is None:
        divider = make_axes_locatable(ax1)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        convergencePlot.colorbars[ax1] = fig.colorbar(sc, cax=cax)
    else:
        colorbar.update_normal(sc)

    # some labels
    ax1.set_xlabel("X (mm)")
    ax1.set_ylabel("Y (mm)")

    # label with the pfsvisit Id
    tString = f'Convergence Distance: pfsVisitId = {visitId:d}, iteration = {nIter:d}'
    ax1.set_title(tString)

    ax1.set_aspect('equal')
    ax1.format_coord = convergencePlot.cobraIdFiberIdFormatter

    convergeData = convergeData.query(f'iteration>={minIter}')

    cmap = plt.get_cmap('viridis')
    cmap = cmap(np.linspace(1.0, 0, len(convergeData.iteration.unique())))

    for i, (iterVal, iterData) in enumerate(convergeData.groupby('iteration')):
        iterData = convergencePlot.addPfsConfigInfo(iterData, pfsConfigDf).reset_index()
        # show moving cobras.
        iterData = convergencePlot.selectMovingCobras(iterData)

        dx = iterData.pfi_center_x_mm - iterData.pfi_target_x_mm
        dy = iterData.pfi_center_y_mm - iterData.pfi_target_y_mm
        dist = np.hypot(dx, dy)
        # converting to microns
        dist *= 1000

        n, bins, patches = ax2.hist(dist, alpha=0.6, histtype='step', linewidth=3,
                                    label=f'{iterVal}-th Iteration', bins=bins, range=(vmin, vmax),
                                    color=cmap[i])

    ax2.legend(loc='upper right')
    ax2.set_title(f"Distance to Target: pfsVisitId = {visitId:d}")
    ax2.set_xlabel("Distance (microns)")
    ax2.set_ylabel("N")
    ax2.set_aspect('auto')
    ax2.grid()

    # adding percentiles
    try:
        showPercentiles = list(map(int, showPercentiles.split(',')))
    except:
        showPercentiles = [75, 95]

    percentiles = np.percentile(dist, showPercentiles)
    ymin, ymax = ax2.get_ylim()

    for value, perc in zip(percentiles, showPercentiles):
        color = 'r' if perc == 95 and value > 10 else 'k'
        ax2.vlines(value, ymin, ymax, label=f'{perc}th : {value:.1f} microns', color=color, alpha=0.5)
        label = ax2.legend().get_texts()[-1]
        label.set_color(color)

    fig.tight_layout()

    return True
