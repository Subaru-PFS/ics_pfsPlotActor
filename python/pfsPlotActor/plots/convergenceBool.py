import numpy as np
import pfsPlotActor.livePlot as livePlot
from ics.cobraCharmer import func
from opdb import opdb
from pfs.utils.butler import Butler


def getCobraStatusIndex(calibModel):
    """Retrieve good/bad cobra index."""
    # get goodIdx
    allCobras = [func.Cobra(calibModel.moduleIds[i], calibModel.positionerIds[i]) for i in calibModel.findAllCobras()]
    nCobras = len(allCobras)

    goodNums = [i + 1 for i, c in enumerate(allCobras) if calibModel.cobraIsGood(c.cobraNum, c.module)]
    badNums = [e for e in range(1, nCobras + 1) if e not in goodNums]

    goodIdx = np.array(goodNums, dtype='i4') - 1
    badIdx = np.array(badNums, dtype='i4') - 1

    return goodIdx, badIdx


class ConvergenceBool(livePlot.LivePlot):
    key = 'convergenceId'
    # needs to be overridden by the user.
    actor = 'tests'

    # load pfi design file
    db = opdb.OpDB(hostname="db-ics", username="pfs", dbname="opdb")
    butler = Butler()

    dots = butler.get('black_dots')
    fids = butler.get('fiducials')
    calibModel = butler.get('moduleXml', moduleName='ALL', version='')

    goodIdx, badIdx = getCobraStatusIndex(calibModel)

    def initialize(self):
        """Initialize your axes and colorbar"""
        ax = self.fig.add_subplot(111)
        return ax

    def identify(self, keyvar):
        """load the convergence data"""
        visit = keyvar.getValue()
        return self.loadConvergence(visit)

    def loadConvergence(self, visitId):
        """
        load data to plot the results of a convergence run.
        This does a join on cobra_target and cobra_match to get both target and actual positions.
        This loads the results at a given iteration
        """
        visitId = int(visitId)

        sql = f'select cm.pfs_visit_id, cm.iteration, cm.cobra_id, cm.pfi_center_x_mm, cm.pfi_center_y_mm, ' \
              f'ct.pfi_target_x_mm, ct.pfi_target_y_mm, md.mcs_center_x_pix, md.mcs_center_y_pix, ' \
              f'md.mcs_second_moment_x_pix,md.mcs_second_moment_y_pix, md.peakvalue  from cobra_match ' \
              f'cm inner join cobra_target ct on ct.pfs_visit_id = cm.pfs_visit_id and ct.iteration = ' \
              f'cm.iteration and ct.cobra_id = cm.cobra_id inner join mcs_data md ' \
              f'on md.mcs_frame_id = cm.pfs_visit_id * 100 + cm.iteration and md.spot_id = cm.spot_id where cm.pfs_visit_id = {visitId} order by ct.cobra_id, ct.iteration'

        # get data
        convergeData = self.db.fetch_query(sql)

        # save the maximum iteration, as this is used a lot
        try:
            nIter = convergeData['iteration'].values.max()
        except:
            nIter = 0

        return dict(visitId=visitId, convergeData=convergeData, iterVal=nIter)

    def plot(self, visitId, convergeData, iterVal, threshNon = 0.01):
        """Plot the latest dataset."""
        fig = self.fig
        ax = self.axes[0]

        # calculate distance from targets at this iteration

        dist = np.sqrt((convergeData['pfi_center_x_mm'].values - convergeData['pfi_target_x_mm'].values) ** 2 +
                       (convergeData['pfi_center_y_mm'].values - convergeData['pfi_target_y_mm'].values) ** 2)

        ind1 = np.where(dist <= threshNon)
        ind2 = np.where(dist > threshNon)

        # scatter plots, one colour for converged, one for non converged

        sc=ax.scatter(self.calibModel.centers.real[cD['cobra_id'].values - 1][ind1],self.calibModel.centers.imag[cD['cobra_id'].values - 1][ind1],
                      c='purple',marker='o', s=20, **kwargs)
        sc=ax.scatter(self.calibModel.centers.real[cD['cobra_id'].values - 1][ind2],self.calibModel.centers.imag[cD['cobra_id'].values - 1][ind2],
                      c='green',marker='o', s=20, **kwargs)

        # some labels
        ax.set_xlabel("X (mm)")
        ax.set_ylabel("Y (mm)")

        # label with the pfsvisit Id
        tString = f'pfsVisitId = {visitId:d}, iteration = {iterVal:d}'
        ax.set_title(tString)

        ax.set_aspect('equal')
