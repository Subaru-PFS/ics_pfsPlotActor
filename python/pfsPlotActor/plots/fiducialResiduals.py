from importlib import reload

import numpy as np
import pandas as pd
import pfsPlotActor.utils.pfi as pfiUtils
from pfsPlotActor.utils.sgfm import fiducials, sgfm

reload(pfiUtils)


def matchedEveryIteration(data, pointColumn):
    """The rows of the points that were matched in every one of the iterations present.

    A point missing from some iterations would have its position rms taken over fewer, and
    contribute fewer residuals than its neighbours, so it is left out rather than compared
    against points measured more often.
    """
    matched = data[data.pfi_center_x_mm.notna()]
    counts = matched.groupby(pointColumn).pfi_center_x_mm.count()
    complete = counts[counts == data.iteration.nunique()].index
    return matched[matched[pointColumn].isin(complete)]


def positionRMS(measuredX, measuredY):
    """Scatter of one point's measured positions about their own mean: mm in, microns out.

    It says how repeatable the measurement is, without reference to where the point was
    expected, so an out of date calibration cannot move it.
    """
    if len(measuredX) < 2:
        return np.nan

    spread = (measuredX - measuredX.mean()) ** 2 + (measuredY - measuredY.mean()) ** 2
    return 1e3 * np.sqrt(spread.sum() / (len(measuredX) - 1))


def pointStatistics(data, pointColumn, expectedX, expectedY, columns):
    """Measure each point of ``data`` against where it was expected, in microns.

    ``expectedX``/``expectedY`` are per row, in mm. Returns (rows, perPoint): ``rows`` is
    ``data`` with the residual of every point at every iteration, and ``perPoint`` holds one
    position rms and one mean residual per point.
    """
    rows = data.copy()
    rows['dx'] = 1e3 * (expectedX - rows.pfi_center_x_mm.to_numpy(dtype=float))
    rows['dy'] = 1e3 * (expectedY - rows.pfi_center_y_mm.to_numpy(dtype=float))
    rows['residual'] = np.hypot(rows.dx.to_numpy(), rows.dy.to_numpy())

    perPoint = pd.DataFrame(
        [(point,
          positionRMS(group.pfi_center_x_mm.to_numpy(dtype=float),
                      group.pfi_center_y_mm.to_numpy(dtype=float)),
          group.dx.mean(), group.dy.mean())
         for point, group in rows.groupby(pointColumn)],
        columns=columns + ['rms', 'dx', 'dy'])

    return rows, perPoint


def perFiducialRMS(fidsData):
    """Position rms and transform residuals of the fiducials matched at every iteration.

    The residual is measured against the fiducial's nominal position, so it is what the mcs to
    pfi transform left behind. Returns (rows, perFiducial); see pointStatistics.
    """
    fidsData = matchedEveryIteration(fidsData, 'fiducial_fiber_id')
    index = fidsData.fiducial_fiber_id.to_numpy() - 1

    rows, perFiducial = pointStatistics(fidsData, 'fiducial_fiber_id',
                                        fiducials.x_mm.to_numpy()[index],
                                        fiducials.y_mm.to_numpy()[index], columns=['fiducialId'])
    return rows, pd.merge(perFiducial, fiducials, on='fiducialId', how='inner')


def perBrokenCobraRMS(convergeData):
    """Position rms and residuals of the broken cobras seen at every iteration.

    A broken cobra does not move, so its position repeats the way a fiducial's does, and
    cobra_target records where it is expected to be found. Measuring against that, rather than
    against the centre its arm holds it a millimetre or so away from, puts its residual on the
    same footing as a fiducial's.
    """
    brokenMask = sgfm[~sgfm.FIBER_BROKEN_MASK & ~sgfm.COBRA_OK_MASK].cobraId
    brokenCobras = matchedEveryIteration(convergeData[convergeData.cobra_id.isin(brokenMask)],
                                         'cobra_id')

    rows, perCobra = pointStatistics(brokenCobras, 'cobra_id',
                                     brokenCobras.pfi_target_x_mm.to_numpy(dtype=float),
                                     brokenCobras.pfi_target_y_mm.to_numpy(dtype=float),
                                     columns=['cobraId'])
    return rows, pd.merge(perCobra, sgfm[['cobraId', 'fiberId', 'x', 'y']], on='cobraId', how='inner')


