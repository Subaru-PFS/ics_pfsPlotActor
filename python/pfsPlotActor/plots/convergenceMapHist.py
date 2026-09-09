from importlib import reload

import matplotlib.pyplot as plt
import numpy as np
import pfsPlotActor.utils.pfi as pfiUtils
from pfs.datamodel import TargetType, FiberStatus, CobraCommand
from pfsPlotActor.utils.sgfm import calibModel

reload(pfiUtils)


class ConvergenceMapHist(pfiUtils.ConvergencePlot):
    units = dict(vmin='microns', vmax='microns')

    def initialize(self):
        """Initialize your axes and colorbar"""
        self.cumAxis = None
        return list(self.singleSubFigure().subplots(1, 2, width_ratios=[1.0, 0.85]))

    def plot(self, latestVisitId, visitId=-1, nIter=-1, vmin=0, vmax=30, bins=30, minIter=3,
             showPercentiles='75,95', showCumulative=False):
        """Plot the latest dataset."""
        shown = self.drawConvergence(self.axes[0], self.axes[1], latestVisitId, visitId=visitId,
                                     nIter=nIter, vmin=vmin, vmax=vmax, bins=bins, minIter=minIter,
                                     showPercentiles=showPercentiles, showCumulative=showCumulative)
        self.decorateTitles(("Distance to target",), shown)
        return bool(shown)

    def drawConvergence(self, ax1, ax2, latestVisitId, visitId=-1, nIter=-1, vmin=0, vmax=30,
                        bins=30, minIter=3, showPercentiles='75,95', showCumulative=False):
        """Draw the convergence map on ax1 and the per-iteration distance histogram on ax2.

        Shared by the standalone plot and the combined convergence/fiducials plot; the caller
        owns the figure, its layout and its titles. Returns the (visit, iteration) drawn, or
        None when there is nothing to show.
        """
        # Get convergence dataframe default is latest.
        convergeData = self.selectData(latestVisitId, visitId=visitId)
        if not len(convergeData):
            return

        [visitId] = convergeData.pfs_visit_id.unique()
        maxIter = int(convergeData.iteration.max())
        # offset puts the title, the minIter cut and the legend on 1-based convergence numbering.
        __, offset = self.convergenceCount(convergeData, visitId)
        if nIter == -1:
            nIter = maxIter
        shownIter = nIter - offset

        iterData = convergeData.query(f'iteration=={nIter}').reset_index(drop=True)
        if iterData.empty:
            return

        pfsConfigDf = self.loadPfsConfigFromDB(visitId)
        finalData = self.addPfsConfigInfo(iterData, pfsConfigDf)

        # show broken cobras.
        bad = finalData.loc[self.badIdx]
        ax1.scatter(calibModel.centers.real[bad['cobra_id'].values - 1],
                    calibModel.centers.imag[bad['cobra_id'].values - 1], marker='x', color='k', s=20,
                    alpha=0.5)

        stats = self.convergenceStats(finalData)

        # cobras entering the statistics, and their distance to target at this iteration.
        moving = self.selectMovingCobras(finalData)
        dist = self.distToTarget(moving)

        vmin = float(dist.min()) if vmin == 'auto' else float(vmin)
        vmax = float(dist.max()) if vmax == 'auto' else float(vmax)

        sc = ax1.scatter(calibModel.centers.real[moving['cobra_id'].values - 1],
                         calibModel.centers.imag[moving['cobra_id'].values - 1],
                         c=dist, marker='o', s=20, vmin=vmin, vmax=vmax)

        self.updateColorbar('convergence', ax1, sc, label='μm')

        ax1.set_xlabel("X (mm)")
        ax1.set_ylabel("Y (mm)")
        ax1.set_aspect('equal')
        ax1.format_coord = self.cobraIdFiberIdFormatter

        # per-iteration histograms.
        histData = convergeData.query(f'iteration>={minIter + offset}')
        cmap = plt.get_cmap('viridis')(np.linspace(1.0, 0, histData.iteration.nunique()))
        for i, (iterVal, group) in enumerate(histData.groupby('iteration')):
            group = self.selectMovingCobras(self.addPfsConfigInfo(group, pfsConfigDf).reset_index())
            ax2.hist(self.distToTarget(group), alpha=0.6, histtype='step', linewidth=3,
                     label=f'{iterVal - offset}-th Iteration', bins=bins, range=(vmin, vmax), color=cmap[i])

        ax2.set_xlabel("Distance (microns)")
        ax2.set_ylabel("N")
        ax2.set_xlim(vmin, vmax)
        # horizontal gridlines are worth more read against the cumulative percentage than
        # against the bin counts, so the cumulative axis carries them when it is shown.
        ax2.grid(axis='x')
        ax2.grid(axis='y', visible=not showCumulative)

        # percentiles of the shown iteration, guarded to [0, 100].
        percentiles = self.parsePercentiles(showPercentiles)
        if len(dist) and percentiles:
            for value, perc in zip(np.percentile(dist, percentiles), percentiles):
                color = 'r' if perc >= 95 and value > 10 else 'k'
                # axvline spans the axes whatever the y limit ends up being.
                ax2.axvline(value, label=f'{perc}th : {value:.1f} microns', color=color, alpha=0.5)

        # Upper left, above the peak: the cumulative curve plateaus in the upper right and the
        # distribution tail runs along the bottom.
        self.makeRoomForLegend(ax2, ax2.legend(loc='upper left', fontsize=8, framealpha=0.8))

        # cumulative distribution of the shown iteration on a twin axis.
        if self.cumAxis is None:
            self.cumAxis = ax2.twinx()
        self.cumAxis.cla()
        # cla() resets the shared axis to the left; put it back on the right.
        self.cumAxis.yaxis.set_label_position("right")
        self.cumAxis.yaxis.tick_right()
        self.cumAxis.set_ylim(0, 100)
        # keep the twin under the histogram, which being the newer axes it would cover.
        self.cumAxis.set_zorder(ax2.get_zorder() - 1)
        ax2.patch.set_visible(False)
        if showCumulative and len(dist):
            xs = np.sort(dist)
            ys = 100 * np.arange(1, len(xs) + 1) / len(xs)
            # One muted line, behind the steps: filling under it would compete with the
            # histogram for the same area. The right axis is coloured to match, so which of
            # the two scales the curve belongs to needs no legend entry.
            cumulativeColor = '0.35'
            self.cumAxis.plot(xs, ys, color=cumulativeColor, linewidth=1.4, zorder=0)
            # The tail runs far past the histogram, so the curve leaves the panel below 100%.
            # Spell out where it actually is at the edge, which flattening near the top hides.
            reached = 100 * np.mean(dist <= vmax)
            self.cumAxis.annotate(f'{reached:.0f}% < {vmax:.0f}um', xy=(vmax, reached),
                                  xytext=(-4, -4), textcoords='offset points', ha='right', va='top',
                                  fontsize=8, color=cumulativeColor)
            self.cumAxis.set_ylabel("cumulative %", color=cumulativeColor)
            self.cumAxis.tick_params(axis='y', colors=cumulativeColor)
            self.cumAxis.spines['right'].set_color(cumulativeColor)
            self.cumAxis.grid(axis='y', color=cumulativeColor, alpha=0.35, linewidth=0.7)
        else:
            self.cumAxis.set_yticks([])

        # statistics box on the map's empty corner.
        threshold = self.loadConvergThreshold(visitId)
        ax1.text(0.02, 0.02, self.statsText(stats, dist, percentiles, threshold),
                 transform=ax1.transAxes, va='bottom', ha='left', fontsize=8, family='monospace',
                 bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))

        return int(visitId), int(shownIter)

    @staticmethod
    def parsePercentiles(showPercentiles):
        """Percentiles to display, from a comma-separated string, kept within [0, 100]."""
        try:
            values = [int(v) for v in str(showPercentiles).split(',')]
        except ValueError:
            return [75, 95]
        values = [v for v in values if 0 <= v <= 100]
        return values or [75, 95]

    @staticmethod
    def distToTarget(data):
        """Distance from target to measured centre, in microns."""
        return 1e3 * np.hypot(data.pfi_center_x_mm - data.pfi_target_x_mm,
                              data.pfi_center_y_mm - data.pfi_target_y_mm)

    def convergenceStats(self, finalData):
        """Convergence bookkeeping for the shown iteration, by cobra role.

        converging and toDot come from cobra_command (CONVERGE / BLACK_DOT), or on legacy
        configs without it from target type. notConverged is read from fiber_status; hidden
        counts the dot cobras with no measured final position (undetected behind the dot).
        """
        good = finalData.loc[self.goodIdx]
        fiberStatus = good.fiberStatus
        if (good.cobraCommand == CobraCommand.CONVERGE).any():
            converging = good.cobraCommand == CobraCommand.CONVERGE
            toDot = good.cobraCommand == CobraCommand.BLACK_DOT
        else:
            converging = (good.targetType != TargetType.UNASSIGNED) & (fiberStatus != FiberStatus.MASKED)
            toDot = good.targetType == TargetType.BLACKSPOT
        return {'converging': int(converging.sum()),
                'notConverged': int((fiberStatus[converging] == FiberStatus.NOTCONVERGED).sum()),
                'toDot': int(toDot.sum()),
                'hidden': int((toDot & good.notDetected).sum()),
                'broken': len(self.badIdx)}

    @staticmethod
    def statsText(stats, dist, percentiles, threshold=None):
        """Summary grouped by cobra role. converging, toDot and broken partition the cobras
        (they should sum to the cobra count); the convergence numbers hang under converging.
        """
        def frac(n, d):
            return f' ({100 * n / d:.0f}%)' if d else ''

        notConvLabel = f'notConverged(<{threshold:.0f}um)' if threshold is not None else 'notConverged'
        lines = [f'converging: {stats["converging"]}']
        if len(dist):
            lines.append(f'    median: {np.median(dist):.1f} um')
            for perc, value in zip(percentiles, np.percentile(dist, percentiles)):
                lines.append(f'    {perc}th: {value:.1f} um')
        lines.append(f'    {notConvLabel}: {stats["notConverged"]}'
                     f'{frac(stats["notConverged"], stats["converging"])}')
        lines.append('')
        lines.append(f'to dot: {stats["toDot"]}')
        lines.append(f'    hidden: {stats["hidden"]}{frac(stats["hidden"], stats["toDot"])}')
        lines.append(f'broken: {stats["broken"]}')
        return '\n'.join(lines)

    def selectMovingCobras(self, iterData):
        """Cobras driven to converge on a science target, the ones the statistics are about.

        cobra_command CONVERGE, or on legacy configs without it, assigned non-masked science
        cobras. Black-dot and broken cobras are counted separately and left out: their
        distance to target is not a convergence measure.
        """
        iterData = iterData.loc[self.goodIdx]
        if (iterData.cobraCommand == CobraCommand.CONVERGE).any():
            keep = iterData.cobraCommand == CobraCommand.CONVERGE
        else:
            keep = (iterData.targetType != TargetType.UNASSIGNED) & (iterData.fiberStatus != FiberStatus.MASKED)
        return iterData[keep]
