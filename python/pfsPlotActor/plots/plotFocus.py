from importlib import reload

import pfs.drp.stella.utils.guiders as guiders
import pfs.drp.stella.utils.sysUtils as sysUtils
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
    units = dict(maxGuideError='microns', maxPosError='microns', guideErrorEstimate='microns')

    actor = 'sps'
    key = 'fileIds'

    def initialize(self):
        """Initialize your axes"""
        self.colorbar = None

        # Define the first three subplots (1 row, 2 columns each)
        axs = self.fig.subplots(1, 1, sharex=True, height_ratios=[2], squeeze=False)
        axs = axs.flatten()
        # self.fig.subplots_adjust(hspace=0.025)

        return axs

    def plot(self, latestSpsVisit, visitStart=-10, visitEnd=-1, plotBy="agc_exposure_id",
             colorBy="camera",
             showPfiFocusPosition=False,
             averageByFocusPosition=False,
             showMedian=False,
             showOnlyMedian=False,
             connectMedian=False,
             showCameraId=False,
             showFocusSets=True,
             onlyGuideStars=True,
             plotFrac=1,
             ditherScale=5e-3,
             yLimitsMicron=220,
             useTraceRadius=True,
             magMin='None',
             magMax='None',
             minFWHM=0.3,
             maxFWHM=1.59,
             mmToMicrons=1e3,
             useM2Off3=True,
             forceAlpha=0.5, *args, **kwargs):
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
        visitEnd = self.selectVisit(latestSpsVisit, visitEnd)
        visitStart = visitEnd + visitStart if visitStart < 0 else visitStart
        visits = list(range(visitStart, visitEnd + 1))

        showAGActorFocus = False
        showOpdbFocus = True
        showFWHM = False

        magMin = None if magMin == 'None' else float(magMin)
        magMax = None if magMax == 'None' else float(magMax)
        forceAlpha = None if forceAlpha == 'None' else float(forceAlpha)

        AGC = [1, 2, 3, 4, 5, 6]

        guiders.plotFocus(self.opdb, visits, AGC=AGC, plotBy=plotBy,
                          colorBy=colorBy,
                          showAGActorFocus=showAGActorFocus,
                          showOpdbFocus=showOpdbFocus,
                          showFWHM=showFWHM,
                          showPfiFocusPosition=showPfiFocusPosition,
                          averageByFocusPosition=averageByFocusPosition,
                          showMedian=showMedian,
                          showOnlyMedian=showOnlyMedian,
                          connectMedian=connectMedian,
                          showCameraId=showCameraId,
                          showFocusSets=showFocusSets,
                          onlyGuideStars=onlyGuideStars,
                          plotFrac=plotFrac,
                          ditherScale=ditherScale,
                          yLimitsMicron=yLimitsMicron,
                          useTraceRadius=useTraceRadius,
                          magMin=magMin,
                          magMax=magMax,
                          minFWHM=minFWHM,
                          maxFWHM=maxFWHM,
                          mmToMicrons=mmToMicrons,
                          useM2Off3=useM2Off3,
                          forceAlpha=forceAlpha,
                          figure=self.fig, axes=self.axes)

        self.fig.tight_layout()

    def selectVisit(self, latestVisit, visitId):
        """The user might choose another visitId."""
        selectedVisit = latestVisit if visitId == -1 else visitId
        selectedVisit = -1 if selectedVisit is None else selectedVisit

        return selectedVisit

    def identify(self, keyvar, newValue):
        """load the ag data"""
        visitId, camList, camMask = keyvar.getValue()
        sql = f'select exp_type from sps_visit where pfs_visit_id={visitId}'
        exptype = sysUtils.pd_read_sql(sql, agUtils.AgPlot.opdb).squeeze()

        if exptype != 'object':
            return dict(skipPlotting=True)

        return dict(dataId=visitId)