def matchedText(fiducialCount, positionRMS, residualMean, residualSigma):
    """The fiducials carrying the statistics, then what each histogram came to.

    ``fiducialCount`` are the ones matched at every iteration, which is the population of both
    histograms: one rms each, and one residual each per iteration. Broken and bad fiducials are
    not expected to match at all, so they are not counted as missing. The values are the ones
    the histograms are marked with, rounded to the micron the fiducials are good to, and named
    apart because they are not the same statistic: a median rms over the fiducials, then the
    centre and width of the gaussian laid over every residual measured.
    """
    bold = pfiUtils.ConvergencePlot.boldText
    # a line each, saying what the number is of: the two are easily taken for one another.
    lines = [f'matched: {bold(str(fiducialCount))}/{int(fiducials.FIDUCIALS_OK.sum())}']

    if np.isfinite(positionRMS):
        lines.append(f'Stability per fiducial: {bold(f"{positionRMS:.0f}")} µm (median)')
    if np.isfinite(residualMean):
        spread = f' ± {bold(f"{residualSigma:.0f}")}' if np.isfinite(residualSigma) else ''
        lines.append(f'Residual vs nominal: {bold(f"{residualMean:.0f}")}{spread} µm (gaussian)')

    return '\n'.join(lines)


def markValue(ax, value, color):
    """Mark ``value`` on ``ax`` and label it, in the room a legend would not fit into."""
    if not np.isfinite(value):
        return

    ax.axvline(value, color=color, linestyle='--', linewidth=2)
    ax.annotate(f'{value:.1f}', xy=(value, 1), xycoords=('data', 'axes fraction'),
                xytext=(3, -3), textcoords='offset points', ha='left', va='top',
                fontsize=8, color=color)


def gaussianOverlay(ax, values, edges, color):
    """Lay the gaussian of the same mean, spread and count over a histogram of ``values``.

    Returns (mean, sigma), nan when there is nothing to draw. The curve carries the area of the
    bars it lies over, being scaled by their count and width. It names itself in a legend rather
    than against the axis, unlike the bare line the other histogram carries: a curve fitted to a
    distribution is not the single number that one marks.
    """
    values = values[np.isfinite(values)]
    if len(values) < 2:
        return np.nan, np.nan

    mean, sigma = values.mean(), values.std(ddof=1)
    if not sigma:
        return mean, sigma

    xs = np.linspace(edges[0], edges[-1], 200)
    ys = (len(values) * (edges[1] - edges[0]) / (sigma * np.sqrt(2 * np.pi))
          * np.exp(-0.5 * ((xs - mean) / sigma) ** 2))

    ax.plot(xs, ys, color=color, linewidth=1.5, label=f'{mean:.1f} ± {sigma:.1f} µm')
    ax.legend(loc='upper right', fontsize=7, framealpha=0.7, handlelength=1.2)
    return mean, sigma


def saturated(values, low, high):
    """The finite ``values``, pulled inside [low, high] rather than left outside it.

    A histogram given a range drops whatever falls beyond it, while the map draws such a point
    at the end of its colour scale. Saturating the same way keeps a point that shows on the map
    from going missing in the histogram, at the price of a pile up in the end bin.
    """
    values = values[np.isfinite(values)]
    return np.clip(values, low, high)


