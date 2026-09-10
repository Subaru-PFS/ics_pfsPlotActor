from importlib import reload

import matplotlib.pyplot as plt
import numpy as np
import pfsPlotActor.utils.pfi as pfiUtils
from pfs.datamodel import TargetType, FiberStatus, CobraCommand, TargetValidation
from pfsPlotActor.utils.sgfm import calibModel

reload(pfiUtils)


class ConvergenceMapHist(pfiUtils.ConvergencePlot):
    units = dict(vmin='µm', vmax='µm')

    def initialize(self):
        """Initialize your axes and colorbar"""
        self.cumAxis = None
        return list(self.singleSubFigure().subplots(1, 2, width_ratios=[1.0, 0.85]))

    def plot(self, latestVisitId, visitId=-1, nIter=-1, vmin=0, vmax=30, bins=30, minIter=3,
             showPercentiles='75,95', showCumulative=True):
        """Plot the latest dataset."""
        shown = self.drawConvergence(self.axes[0], self.axes[1], latestVisitId, visitId=visitId,
                                     nIter=nIter, vmin=vmin, vmax=vmax, bins=bins, minIter=minIter,
                                     showPercentiles=showPercentiles, showCumulative=showCumulative)
        self.decorateTitles((self.distanceHeading(),), shown)
        return bool(shown)

    def drawConvergence(self, ax1, ax2, latestVisitId, visitId=-1, nIter=-1, vmin=0, vmax=30,
                        bins=30, minIter=3, showPercentiles='75,95', showCumulative=True):
        """Draw the convergence map on ax1 and the per-iteration distance histogram on ax2.

        Shared by the standalone plot and the combined convergence/fiducials plot; the caller
        owns the figure, its layout and its titles. Returns the (visit, iteration) drawn, or
        None when there is nothing to show.
        """
        self.convergenceSummary = self.convergenceSpread = self.targetSummary = ""
        # the twin is not among self.axes, so clear() leaves it be; wipe it here rather than
        # where it is drawn, which a run with nothing to show never reaches.
        if self.cumAxis is not None:
            self.cumAxis.cla()
            self.cumAxis.set_yticks([])
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

        # 'auto' has nothing to read from a run that measured no cobra at a target, so keep the
        # range finite rather than handing matplotlib a NaN to bin over.
        measured = dist[np.isfinite(dist)]
        if vmin == 'auto':
            vmin = float(measured.min()) if len(measured) else 0.
        if vmax == 'auto':
            vmax = float(measured.max()) if len(measured) else 1.
        vmin, vmax = float(vmin), float(vmax)

        # a cobra with no spot matched to it has no distance to colour by; grey rather than
        # the transparent a NaN would otherwise draw, so it does not silently leave the map.
        unmeasured = plt.get_cmap('viridis').copy()
        unmeasured.set_bad('0.85')

        # a marker per target type, so what a cobra was pointed at reads off the map.
        sc = None
        for targetType, marker, size in self.targetMarkers:
            subset = moving[moving.targetType == targetType]
            if not len(subset):
                continue
            sc = ax1.scatter(calibModel.centers.real[subset['cobra_id'].values - 1],
                             calibModel.centers.imag[subset['cobra_id'].values - 1],
                             c=dist.loc[subset.index], marker=marker, s=size, vmin=vmin,
                             vmax=vmax, cmap=unmeasured)

        # a legacy config names no target type this knows; those keep the science marker.
        rest = moving[~moving.targetType.isin([t for t, __, __ in self.targetMarkers])]
        if len(rest):
            sc = ax1.scatter(calibModel.centers.real[rest['cobra_id'].values - 1],
                             calibModel.centers.imag[rest['cobra_id'].values - 1],
                             c=dist.loc[rest.index], marker='o', s=20, vmin=vmin, vmax=vmax,
                             cmap=unmeasured)

        # a cobra driven at its dot is left uncoloured: it converged on nothing, and by the last
        # iteration it is behind the dot with no position to measure anyway.
        parked = finalData[finalData.cobraCommand == CobraCommand.BLACK_DOT]
        ax1.scatter(calibModel.centers.real[parked['cobra_id'].values - 1],
                    calibModel.centers.imag[parked['cobra_id'].values - 1], marker='h', color='k',
                    s=20, alpha=0.35)

        self.markerLegend(ax1, moving, len(parked), len(bad))
        if sc is not None:
            self.updateColorbar('convergence', ax1, sc, label='µm')

        ax1.set_xlabel("X (mm)")
        ax1.set_ylabel("Y (mm)")
        ax1.set_aspect('equal')
        ax1.format_coord = self.cobraIdFiberIdFormatter

        # per-iteration histograms.
        histData = convergeData.query(f'iteration>={minIter + offset}')
        cmap = plt.get_cmap('viridis')(np.linspace(1.0, 0, histData.iteration.nunique()))
        for i, (iterVal, group) in enumerate(histData.groupby('iteration')):
            group = self.selectMovingCobras(self.addPfsConfigInfo(group, pfsConfigDf).reset_index(),
                                            orDots=True)
            groupDist = self.distToTarget(group)
            ax2.hist(groupDist[np.isfinite(groupDist)], alpha=0.6, histtype='step', linewidth=3,
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
        if len(measured) and percentiles:
            for value, perc in zip(np.percentile(measured, percentiles), percentiles):
                color = 'r' if perc >= 95 and value > 10 else 'k'
                # axvline spans the axes whatever the y limit ends up being.
                ax2.axvline(value, label=f'{perc}th : {value:.1f} µm', color=color, alpha=0.5)

        # Upper left, above the peak: the cumulative curve plateaus in the upper right and the
        # distribution tail runs along the bottom. A run with nothing to show has nothing to
        # name either, and matplotlib warns rather than drawing an empty box.
        if ax2.get_legend_handles_labels()[0]:
            self.makeRoomForLegend(ax2, ax2.legend(loc='upper left', fontsize=8, framealpha=0.8))

        # cumulative distribution of the shown iteration on a twin axis.
        if self.cumAxis is None:
            self.cumAxis = ax2.twinx()
        # cla() resets the shared axis to the left; put it back on the right.
        self.cumAxis.yaxis.set_label_position("right")
        self.cumAxis.yaxis.tick_right()
        self.cumAxis.set_ylim(0, 100)
        # keep the twin under the histogram, which being the newer axes it would cover.
        self.cumAxis.set_zorder(ax2.get_zorder() - 1)
        ax2.patch.set_visible(False)
        if showCumulative and len(measured):
            xs = np.sort(measured)
            ys = 100 * np.arange(1, len(xs) + 1) / len(xs)
            # One muted line, behind the steps: filling under it would compete with the
            # histogram for the same area. The right axis is coloured to match, so which of
            # the two scales the curve belongs to needs no legend entry.
            cumulativeColor = '0.35'
            self.cumAxis.plot(xs, ys, color=cumulativeColor, linewidth=1.4, zorder=0)
            # The tail runs far past the histogram, so the curve leaves the panel below 100%.
            # Spell out where it actually is at the edge, which flattening near the top hides.
            reached = 100 * np.mean(measured <= vmax)
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
        self.convergenceSpread = self.spreadText(measured, percentiles)
        self.targetSummary = self.targetsText(finalData)
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

    # what the design asked of a cobra, in the order a reader wants them. Only the first three
    # carry a target to validate.
    targetTypes = (TargetType.SCIENCE, TargetType.SKY, TargetType.FLUXSTD,
                   TargetType.UNASSIGNED, TargetType.BLACKSPOT)
    # why fps refused a target. NOT_SET is not a refusal but a config that recorded no verdict.
    rejectionFlags = tuple(flag for flag in TargetValidation if flag != TargetValidation.NOT_SET)

    def targetsText(self, finalData):
        """What the design asked for, and what target validation refused of it.

        Counted over the cobras fps commanded: an uncommanded one is broken, and the design
        assigns it whatever it likes without that meaning anything. Engineering fibers hold no
        target and are left out. Only science, sky and flux standards are validated, so they
        alone are the denominator; a config that recorded no verdict says so instead, whether it
        wrote NOT_SET or, being older than the column, nothing at all.
        """
        working = finalData[finalData.cobraCommand != CobraCommand.NOT_COMMANDED]
        counts = [f'{int((working.targetType == targetType).sum())} {targetType.name}'
                  for targetType in self.targetTypes if (working.targetType == targetType).any()]

        assigned = working[working.targetType.isin(self.targetTypes[:3])]
        line = '  ·  '.join(counts)
        if not len(assigned):
            return line

        # a column older than the verdict comes back null, which pandas floats; the bit tests
        # below need an integer, and a null is no more a verdict than NOT_SET is.
        recorded = assigned.validationMask.notna() & (assigned.validationMask != TargetValidation.NOT_SET)
        if not recorded.any():
            return f'{line}   Rejected: not recorded'

        verdicts = assigned.validationMask[recorded].astype(int)
        refused = verdicts[verdicts > 0]
        line = f'{line}   Rejected: {self.boldText(str(len(refused)))}/{int(recorded.sum())}'
        why = [f'{int((refused & int(flag)).astype(bool).sum())} {flag.name}'
               for flag in self.rejectionFlags if (refused & int(flag)).any()]
        return f'{line} — {" · ".join(why)}' if why else line

    # a marker per target type on the map, the commonest type taking the plainest marker.
    targetMarkers = ((TargetType.SCIENCE, 'o', 20), (TargetType.SKY, '^', 22),
                     (TargetType.FLUXSTD, '*', 40))

    def markerLegend(self, mapAxes, moving, parked, uncommanded):
        """Name the markers in the map's empty corner, listing only the ones drawn."""
        entries = [(marker, size, targetType.name, len(moving[moving.targetType == targetType]))
                   for targetType, marker, size in self.targetMarkers]
        entries.append(('h', 20, TargetType.BLACKSPOT.name, parked))
        entries.append(('x', 20, 'NOT_COMMANDED', uncommanded))

        handles = [mapAxes.scatter([], [], marker=marker, s=size, color='0.35',
                                   label=f'{name} ({count})')
                   for marker, size, name, count in entries if count]
        if handles:
            mapAxes.legend(handles=handles, loc='upper left', fontsize=7, framealpha=0.7,
                           handletextpad=0.2, borderpad=0.3, labelspacing=0.25)

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
        """Median and the requested percentiles of the distance to target.

        Rounded to the micron, which is finer than the cobras are placed to.
        """
        if not len(dist):
            return ''
        spread = [f'median: {self.boldText(f"{np.median(dist):.0f} µm")}']
        spread.extend(f'{perc}th: {self.boldText(f"{value:.0f} µm")}' for perc, value
                      in zip(percentiles, np.percentile(dist, percentiles)))
        return '   '.join(spread)

    def statsText(self, stats, threshold):
        """The cobras that fell short, each over the total of the role it belongs to.

        Converging, black dot and broken partition the cobras, so the two denominators and
        BROKENCOBRA sum to the cobra count. ``threshold`` is in microns, and NOTCONVERGED is
        the fiber status, so it counts the cobras that ended further than that from their
        target. HIDDEN counts the dot cobras fps recorded no final position for, having lost
        sight of them behind their dot. The
        counts are bold and the labels plain, so the eye lands on the numbers.
        """
        def over(n, d):
            return self.boldText(f'{n}/{d} ({100 * n / d:.0f}%)' if d else f'{n}')

        return (f'NOTCONVERGED(>{threshold:.0f}µm): {over(stats["notConverged"], stats["converging"])}   '
                f'HIDDEN: {over(stats["hidden"], stats["toDot"])}   '
                f'BROKENCOBRA: {self.boldText(str(stats["broken"]))}')

    def distanceHeading(self):
        """What the design asked for, then the quantity name, then how the run came out.

        The design is settled before a cobra moves, so it reads above the distance rather than
        under it.
        """
        heading = self.boldText("Distance to target")
        if self.convergenceSpread:
            heading = f'{heading}   {self.convergenceSpread}'

        lines = [line for line in (self.targetSummary, heading, self.convergenceSummary) if line]
        return '\n'.join(lines)

    def selectMovingCobras(self, iterData, orDots=False):
        """Cobras driven at a target, whose distance to it is what the run converged to.

        cobra_command CONVERGE, or on legacy configs without it, assigned non-masked science
        cobras. A cobra driven at its dot is left out of a run that has both: its distance to a
        dot is not a convergence measure. Uncommanded cobras are never included.

        orDots takes the black dot cobras where a run drove nothing at a science target, for a
        caller that can use them: they were measured at every iteration, only the last hiding
        them behind their dots.
        """
        if not self.commandsRecorded(iterData):
            iterData = iterData.loc[self.goodIdx]
            keep = ((iterData.targetType != TargetType.UNASSIGNED)
                    & (iterData.fiberStatus != FiberStatus.MASKED))
            return iterData[keep]

        converging = iterData[iterData.cobraCommand == CobraCommand.CONVERGE]
        if len(converging) or not orDots:
            return converging

        return iterData[iterData.cobraCommand == CobraCommand.BLACK_DOT]
