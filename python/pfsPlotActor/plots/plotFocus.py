from importlib import reload

import pfs.drp.stella.utils.guiders as guiders
import pfsPlotActor.utils.ag as agUtils

reload(agUtils)


class FocusPlot(agUtils.AgPlot):
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
    noCallback = True
    units = dict(maxGuideError='microns', maxPosError='microns', guideErrorEstimate='microns')

    def initialize(self):
        """Initialize your axes"""
        self.colorbar = None

        # Define the first three subplots (1 row, 2 columns each)
        axs = self.fig.subplots(2, 1, sharex=True, height_ratios=[2, 3], squeeze=False)
        axs = axs.flatten()
        # self.fig.subplots_adjust(hspace=0.025)

        return axs

    def plot(self, visit=125468, plotBy="focus", colorBy="camera", averageByFocusPosition=False, yLimitsMicron=170,
             showMedian=False, showOnlyMedian=False, showCameraId=False, minFWHM=0.3, maxFWHM=1.59,
             useTraceRadius=False, *args, **kwargs):
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
        visits = [visit]
        # plotBy = "agc_exposure_id"
        # plotBy = "focus"
        # plotBy = "insrot"
        # plotBy = "altitude"
        # colorBy = "camera"
        # colorBy = "altitude"
        # colorBy = "insrot"
        showAGActorFocus = False
        showOpdbFocus = True
        showFWHM = True  # or plotBy == "focus"
        # averageByFocusPosition = False
        # yLimitsMicron = 170  # (-150, 150)                  # if >= 0, set focus error scale to +- yLimitsMicron (or the given tuple)
        # FWHM panel:
        # showMedian = False
        # showOnlyMedian = False
        # showCameraId = False  # if False, plot left/right
        # minFWHM = None if False else 0.3
        # maxFWHM = None if False else 1.59
        # useTraceRadius = False
        showFocusSets = plotBy == "agc_exposure_id"
        AGC = [1, 2, 3, 4, 5, 6]
        # AGC = [agc for agc in AGC if agc not in [1, 2 ]]
        # AGC = [3, 6]
        guiders.plotFocus(self.opdb, visits, AGC, plotBy=plotBy, colorBy=colorBy,
                          showAGActorFocus=showAGActorFocus, showOpdbFocus=showOpdbFocus, showFWHM=showFWHM,
                          # magMax=19, magMin=18,
                          showMedian=showMedian, showOnlyMedian=showOnlyMedian, showCameraId=showCameraId,
                          # butler=butler, # ditherScale=0,
                          averageByFocusPosition=averageByFocusPosition, onlyGuideStars=True,
                          showFocusSets=showFocusSets, useTraceRadius=useTraceRadius,
                          yLimitsMicron=yLimitsMicron, minFWHM=minFWHM, maxFWHM=maxFWHM, useM2Off3=True, forceAlpha=0.5,
                          figure=self.fig, livePlot=self)

        self.fig.tight_layout()