def drawFiducialRMS(plot, mapAxes, rmsAxes, residualAxes, latestVisitId, visitId=-1, vmin=0, vmax=15,
                    addBrokenCobras='none', showTransformResidualArrows=True, bins=20,
                    arrowSize='auto', residualTicksRight=False):
    """Draw the fiducial map on mapAxes, then a histogram of each quantity it carries.

    A free function so both FiducialResiduals and the combined plot can call it; ``plot`` is the
    LivePlot providing selectData, getFiducialData, updateColorbar and cobraIdFiberIdFormatter.
    The caller owns the figure, its layout and its titles. Returns the (visit, iteration count)
    the statistics were taken over, or None when there is nothing to show.

    The two histograms count different things. rmsAxes holds one position rms per fiducial, each
    taken over the iterations, marked with their median. residualAxes holds every fiducial's
    residual at every iteration, marked with their median over the interquartile range, drawn
    unalike so the two are not read as the same statistic. The map is coloured by position rms
    and its arrows draw the mean residual.

    vmin, vmax bound the rms in microns, and a point beyond them saturates rather than going
    missing; the residuals frame themselves. addBrokenCobras measures the broken cobras the same
    way: 'all' of them, only the 'stable' ones, being those repeating within the colour scale, or
    'none'. bins: histogram bins. arrowSize: arrow scale in microns, or 'auto'.
    residualTicksRight: hang the residual histogram's axis on its right, for a caller that puts
    the two side by side.
    """
    plot.fiducialSummary = ''
    # the tweak widget sends the choice it is set to, but calling plot() directly leaves the
    # signature default, which for a combo is the whole list of choices.
    addBrokenCobras = addBrokenCobras[0] if isinstance(addBrokenCobras, tuple) else addBrokenCobras

    convergeData = plot.selectData(latestVisitId, visitId=visitId)
    if not len(convergeData):
        return

    [visitId] = convergeData.pfs_visit_id.unique()
    convCount, __ = plot.convergenceCount(convergeData, visitId)

    fidsData = plot.getFiducialData(visitId)
    if not len(fidsData):
        return

    fiducialRows, fiducialRMS = perFiducialRMS(fidsData)
    brokenRows, brokenCobraRMS = perBrokenCobraRMS(convergeData)

    # 'stable' is measured against the colour scale, so the scale cannot depend on it in turn.
    merged = [fiducialRMS, brokenCobraRMS] if addBrokenCobras == 'all' else [fiducialRMS]

    vmin = min([rmsVal.rms.min() for rmsVal in merged]) if vmin == 'auto' else float(vmin)
    vmax = max([rmsVal.rms.max() for rmsVal in merged]) if vmax == 'auto' else float(vmax)

    if addBrokenCobras == 'stable':
        # one that moves further than the colour scale runs is not parked, it is drifting, and
        # its mean position is not somewhere it ever was.
        steady = brokenCobraRMS.rms <= vmax
        brokenCobraRMS = brokenCobraRMS[steady]
        brokenRows = brokenRows[brokenRows.cobra_id.isin(brokenCobraRMS.cobraId)]

    showBroken = addBrokenCobras != 'none' and len(brokenCobraRMS)

    sc = mapAxes.scatter(fiducialRMS.x_mm, fiducialRMS.y_mm, c=fiducialRMS.rms, marker='D', s=40,
                         vmin=vmin, vmax=vmax)

    shownRows = [fiducialRows, brokenRows] if showBroken else [fiducialRows]
    residual = np.concatenate([rows.residual.to_numpy(dtype=float) for rows in shownRows])
    residual = residual[np.isfinite(residual)]

    if showTransformResidualArrows:
        if arrowSize == 'auto':
            arrowSize = int(np.percentile(residual, 90)) if len(residual) else 0
        else:
            arrowSize = int(arrowSize)
        # quiver divides by the scale, so sub-micron residuals still need a whole micron.
        arrowSize = max(arrowSize, 1)
        scale = 1000 * arrowSize / 100

        Q = mapAxes.quiver(fiducialRMS.x_mm, fiducialRMS.y_mm, fiducialRMS.dx, fiducialRMS.dy,
                           alpha=0.5, scale=scale)
        mapAxes.quiverkey(Q, X=0.85, Y=0.1, U=arrowSize, label=f'{arrowSize} µm', labelpos='E',
                          coordinates='axes')

    plot.updateColorbar('fiducial', mapAxes, sc, label='Stability (µm)')

    positionRMS = np.nanmedian(fiducialRMS.rms.to_numpy(dtype=float))
    rmsAxes.hist(saturated(fiducialRMS.rms.to_numpy(dtype=float), vmin, vmax), bins=bins,
                 range=(vmin, vmax), alpha=0.7)
    markValue(rmsAxes, positionRMS, 'blue')

    fiducialResidual = fiducialRows.residual.to_numpy(dtype=float)
    fiducialResidual = fiducialResidual[np.isfinite(fiducialResidual)]
    vmaxResidual = float(fiducialResidual.max()) if len(fiducialResidual) else 1.0
    __, edges, __ = residualAxes.hist(fiducialResidual, bins=bins, range=(0, vmaxResidual),
                                      alpha=0.7)
    residualMean, residualSigma = gaussianOverlay(residualAxes, fiducialResidual, edges, 'navy')

    if showBroken:
        mapAxes.scatter(brokenCobraRMS.x, brokenCobraRMS.y, c=brokenCobraRMS.rms, marker='o', s=40,
                        vmin=vmin, vmax=vmax)
        rmsAxes.hist(saturated(brokenCobraRMS.rms.to_numpy(dtype=float), vmin, vmax), bins=bins,
                     range=(vmin, vmax), alpha=0.7)
        markValue(rmsAxes, np.nanmedian(brokenCobraRMS.rms.to_numpy(dtype=float)), 'orange')

        brokenResidual = brokenRows.residual.to_numpy(dtype=float)
        residualAxes.hist(saturated(brokenResidual, 0, vmaxResidual), bins=bins,
                          range=(0, vmaxResidual), alpha=0.7)

        if showTransformResidualArrows:
            mapAxes.quiver(brokenCobraRMS.x, brokenCobraRMS.y, brokenCobraRMS.dx, brokenCobraRMS.dy,
                           alpha=0.5, scale=scale)

    mapAxes.set_xlabel("X (mm)")
    mapAxes.set_ylabel("Y (mm)")
    mapAxes.set_aspect('equal')
    mapAxes.format_coord = plot.cobraIdFiberIdFormatter

    for axes, label, limits in ((rmsAxes, 'Stability (µm)', (vmin, vmax)),
                                (residualAxes, 'Residual (µm)', (0, vmaxResidual))):
        axes.set_xlabel(label)
        axes.set_ylabel("N")
        # hold the histogram's own range, which a marker outside it would stretch.
        axes.set_xlim(*limits)
        axes.grid(True, linestyle='--', alpha=0.6)

    if residualTicksRight:
        # set here rather than once with the axes: cla() puts the axis back on the left before
        # every draw.
        residualAxes.yaxis.tick_right()
        residualAxes.yaxis.set_label_position('right')

    plot.fiducialSummary = matchedText(len(fiducialRMS), positionRMS, residualMean,
                                      residualSigma)

    return int(visitId), convCount


