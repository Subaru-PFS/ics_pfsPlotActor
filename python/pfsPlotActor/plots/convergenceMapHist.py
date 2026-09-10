from importlib import reload

import matplotlib.pyplot as plt
import numpy as np
import pfsPlotActor.utils.pfi as pfiUtils
from pfs.datamodel import TargetType, FiberStatus, CobraCommand
from pfsPlotActor.utils.sgfm import calibModel

reload(pfiUtils)


class ConvergenceMapHist(pfiUtils.ConvergencePlot):
    units = dict(vmin='µm', vmax='µm')

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
        self.decorateTitles((self.distanceHeading(),), shown)
        return bool(shown)

    def drawConvergence(self, ax1, ax2, latestVisitId, visitId=-1, nIter=-1, vmin=0, vmax=30,
                        bins=30, minIter=3, showPercentiles='75,95', showCumulative=False):
        """Draw the convergence map on ax1 and the per-iteration distance histogram on ax2.

        Shared by the standalone plot and the combined convergence/fiducials plot; the caller
        owns the figure, its layout and its titles. Returns the (visit, iteration) drawn, or
        None when there is nothing to show.
        """
        self.convergenceSummary = self.convergenceSpread = ""
        self.distanceName = "Distance to target"
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

        # the cobras fps did not command, crossed out. Taken from the visit like the count that
        # goes with them, so the two agree whatever calibration this client holds.
        bad = (finalData[finalData.cobraCommand == CobraCommand.NOT_COMMANDED]
               if self.commandsRecorded(finalData) else finalData.loc[self.badIdx])
        ax1.scatter(calibModel.centers.real[bad['cobra_id'].values - 1],
                    calibModel.centers.imag[bad['cobra_id'].values - 1], marker='x', color='r', s=20,
                    alpha=0.4)

        stats = self.convergenceStats(finalData)

        # cobras entering the statistics, and their distance to target at this iteration.
        moving = self.selectMovingCobras(finalData)
        dist = self.distToTarget(moving)
        # a run that drove nothing at a science target converged on the dots, so say so.
        if len(moving) and (moving.cobraCommand == CobraCommand.BLACK_DOT).all():
            self.distanceName = "Distance to black dot"

        vmin = float(dist.min()) if vmin == 'auto' else float(vmin)
        vmax = float(dist.max()) if vmax == 'auto' else float(vmax)

        sc = ax1.scatter(calibModel.centers.real[moving['cobra_id'].values - 1],
                         calibModel.centers.imag[moving['cobra_id'].values - 1],
                         c=dist, marker='o', s=20, vmin=vmin, vmax=vmax)

        # a cobra parked on its dot converged on nothing, so it carries no distance to colour;
        # star it instead, telling it from the broken cobras' cross. A run whose subject is the
        # dots has none left over, having just drawn them.
        parked = finalData[(finalData.cobraCommand == CobraCommand.BLACK_DOT)
                           & ~finalData.index.isin(moving.index)]
        ax1.scatter(calibModel.centers.real[parked['cobra_id'].values - 1],
                    calibModel.centers.imag[parked['cobra_id'].values - 1], marker='*', color='k',
                    s=25, alpha=0.5)

        self.updateColorbar('convergence', ax1, sc, label='µm')

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

        ax2.set_xlabel("Distance (µm)")
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
                ax2.axvline(value, label=f'{perc}th : {value:.1f} µm', color=color, alpha=0.5)

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
            self.cumAxis.annotate(f'{reached:.0f}% < {vmax:.0f} µm', xy=(vmax, reached),
                                  xytext=(-4, -4), textcoords='offset points', ha='right', va='top',
                                  fontsize=8, color=cumulativeColor)
            self.cumAxis.set_ylabel("cumulative %", color=cumulativeColor)
            self.cumAxis.tick_params(axis='y', colors=cumulativeColor)
            self.cumAxis.spines['right'].set_color(cumulativeColor)
            self.cumAxis.grid(axis='y', color=cumulativeColor, alpha=0.35, linewidth=0.7)
        else:
            self.cumAxis.set_yticks([])

        # read under the heading, which spans both panels rather than crowding either one.
        self.convergenceSpread = self.spreadText(dist, percentiles)
        self.convergenceSummary = self.statsText(stats, self.loadConvergThreshold(visitId))

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

    @staticmethod
    def commandsRecorded(iterData):
        """Whether pfs_config_fiber recorded what each cobra was told to do.

        A config written before cobra_command existed leaves it unset, and there the roles can
        only come from the target type. A run that commands every cobra to its black dot still
        recorded them, so looking for CONVERGE would mistake it for one of those old configs.
        """
        return iterData.cobraCommand.isin([CobraCommand.CONVERGE, CobraCommand.BLACK_DOT,
                                           CobraCommand.HOME]).any()

    def convergenceStats(self, finalData):
        """Convergence bookkeeping for the shown iteration, by cobra role.

        converging, toDot and broken come from cobra_command (CONVERGE / BLACK_DOT /
        NOT_COMMANDED), so they partition the cobras and report what fps decided for this
        visit rather than the calibration the client running this happens to have. A legacy
        config carries no cobra_command; there the roles come from target type and the broken
        count from COBRA_OK_MASK. notConverged is read from fiber_status; hidden counts the
        dot cobras with no measured final position (undetected behind the dot).
        """
        if self.commandsRecorded(finalData):
            rows = finalData
            converging = rows.cobraCommand == CobraCommand.CONVERGE
            toDot = rows.cobraCommand == CobraCommand.BLACK_DOT
            broken = int((rows.cobraCommand == CobraCommand.NOT_COMMANDED).sum())
        else:
            rows = finalData.loc[self.goodIdx]
            converging = ((rows.targetType != TargetType.UNASSIGNED)
                          & (rows.fiberStatus != FiberStatus.MASKED))
            toDot = rows.targetType == TargetType.BLACKSPOT
            broken = len(self.badIdx)

        return {'converging': int(converging.sum()),
                'notConverged': int((rows.fiberStatus[converging] == FiberStatus.NOTCONVERGED).sum()),
                'toDot': int(toDot.sum()),
                'hidden': int((toDot & rows.notDetected).sum()),
                'broken': broken}

    def spreadText(self, dist, percentiles):
        """Median and the requested percentiles of the distance to target, in microns."""
        if not len(dist):
            return ''
        spread = [f'median: {self.boldText(f"{np.median(dist):.1f} µm")}']
        spread.extend(f'{perc}th: {self.boldText(f"{value:.1f} µm")}' for perc, value
                      in zip(percentiles, np.percentile(dist, percentiles)))
        return '   '.join(spread)

    def statsText(self, stats, threshold):
        """The cobras that fell short, each over the total of the role it belongs to.

        Converging, black dot and broken partition the cobras, so the two denominators and
        BROKENCOBRA sum to the cobra count. ``threshold`` is in microns, and NOTCONVERGED is
        the fiber status, so it counts the cobras that ended further than that from their
        target. BLACKDOT counts the dot cobras that went undetected behind their dot. The
        counts are bold and the labels plain, so the eye lands on the numbers.
        """
        def over(n, d):
            return self.boldText(f'{n}/{d} ({100 * n / d:.0f}%)' if d else f'{n}')

        return (f'NOTCONVERGED(>{threshold:.0f}µm): {over(stats["notConverged"], stats["converging"])}   '
                f'BLACKDOT: {over(stats["hidden"], stats["toDot"])}   '
                f'BROKENCOBRA: {self.boldText(str(stats["broken"]))}')

    def distanceHeading(self):
        """The quantity name, with its spread alongside and the cobra counts underneath."""
        heading = self.boldText(self.distanceName)
        if self.convergenceSpread:
            heading = f'{heading}   {self.convergenceSpread}'
        return f'{heading}\n{self.convergenceSummary}' if self.convergenceSummary else heading

    def selectMovingCobras(self, iterData):
        """Cobras driven at a target, whose distance to it is what the run converged to.

        cobra_command CONVERGE, or on legacy configs without it, assigned non-masked science
        cobras. Where a run commands none of them to a science target it is converging on the
        dots instead, and the black dot cobras are the subject; on a run that has both, they are
        counted separately and left out, their distance to a dot not being a convergence
        measure. Uncommanded cobras are never included.
        """
        if not self.commandsRecorded(iterData):
            iterData = iterData.loc[self.goodIdx]
            keep = ((iterData.targetType != TargetType.UNASSIGNED)
                    & (iterData.fiberStatus != FiberStatus.MASKED))
            return iterData[keep]

        converging = iterData.cobraCommand == CobraCommand.CONVERGE
        if converging.any():
            return iterData[converging]

        return iterData[iterData.cobraCommand == CobraCommand.BLACK_DOT]
