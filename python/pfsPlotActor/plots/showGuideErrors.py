from importlib import reload

import pfsPlotActor.utils.ag as agUtils
import pfs.drp.stella.utils.guiders as guiders

reload(agUtils)


class ShowGuideErrors(agUtils.AgPlot):
    """
    A class to visualize and plot guiding errors using AGC data.

    This class utilizes the GuiderConfig object to configure various
    plotting options and visualizations for guide star data collected by
    the AG cameras.

    Attributes:
    -----------
    fig : matplotlib.figure.Figure
        Figure object used for plotting.
    axes : list of matplotlib.axes.Axes
        List of axes used for plotting.
    """

    def plot(self, agcData, visitId=-1,
             showAverageGuideStarPos=False,
             showAverageGuideStarPath=False,
             showGuideStars=True,
             showGuideStarsAsPoints=True,
             showGuideStarsAsArrows=False,
             showGuideStarPositions=False,
             rotateToAG1Down=False,
             modelBoresightOffset=False,
             modelCCDOffset=False,
             solveForAGTransforms=False,
             onlyShutterOpen=True,
             maxGuideError=25,
             maxPosError=40,
             guideErrorEstimate=50,
             pfiScaleReduction=1,
             gstarExpansion=10,
             agc_exposure_idsStride=1,
             guide_star_frac=0.1):
        """
        Configure the GuiderConfig object and call the plotting routine.

        Parameters:
        -----------
        agcData : pandas.DataFrame
            DataFrame containing the AGC data to plot.
        visitId : int, optional
            ID of the visit being processed (default: -1).
        All other parameters correspond to GuiderConfig settings.
        """
        agcData = self.selectData(agcData, visitId=visitId)

        if not len(agcData):
            return

        # Instantiate a GuiderConfig object with the given settings
        config = guiders.GuiderConfig(
            showAverageGuideStarPos=showAverageGuideStarPos,
            showAverageGuideStarPath=showAverageGuideStarPath,
            showGuideStars=showGuideStars,
            showGuideStarsAsPoints=showGuideStarsAsPoints,
            showGuideStarsAsArrows=showGuideStarsAsArrows,
            showGuideStarPositions=showGuideStarPositions,
            rotateToAG1Down=rotateToAG1Down,
            modelBoresightOffset=modelBoresightOffset,
            modelCCDOffset=modelCCDOffset,
            solveForAGTransforms=solveForAGTransforms,
            onlyShutterOpen=onlyShutterOpen,
            maxGuideError=maxGuideError,
            maxPosError=maxPosError,
            guideErrorEstimate=guideErrorEstimate,
            pfiScaleReduction=pfiScaleReduction,
            gstarExpansion=gstarExpansion,
            agc_exposure_idsStride=agc_exposure_idsStride,
            guide_star_frac=guide_star_frac,
        )

        # Call the plotting routine
        guiders.showGuiderErrors(agcData, config=config, livePlot=self)