def fiducialHeading(plot):
    """The quantity name, with how many matched beside it and what they came to underneath."""
    heading = plot.boldText("Fiducials")
    if not plot.fiducialSummary:
        return heading

    matched, *achieved = plot.fiducialSummary.split('\n')
    return '\n'.join([f'{heading}   {matched}'] + achieved)


class FiducialResiduals(pfiUtils.ConvergencePlot):
    """Plot fiducial and broken cobra residuals for PFS data."""

    units = dict(vmin='µm', vmax='µm', arrowSize='µm')

    def initialize(self):
        """Map over the full height, the histogram of each quantity it carries stacked beside."""
        subFig = self.singleSubFigure()
        grid = subFig.add_gridspec(2, 2, width_ratios=[1.0, 0.85], hspace=0.03)
        return [subFig.add_subplot(grid[:, 0]),
                subFig.add_subplot(grid[0, 1]),
                subFig.add_subplot(grid[1, 1])]

    def plot(self, latestVisitId, visitId=-1, vmin=0, vmax=15,
             addBrokenCobras=('none', 'stable', 'all'),
             showTransformResidualArrows=True, bins=20, arrowSize='auto'):
        """Plot the latest dataset."""
        shown = drawFiducialRMS(self, self.axes[0], self.axes[1], self.axes[2], latestVisitId,
                                visitId=visitId, vmin=vmin, vmax=vmax, addBrokenCobras=addBrokenCobras,
                                showTransformResidualArrows=showTransformResidualArrows, bins=bins,
                                arrowSize=arrowSize)
        self.decorateTitles((fiducialHeading(self),), shown)
        return bool(shown)
