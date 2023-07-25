import numpy as np
import pandas as pd
import pfsPlotActor.livePlot as livePlot
from ics.cobraCharmer import func
from opdb import opdb
from pfs.datamodel import PfsDesign
from pfs.utils.butler import Butler
from pfs.utils.fiberids import FiberIds


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


def cobraPositionToFiber(db):
    """Return cobraId,fiberId,x,y from opdb/grandfibermap."""
    sql = 'SELECT cobra_id,cobra_geometry_calib_id,center_x_mm,center_y_mm FROM cobra_geometry ' \
          'WHERE cobra_geometry_calib_id=(SELECT MAX(cobra_geometry_calib_id) from cobra_geometry)'
    df = db.fetch_query(sql)
    gfmDf = pd.DataFrame(FiberIds().data)
    df['fiberId'] = gfmDf.set_index('cobraId').loc[df.cobra_id].fiberId.to_numpy()
    return df[['cobra_id', 'fiberId', 'center_x_mm', 'center_y_mm']]


class ConvergencePlot(livePlot.LivePlot):
    key = 'pfsConfig'
    # needs to be overridden by the user.
    actor = 'fps'

    db = opdb.OpDB(hostname="db-ics", username="pfs", dbname="opdb")
    butler = Butler()

    dots = butler.get('black_dots')
    fids = butler.get('fiducials')
    calibModel = butler.get('moduleXml', moduleName='ALL', version='')

    goodIdx, badIdx = getCobraStatusIndex(calibModel)
    cobraPosition = cobraPositionToFiber(db)
    pfsDesign = None

    @staticmethod
    def cobraIdFiberIdFormatter(x, y):
        """"""
        dx = ConvergencePlot.cobraPosition.center_x_mm.to_numpy() - x
        dy = ConvergencePlot.cobraPosition.center_y_mm.to_numpy() - y
        [cobraId, fiberId, cx, cy] = ConvergencePlot.cobraPosition.to_numpy()[np.argmin(np.hypot(dx, dy))]
        return f'x=%d. y=%d. cobraId=%d fiberId=%d' % (x, y, cobraId, fiberId)

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

    @staticmethod
    def loadTargetType(visitId):
        sql = f'select fiber_id,target_type from pfs_design_fiber ' \
              f'inner join pfs_config on pfs_config.pfs_design_id=pfs_design_fiber.pfs_design_id where visit0={visitId}'
        return ConvergencePlot.db.fetch_query(sql)

    @staticmethod
    def getPfsDesignId(visitId):
        visitId = int(visitId)
        sql = f'select pfs_design_id from pfs_visit where pfs_visit_id={visitId}'
        [[pfsDesignId]] = ConvergencePlot.db.fetch_query(sql).to_numpy()
        return pfsDesignId

    @staticmethod
    def getPfsDesign(designId):
        return PfsDesign.read(designId, dirName='/data/pfsDesign')

    def addTargetInfo(self, iterData, targetType):
        """add target information."""
        iterData = iterData.copy()
        iterData['fiberId'] = self.cobraPosition.fiberId.to_numpy()
        iterData['targetType'] = targetType.set_index('fiber_id').loc[self.cobraPosition.fiberId.to_numpy()].to_numpy()
        return iterData

    def chosenConvergence(self, convergenceData, visitId):
        """The user might choose another visitId."""
        if visitId == -1:
            return convergenceData

        return self.loadConvergence(visitId)['convergeData']

    def initialize(self):
        """Initialize your axes and colorbar"""
        self.colorbar = None
        ax = self.fig.add_subplot(111)
        return ax

    def identify(self, keyvar):
        """load the convergence data"""
        try:
            designId, visit, status = keyvar.getValue()
        except ValueError:
            visit = 0

        return self.loadConvergence(visit)

    def plot(self, convergeData, *args, **kwargs):
        """Plot the latest dataset."""
        pass

    def reloadDesign(self, visitId):
        """Reload PfsDesign"""
        pfsDesignId = ConvergencePlot.getPfsDesignId(visitId)

        if not self.pfsDesign or self.pfsDesign.pfsDesignId != pfsDesignId:
            self.pfsDesign = ConvergencePlot.getPfsDesign(pfsDesignId)

        return self.pfsDesign
