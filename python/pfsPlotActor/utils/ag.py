import pfs.drp.stella.utils.guiders as guiders
import pfs.drp.stella.utils.sysUtils as sysUtils
import pfsPlotActor.livePlot as livePlot


class AgPlot(livePlot.LivePlot):
    key = 'guideErrors'
    # needs to be overridden by the user.
    actor = 'ag'

    opdb = livePlot.LivePlot.getConn()

    @staticmethod
    def readData(visitId, includeAllVisitsInGroup=False):
        """
        load data to plot the results of a convergence run.
        This does a join on cobra_target and cobra_match to get both target and actual positions.
        This loads the results at a given iteration
        """
        visits = [visitId]

        if includeAllVisitsInGroup:
            visit0 = sysUtils.pd_read_sql(
                f'select pfs_visit_id, visit0 from pfs_config_sps where pfs_visit_id={visitId}',
                AgPlot.opdb)

            if visit0.size:
                allVisits = sysUtils.pd_read_sql(
                    f'select pfs_visit_id, visit0 from pfs_config_sps where visit0={visit0.squeeze().visit0}',
                    AgPlot.opdb)
                visits += list(allVisits.pfs_visit_id)
                visits = list(set(visits))

        agcData = guiders.readAgcDataFromOpdb(AgPlot.opdb, visits=visits)
        return dict(agcData=agcData)

    def selectData(self, dataset, visitId, includeAllVisitsInGroup=False):
        """The user might choose another visitId."""
        if visitId == -1:
            return dataset

        return self.readData(visitId, includeAllVisitsInGroup=includeAllVisitsInGroup)['agcData']

    def initialize(self):
        """Initialize your axes and colorbar"""
        self.colorbar = None
        ax = self.fig.add_subplot(111)
        return ax

    def identify(self, keyvar):
        """load the convergence data"""
        try:
            exposureId, dRA, dDec, dInR, dAz, dAlt, dZ, dScale = keyvar.getValue()
            sql = f'select pfs_visit_id from agc_exposure where agc_exposure_id={exposureId}'
            [visitId, ] = sysUtils.pd_read_sql(sql, AgPlot.opdb).pfs_visit_id.to_numpy()
        except ValueError:
            visitId = 1

        return self.readData(visitId)

    def plot(self, agcData, *args, **kwargs):
        """Plot the latest dataset."""
        pass
