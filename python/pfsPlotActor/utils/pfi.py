import numpy as np
import pfsPlotActor.livePlot as livePlot
from pfs.datamodel import PfsDesign
from pfs.utils.database import opdb as opdbIO
from pfsPlotActor.utils.sgfm import sgfm


class ConvergencePlot(livePlot.LivePlot):
    key = 'pfsConfig'
    # needs to be overridden by the user.
    actor = 'fps'

    badIdx = sgfm[~sgfm.COBRA_OK_MASK].index.to_numpy()
    goodIdx = sgfm[sgfm.COBRA_OK_MASK].index.to_numpy()

    pfsDesign = None
    opdb = opdbIO.OpDB()

    def updateColorbar(self, key, ax, mappable, label=None, location='right'):
        """Create the colorbar named ``key`` beside ``ax``, or refresh it in place.

        Keyed so a figure with several maps keeps one persistent colorbar each across redraws.
        """
        colorbars = getattr(self, '_colorbars', None)
        if colorbars is None:
            colorbars = self._colorbars = {}
        if key not in colorbars:
            # ax.get_figure() so an axes living in a subfigure gets its colorbar there.
            colorbars[key] = ax.get_figure().colorbar(mappable, ax=ax, fraction=0.046, pad=0.02,
                                                      location=location, label=label)
        else:
            colorbars[key].update_normal(mappable)

    @staticmethod
    def makeRoomForLegend(legendAxes, legend, pad=0.05):
        """Raise the y limit of ``legendAxes`` until the plotted data clears ``legend``.

        A legend pinned to a corner overlaps whatever is drawn there; stretching the axis
        instead of moving the legend keeps the corner it was given. ``pad`` is the gap left
        below the legend, as a fraction of the axes height. Does nothing when the legend
        cannot be measured, or when it already covers most of the height.
        """
        figure = legendAxes.get_figure()
        try:
            renderer = figure.canvas.get_renderer()
        except AttributeError:
            return

        # legend height as a fraction of the axes, so it stays valid across y limits.
        legendBox = legend.get_window_extent(renderer).transformed(legendAxes.transAxes.inverted())
        below = 1 - legendBox.height - pad
        if below <= 0.1:
            return

        ymin, ymax = legendAxes.get_ylim()
        legendAxes.set_ylim(ymin, ymin + (ymax - ymin) / below)

    def singleSubFigure(self):
        """One full-figure subfigure, so a single-quantity plot titles itself like a multi one."""
        self.fig.set_layout_engine('constrained')
        self.subFigs = self.fig.subfigures(1, 1, squeeze=False).ravel()
        return self.subFigs[0]

    def decorateTitles(self, headings, shown=None):
        """Two levels of title: figure = the run, subfigure = the quantity it shows.

        ``headings`` pairs with self.subFigs; ``shown`` is the (visit, iteration) on display,
        or None when nothing was drawn. Panel titles are left alone, so a panel is free to
        title itself.
        """
        for subFig, heading in zip(self.subFigs, headings):
            # left aligned and spanning the subfigure, so a heading can carry lines of numbers.
            subFig.suptitle(heading, x=0.01, ha='left', fontsize=13)

        self.fig.suptitle(self.runTitle(*shown) if shown else "", fontsize=14)

    @staticmethod
    def boldText(text):
        """``text`` as mathtext bold, to weight part of a title whose rest is plain.

        Spaces and percent signs are escaped, being mathtext markup rather than characters.
        """
        return f"$\\bf{{{text.replace('%', chr(92) + '%').replace(' ', chr(92) + ' ')}}}$"

    def runTitle(self, visitId, iteration):
        """When the visit ran, how long it took, and the design it was observing.

        Kept terse so it holds a single line down to an 11 inch window.
        """
        parts = [f"v{visitId}"]

        startedAt, elapsed = self.loadConvergTiming(visitId)
        if startedAt is not None:
            parts.append(startedAt.strftime('%Y-%m-%d %H:%M'))
        parts.append(f"nIter={iteration}")
        if elapsed is not None:
            perIteration = f", {elapsed / iteration:.0f}s/iter" if iteration else ""
            parts.append(f"{elapsed:.0f}s{perIteration}")

        designId, designName = self.loadDesign(visitId)
        if designId is not None:
            parts.append(f"0x{designId:016x}")
        if designName:
            parts.append(designName)
        return " · ".join(parts)

    def convergenceCount(self, convergeData, visitId):
        """Number of convergence iterations in the run, and the offset from the raw index.

        The raw iteration index can carry a leading frame that is not a convergence step (a
        goHome, or the exposure after a blind move). Anchoring to the allocated count
        (converg_num_iter, clamped to what actually ran) absorbs it without having to detect
        it, so subtracting the offset gives 1-based convergence numbering.
        """
        numIter = self.loadConvergNumIter(visitId)
        nRan = convergeData.iteration.nunique()
        convCount = nRan if numIter is None else min(numIter, nRan)
        return convCount, int(convergeData.iteration.max()) - convCount

    @staticmethod
    def cobraIdFiberIdFormatter(x, y):
        """"""
        dx = sgfm.x.to_numpy() - x
        dy = sgfm.y.to_numpy() - y
        row = sgfm.loc[np.argmin(np.hypot(dx, dy))]
        return f'x=%d. y=%d. cobraId=%d fiberId=%d' % (x, y, row.cobraId, row.fiberId)

    @staticmethod
    def loadConvergence(visitId):
        """
        load data to plot the results of a convergence run.
        This does a join on cobra_target and cobra_match to get both target and actual positions.
        This loads the results at a given iteration

        A cobra with no spot matched to it, spot_id -1, comes back with a NaN position: it was
        not measured that iteration, whatever cobra_match holds for it.
        """
        visitId = int(visitId)

        sql = f'select cm.pfs_visit_id, cm.iteration, cm.cobra_id, cm.spot_id, ' \
              f'cm.pfi_center_x_mm, cm.pfi_center_y_mm, ' \
              f'ct.pfi_target_x_mm, ct.pfi_target_y_mm, md.mcs_center_x_pix, md.mcs_center_y_pix, ' \
              f'md.mcs_second_moment_x_pix,md.mcs_second_moment_y_pix, md.peakvalue  from cobra_match ' \
              f'cm inner join cobra_target ct on ct.pfs_visit_id = cm.pfs_visit_id and ct.iteration = ' \
              f'cm.iteration and ct.cobra_id = cm.cobra_id inner join mcs_data md ' \
              f'on md.mcs_frame_id = cm.pfs_visit_id * 100 + cm.iteration and md.spot_id = cm.spot_id where cm.pfs_visit_id = {visitId} order by ct.cobra_id, ct.iteration'

        convergeData = ConvergencePlot.opdb.query_dataframe(sql)

        # cobra_match records a position for a cobra it matched no spot to, which the cobra was
        # never measured at. fps finalises those to NaN off the same flag; do it here so no
        # caller mistakes one for a measurement.
        unmatched = convergeData.spot_id == -1
        convergeData.loc[unmatched, ['pfi_center_x_mm', 'pfi_center_y_mm']] = np.nan

        return convergeData

    @staticmethod
    def loadPfsConfigFromDB(visitId):
        sql = (
            "SELECT pcf.fiber_id, pdf.target_type, pcf.fiber_status, pcf.cobra_command, "
            "pcf.pfi_center_final_x_mm, pcf.target_validation_mask "
            "FROM pfs_config AS pc "
            "INNER JOIN pfs_config_fiber AS pcf "
            "ON pcf.pfs_design_id = pc.pfs_design_id AND pcf.visit0 = pc.visit0 "
            "INNER JOIN pfs_design_fiber AS pdf "
            "ON pdf.pfs_design_id = pc.pfs_design_id AND pdf.fiber_id = pcf.fiber_id "
            f"WHERE pc.visit0 = {visitId}"
        )

        return ConvergencePlot.opdb.query_dataframe(sql).set_index('fiber_id').sort_index()

    @staticmethod
    def loadConvergNumIter(visitId):
        """Allocated number of convergence iterations for the visit, or None if unset.

        This is the requested count, so it can exceed the iterations actually taken when
        convergence stops early; callers should clamp to the last iteration present.
        """
        sql = f'select converg_num_iter from pfs_config where visit0={int(visitId)}'
        df = ConvergencePlot.opdb.query_dataframe(sql)
        if not len(df) or df.converg_num_iter.isna().all():
            return None
        return int(df.converg_num_iter.iloc[0])

    @staticmethod
    def loadDesign(visitId):
        """The design id and name behind the visit, or (None, None) when there is no design."""
        sql = ('select pv.pfs_design_id, pd.design_name from pfs_visit pv '
               'join pfs_design pd on pd.pfs_design_id = pv.pfs_design_id '
               f'where pv.pfs_visit_id = {int(visitId)}')
        df = ConvergencePlot.opdb.query_dataframe(sql)
        if not len(df):
            return None, None
        # the id is stored signed, but it is always shown as a 64 bit hex.
        return int(df.pfs_design_id.iloc[0]) & (2 ** 64 - 1), df.design_name.iloc[0]

    @staticmethod
    def loadConvergTiming(visitId):
        """When the convergence started and how long it took, either None if not recorded.

        The start is the first MCS frame of the visit. The duration is what fps recorded for the
        run, which is longer than the span between frames since it covers the moves either side.
        """
        visitId = int(visitId)
        frames = ConvergencePlot.opdb.query_dataframe(
            f'select min(taken_at) as started_at from mcs_exposure '
            f'where mcs_frame_id between {visitId * 100} and {visitId * 100 + 99}')
        started = frames.started_at.iloc[0] if len(frames) and not frames.started_at.isna().all() else None

        config = ConvergencePlot.opdb.query_dataframe(
            f'select converg_elapsed_time from pfs_config where visit0={visitId}')
        elapsed = float(config.converg_elapsed_time.iloc[0]) \
            if len(config) and not config.converg_elapsed_time.isna().all() else None

        return started, elapsed

    # what fps converges to when pfs_config does not say.
    defaultConvergThreshold = 50

    @staticmethod
    def loadConvergThreshold(visitId):
        """Distance [microns] within which a science fiber counts as converged.

        Falls back to defaultConvergThreshold for a visit whose pfs_config does not record it.
        """
        sql = f'select converg_distance_threshold from pfs_config where visit0={int(visitId)}'
        df = ConvergencePlot.opdb.query_dataframe(sql)
        if not len(df) or df.converg_distance_threshold.isna().all():
            return ConvergencePlot.defaultConvergThreshold
        return 1e3 * float(df.converg_distance_threshold.iloc[0])

    @staticmethod
    def getPfsDesignId(visitId):
        visitId = int(visitId)
        sql = f'select pfs_design_id from pfs_visit where pfs_visit_id={visitId}'
        [[pfsDesignId]] = ConvergencePlot.opdb.query_dataframe(sql).to_numpy()
        return pfsDesignId

    @staticmethod
    def getFiducialData(visitId):
        sql = f'SELECT * from fiducial_fiber_match WHERE pfs_visit_id={visitId}'
        return ConvergencePlot.opdb.query_dataframe(sql)

    @staticmethod
    def getPfsDesign(designId):
        return PfsDesign.read(designId, dirName='/data/pfsDesign')

    def initialize(self):
        """Initialize your axes and colorbar"""
        self.colorbar = None
        ax = self.fig.add_subplot(111)
        return ax

    def identify(self, keyvar, newValue):
        """identify visit from keyvar"""
        designId, visit, status = keyvar.getValue()
        return dict(dataId=visit, newValue=newValue)

    def plot(self, latestVisitId, *args, **kwargs):
        """Plot the latest dataset."""
        pass

    def addPfsConfigInfo(self, iterData, pfsConfigDf):
        """add target information."""
        iterData = iterData.copy()
        iterData['fiberId'] = sgfm.loc[iterData.cobra_id.to_numpy() - 1].fiberId.to_numpy()
        iterData['targetType'] = pfsConfigDf.loc[iterData.fiberId.to_numpy()].target_type.to_numpy()
        iterData['fiberStatus'] = pfsConfigDf.loc[iterData.fiberId.to_numpy()].fiber_status.to_numpy()
        iterData['cobraCommand'] = pfsConfigDf.loc[iterData.fiberId.to_numpy()].cobra_command.to_numpy()
        iterData['validationMask'] = \
            pfsConfigDf.loc[iterData.fiberId.to_numpy()].target_validation_mask.to_numpy()
        # No measured final position means the spot was not detected (e.g. hidden behind the dot).
        finalX = pfsConfigDf.loc[iterData.fiberId.to_numpy()].pfi_center_final_x_mm.to_numpy(dtype=float)
        iterData['notDetected'] = np.isnan(finalX)
        return iterData

    def selectData(self, latestVisitId, visitId):
        """The user might choose another visitId."""
        selectedVisit = latestVisitId if visitId == -1 else visitId
        selectedVisit = -1 if selectedVisit is None else selectedVisit
        return self.loadConvergence(selectedVisit)

    def reloadDesign(self, visitId):
        """Reload PfsDesign"""
        pfsDesignId = ConvergencePlot.getPfsDesignId(visitId)

        if not self.pfsDesign or self.pfsDesign.pfsDesignId != pfsDesignId:
            self.pfsDesign = ConvergencePlot.getPfsDesign(pfsDesignId)

        return self.pfsDesign
