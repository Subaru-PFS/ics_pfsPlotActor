import pfs.drp.qa.guiders.analysis as guiderAnalysis
import pfs.drp.qa.guiders.plotting as guiderPlotting
import pfs.drp.qa.guiders.queries as guiderQueries
import pfsPlotActor.livePlot as livePlot
from pfs.utils.database import opdb as opdbIO


class AgPlot(livePlot.LivePlot):
    key = 'guideErrors'
    # needs to be overridden by the user.
    actor = 'ag'

    opdb = opdbIO.OpDB()

    @staticmethod
    def readData(visitId, includeAllVisitsInGroup=False):
        """Read the AG data of a visit, or of every visit in its group.

        One row per matched spot, sorted by exposure, camera and spot, in hardware coordinates.
        """
        visits = AgPlot.getAllVisits(visitId, includeAllVisitsInGroup=includeAllVisitsInGroup)
        return AgPlot.readAgcData(visits)

    @staticmethod
    def readAgcData(visits):
        """Read the AG data of some visits; see pfs.drp.qa.guiders.queries.readAgcData."""
        return guiderQueries.readAgcData(AgPlot.opdb, visits)

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
                visits = sorted(set(visits))

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

    def showGuiderErrors(self, agcData, ax, fitConfig, plotConfig):
        """Fit the guider models to agcData and draw the guide stars' offsets on ax.

        The colorbar is kept on the plot and updated on each redraw, rather than added again.
        """
        fit = guiderAnalysis.fitGuiderModel(agcData, fitConfig)
        colorbars = None if self.colorbar is None else (self.colorbar,)
        drawn = guiderPlotting.showGuiderErrors(fit, plotConfig, ax=ax, colorbars=colorbars)
        if drawn.colorbars:
            [self.colorbar] = drawn.colorbars

        return drawn


def guiderConfigs(showAverageGuideStarPos, showAverageGuideStarPath, showGuideStars, showGuideStarsAsPoints,
                  showGuideStarsAsArrows, showGuideStarPositions, rotateToAG1Down, modelBoresightOffset,
                  modelCCDOffset, solveForAGTransforms, onlyShutterOpen, maxGuideError, maxPosError,
                  guideErrorEstimate, pfiScaleReduction, gstarExpansion, agc_exposure_idsStride, guide_star_frac):
    """Split the guider-error tweaks into drp_qa's fit and plot configs.

    The tweaks keep drp_stella's GuiderConfig names, which the GUI shows; drp_qa renames them.
    """
    fitConfig = guiderAnalysis.GuiderFitConfig(
        modelBoresightOffset=modelBoresightOffset,
        modelCCDOffset=modelCCDOffset,
        solveForAGTransforms=solveForAGTransforms,
        onlyShutterOpen=onlyShutterOpen,
        maxGuideError_um=maxGuideError,
        maxPosError_um=maxPosError,
        agcExposureStride=agc_exposure_idsStride,
    )
    plotConfig = guiderPlotting.GuiderPlotConfig(
        showGuideStars=showGuideStars,
        showGuideStarsAsPoints=showGuideStarsAsPoints,
        showGuideStarsAsArrows=showGuideStarsAsArrows,
        showGuideStarPositions=showGuideStarPositions,
        showAverageGuideStarPos=showAverageGuideStarPos,
        showAverageGuideStarPath=showAverageGuideStarPath,
        rotateToAG1Down=rotateToAG1Down,
        guideErrorEstimate_um=guideErrorEstimate,
        pfiScaleReduction=pfiScaleReduction,
        gstarExpansion=gstarExpansion,
        guideStarFrac=guide_star_frac,
    )

    return fitConfig, plotConfig
