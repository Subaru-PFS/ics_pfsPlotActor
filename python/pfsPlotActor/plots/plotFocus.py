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
    noCallback = True
    def initialize(self):
        """Initialize your axes"""
        # Define the first three subplots (1 row, 2 columns each)
        axs = self.fig.subplots(2, 1, sharex=True, height_ratios=[2, 3], squeeze=False)
        axs = axs.flatten()
        # self.fig.subplots_adjust(hspace=0.025)

        return axs

    def plot(self, lastFocusVisit, visit=-1, plotBy="focus",
             colorBy="camera",
             showPfiFocusPosition=False,
             averageByFocusPosition=False,
             showMedian=False,
             showOnlyMedian=False,
             connectMedian=True,
             showCameraId=False,
             showFocusSets=False,
             onlyGuideStars=True,
             plotFrac=1,
             ditherScale=5e-3,
             yLimitsMicron=180,
             useTraceRadius=True,
             magMin='None',
             magMax='None',
             minFWHM='None',
             maxFWHM='None',
             mmToMicrons=1e3,
             useM2Off3=True,
             forceAlpha='None', *args, **kwargs):
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
        visit = self.selectVisit(lastFocusVisit, visitId=visit)
        visits = [visit]

        showAGActorFocus = False
        showOpdbFocus = True
        showFWHM = True

        magMin = None if magMin == 'None' else None
        magMax = None if magMax == 'None' else None
        minFWHM = None if minFWHM == 'None' else None
        maxFWHM = None if maxFWHM == 'None' else None
        forceAlpha = None if forceAlpha == 'None' else None

        AGC = [1, 2, 3, 4, 5, 6]

        print('visit=', visit)

        guiders.plotFocus(self.opdb, visits, AGC, plotBy=plotBy,
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

    def identify(self, keyvar):
        """load the ag data"""
        # if no callback just return.

        sql = """SELECT max(pfs_visit_id) FROM visit_set INNER JOIN iic_sequence """ \
              """ON visit_set.iic_sequence_id = iic_sequence.iic_sequence_id """ \
              """WHERE iic_sequence.sequence_type = 'agFocusSweep'"""

        lastFocusVisit = sysUtils.pd_read_sql(sql, agUtils.AgPlot.opdb).squeeze()

        return dict(lastFocusVisit=lastFocusVisit)

    def selectVisit(self, lastFocusVisit, visitId):
        """The user might choose another visitId."""
        if visitId == -1:
            return lastFocusVisit

        return visitId
