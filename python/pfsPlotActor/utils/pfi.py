import numpy as np
import pfs.drp.stella.utils.sysUtils as sysUtils
import pfsPlotActor.livePlot as livePlot
from pfs.datamodel import PfsDesign
from pfsPlotActor.utils.sgfm import sgfm


class ConvergencePlot(livePlot.LivePlot):
    key = 'pfsConfig'
    # needs to be overridden by the user.
    actor = 'fps'

    opdb = livePlot.LivePlot.getConn()

    badIdx = sgfm[~sgfm.COBRA_OK_MASK].index.to_numpy()
    goodIdx = sgfm[sgfm.COBRA_OK_MASK].index.to_numpy()

    pfsDesign = None

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
        """
        visitId = int(visitId)

        sql = f'select cm.pfs_visit_id, cm.iteration, cm.cobra_id, cm.pfi_center_x_mm, cm.pfi_center_y_mm, ' \
              f'ct.pfi_target_x_mm, ct.pfi_target_y_mm, md.mcs_center_x_pix, md.mcs_center_y_pix, ' \
              f'md.mcs_second_moment_x_pix,md.mcs_second_moment_y_pix, md.peakvalue  from cobra_match ' \
              f'cm inner join cobra_target ct on ct.pfs_visit_id = cm.pfs_visit_id and ct.iteration = ' \
              f'cm.iteration and ct.cobra_id = cm.cobra_id inner join mcs_data md ' \
              f'on md.mcs_frame_id = cm.pfs_visit_id * 100 + cm.iteration and md.spot_id = cm.spot_id where cm.pfs_visit_id = {visitId} order by ct.cobra_id, ct.iteration'

        # get data
        return sysUtils.pd_read_sql(sql, ConvergencePlot.opdb)

    @staticmethod
    def loadPfsConfigFromDB(visitId):
        sql = (
            "SELECT pcf.fiber_id, pdf.target_type, pcf.fiber_status "
            "FROM pfs_config AS pc "
            "INNER JOIN pfs_config_fiber AS pcf "
            "ON pcf.pfs_design_id = pc.pfs_design_id AND pcf.visit0 = pc.visit0 "
            "INNER JOIN pfs_design_fiber AS pdf "
            "ON pdf.pfs_design_id = pc.pfs_design_id AND pdf.fiber_id = pcf.fiber_id "
            f"WHERE pc.visit0 = {visitId}"
        )

        return sysUtils.pd_read_sql(sql, ConvergencePlot.opdb).set_index('fiber_id').sort_index()

    @staticmethod
    def getPfsDesignId(visitId):
        visitId = int(visitId)
        sql = f'select pfs_design_id from pfs_visit where pfs_visit_id={visitId}'
        [[pfsDesignId]] = sysUtils.pd_read_sql(sql, ConvergencePlot.opdb).to_numpy()
        return pfsDesignId

    @staticmethod
    def getFiducialData(visitId):
        sql = f'SELECT * from fiducial_fiber_match WHERE pfs_visit_id={visitId}'
        return sysUtils.pd_read_sql(sql, ConvergencePlot.opdb)

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
