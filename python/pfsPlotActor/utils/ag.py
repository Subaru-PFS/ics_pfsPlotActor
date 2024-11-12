import pfsPlotActor.livePlot as livePlot
import pfsPlotActor.utils.guiders as rhlGuiders
import psycopg2


class AgPlot(livePlot.LivePlot):
    key = 'guideErrors'
    # needs to be overridden by the user.
    actor = 'ag'

    @staticmethod
    def getConn():
        """
        Establishes a connection to the PostgreSQL database 'opdb' on host 'pfsa-db01' and port 5432 with user 'pfs'.

        Returns:
        conn: A PostgreSQL connection object.
        """
        return psycopg2.connect("dbname='opdb' host='db-ics' port=5432 user='pfs'")

    @staticmethod
    def readData(visitId):
        """
        load data to plot the results of a convergence run.
        This does a join on cobra_target and cobra_match to get both target and actual positions.
        This loads the results at a given iteration
        """
        opdb = AgPlot.getConn()
        agcData = rhlGuiders.readAgcDataFromOpdb(opdb, visits=[visitId])
        return dict(agcData=agcData)

    def selectData(self, dataset, visitId):
        """The user might choose another visitId."""
        if visitId == -1:
            return dataset

        return self.readData(visitId)['agcData']

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
            [visitId, ] = rhlGuiders.pd_read_sql(sql, AgPlot.getConn()).pfs_visit_id.to_numpy()
        except ValueError:
            visitId = 1

        return self.readData(visitId)

    def plot(self, agcData, *args, **kwargs):
        """Plot the latest dataset."""
        pass
