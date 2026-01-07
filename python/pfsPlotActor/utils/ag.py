import pfs.drp.stella.utils.guiders as guiders
import pfsPlotActor.livePlot as livePlot
from pfs.utils.database import opdb as opdbIO


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
