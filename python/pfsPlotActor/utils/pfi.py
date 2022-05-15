import numpy as np
import pandas as pd
import pfsPlotActor.livePlot as livePlot
from ics.cobraCharmer import func
from opdb import opdb
from pfs.utils.butler import Butler
from pfs.utils.fiberids import FiberIds

gfm = FiberIds()
gfmDf = pd.DataFrame(gfm.data)
cobraId = np.arange(2394) + 1
cobraPosition = gfmDf.set_index('cobraId').loc[cobraId].reset_index()[['cobraId', 'fiberId', 'x', 'y']].to_numpy()


def getCobraStatusIndex(calibModel):
    """Retrieve good/bad cobra index."""
    # get goodIdx
    allCobras = [func.Cobra(calibModel.moduleIds[i], calibModel.positionerIds[i]) for i in
                 calibModel.findAllCobras()]
    nCobras = len(allCobras)

    goodNums = [i + 1 for i, c in enumerate(allCobras) if calibModel.cobraIsGood(c.cobraNum, c.module)]
    badNums = [e for e in range(1, nCobras + 1) if e not in goodNums]

    goodIdx = np.array(goodNums, dtype='i4') - 1
    badIdx = np.array(badNums, dtype='i4') - 1

    return goodIdx, badIdx


def cobraIdFiberIdFormatter(x, y):
    """"""
    [cobraId, fiberId, cx, cy] = cobraPosition[np.argmin(np.hypot(cobraPosition[:, 2] - x, cobraPosition[:, 3] - y))]
    return f'x=%d. y=%d. cobraId=%d fiberId=%d' % (x, y, cobraId, fiberId)


class ConvergencePlot(livePlot.LivePlot):
    key = 'convergenceId'
    # needs to be overridden by the user.
    actor = 'tests'

    db = opdb.OpDB(hostname="db-ics", username="pfs", dbname="opdb")
    butler = Butler()

    dots = butler.get('black_dots')
    fids = butler.get('fiducials')
    calibModel = butler.get('moduleXml', moduleName='ALL', version='')

    goodIdx, badIdx = getCobraStatusIndex(calibModel)

    @staticmethod
    def loadConvergence(visitId):
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
        convergeData = ConvergencePlot.db.fetch_query(sql)
        return dict(convergeData=convergeData)

    def initialize(self):
        """Initialize your axes and colorbar"""
        self.colorbar = None
        ax = self.fig.add_subplot(111)
        return ax

    def identify(self, keyvar):
        """load the convergence data"""
        visit = keyvar.getValue()
        return self.loadConvergence(visit)

    def plot(self, convergeData, *args, **kwargs):
        """Plot the latest dataset."""
        pass
