from importlib import reload

import pfs.drp.stella.utils.guiders as guiders
import pfsPlotActor.utils.ag as agUtils
from matplotlib.gridspec import GridSpec

reload(agUtils)


class ShowGuiderErrorsCombined(agUtils.AgPlot):
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
    units = dict(maxGuideError='microns', maxPosError='microns', guideErrorEstimate='microns')

    def initialize(self):
        """Initialize your axes"""
        self.colorbar = None
        # gs = GridSpec(3, 5, figure=self.fig)  # 3 rows and 5 columns
        #
        # # Define the first three subplots (1 row, 2 columns each)
        # ax1 = self.fig.add_subplot(gs[0, 0:2])  # First row, first 2 columns
        # ax2 = self.fig.add_subplot(gs[1, 0:2])  # Second row, first 2 columns
        # ax3 = self.fig.add_subplot(gs[2, 0:2])  # Third row, first 2 columns
        # Define the large subplot (3 rows, 3 columns)
        # ax4 = fig.add_subplot(gs[:, 2:])  # All rows, last 3 columns

        gs = GridSpec(3, 2, figure=self.fig)  # 3 rows and 5 columns

        # Define the first three subplots (1 row, 2 columns each)
        ax1 = self.fig.add_subplot(gs[0, 0])  # First row, first 2 columns
        ax2 = self.fig.add_subplot(gs[1, 0])  # Second row, first 2 columns
        ax3 = self.fig.add_subplot(gs[2, 0])  # Third row, first 2 columns
        # Define the large subplot (3 rows, 3 columns)
        ax4 = self.fig.add_subplot(gs[:, 1])  # All rows, last 3 columns

        return [ax1, ax2, ax3, ax4]

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
             maxGuideError=100,
             maxPosError=40,
             guideErrorEstimate=50,
             pfiScaleReduction=1,
             gstarExpansion=10,
             agc_exposure_idsStride=1,
             guide_star_frac=0.3):
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

        # Call both plotting routines

        guiders.showAgcErrorsForVisits(agcData, livePlot=self)
        guiders.showGuiderErrors(agcData, config=config, livePlot=self)
        self.fig.tight_layout()
