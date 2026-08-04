import numpy as np
import pfs.drp.stella.utils.guiders as guiders
import pfsPlotActor.livePlot as livePlot
from pfs.utils.database import opdb as opdbIO


class AxesGrid:
    """Present a flat list of Axes as the (nRows, 1) grid that guiders.plotFocus expects.

    The deployed drp_stella weekly's guiders.plotFocus is inconsistent about axes
    dimensionality: it indexes ``axes[i, j]`` (2-D) for plotting but also does
    ``for ax in axes`` / ``axes.flatten()`` in its helpers (overplotFocusSets,
    showVisitBoundaries, ShowFocusFit), which expect a flat sequence of Axes. A plain
    ndarray cannot satisfy both. This wrapper is 2-D-indexable yet iterates and flattens
    as individual Axes. Assumes a single column (the actor never uses plotPerCamera).
    """

    def __init__(self, axes):
        self._axes = list(axes)
        self.shape = (len(self._axes), 1)

    def __getitem__(self, key):
        # 2-D access axes[i, j] -> row i (single column); int access axes[i] -> Axes i.
        i = key[0] if isinstance(key, tuple) else key
        return self._axes[i]

    def __iter__(self):
        return iter(self._axes)

    def __len__(self):
        return len(self._axes)

    def flatten(self):
        return np.array(self._axes, dtype=object)


class AgPlot(livePlot.LivePlot):
    key = 'guideErrors'
    # needs to be overridden by the user.
    actor = 'ag'

    opdb = opdbIO.OpDB()

    @staticmethod
    def readData(visitId, includeAllVisitsInGroup=False):
        """
        load data to plot the results of a convergence run.
        This does a join on cobra_target and cobra_match to get both target and actual positions.
        This loads the results at a given iteration
        """
        visits = AgPlot.getAllVisits(visitId, includeAllVisitsInGroup=includeAllVisitsInGroup)
        return guiders.readAgcDataFromOpdb(livePlot.LivePlot.getConn(), visits=visits)
        # return guiders.readAgcDataFromOpdb(AgPlot.opdb.connect(), visits=visits)

    @staticmethod
    def getAllVisits(visitId, includeAllVisitsInGroup=False):
        visits = [visitId]

        if includeAllVisitsInGroup:
            visit0 = AgPlot.opdb.query_dataframe(
                f'select pfs_visit_id, visit0 from pfs_config_sps where pfs_visit_id={visitId}')

            if visit0.size:
                allVisits = AgPlot.opdb.query_dataframe(
                    f'select pfs_visit_id, visit0 from pfs_config_sps where visit0={visit0.squeeze().visit0}')
                visits += list(allVisits.pfs_visit_id)
                visits = list(set(visits))

        return visits

    def initialize(self):
        """Initialize your axes and colorbar"""
        self.colorbar = None
        ax = self.fig.add_subplot(111)
        return ax

    def identify(self, keyvar, newValue):
        """load the ag data"""
        exposureId, dRA, dDec, dInR, dAz, dAlt, dZ, dScale, status = keyvar.getValue()
        sql = f'select pfs_visit_id from agc_exposure where agc_exposure_id={exposureId}'
        [visitId, ] = AgPlot.opdb.query_dataframe(sql).pfs_visit_id.to_numpy()

        return dict(dataId=visitId, newValue=newValue)

    def plot(self, agcData, *args, **kwargs):
        """Plot the latest dataset."""
        pass

    def selectData(self, latestVisitId, visitId, includeAllVisitsInGroup=False):
        """The user might choose another visitId."""
        selectedVisit = latestVisitId if visitId == -1 else visitId
        selectedVisit = -1 if selectedVisit is None else selectedVisit

        return self.readData(selectedVisit, includeAllVisitsInGroup=includeAllVisitsInGroup)

    def selectVisit(self, latestVisit, visitId):
        """The user might choose another visitId."""
        selectedVisit = latestVisit if visitId == -1 else visitId
        selectedVisit = -1 if selectedVisit is None else selectedVisit

        return selectedVisit
