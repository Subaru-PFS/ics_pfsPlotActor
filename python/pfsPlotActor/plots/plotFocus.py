import hashlib
import pickle
from importlib import reload

import pfs.drp.qa.guiders.plotting as guiderPlotting
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
        self.cacheKey = None
        self.agcData = None
        self.visits = None

        # Define the first three subplots (1 row, 2 columns each)
        axs = self.fig.subplots(1, 1, sharex=True, height_ratios=[2], squeeze=False)
        axs = axs.flatten()
        # self.fig.subplots_adjust(hspace=0.025)

        return axs

    def identify(self, keyvar, newValue):
        """load the ag data"""
        visitId, camList, camMask = keyvar.getValue()
        sql = f'select exp_type from sps_visit where pfs_visit_id={visitId}'
        exptype = agUtils.AgPlot.opdb.query_dataframe(sql).squeeze()

        if newValue and exptype != 'object':
            return dict(skipPlotting=True, newValue=newValue)

        else:
            sql = f"select max(pfs_visit_id) from sps_visit where exp_type='object'"
            visitId = agUtils.AgPlot.opdb.query_dataframe(sql).squeeze()

        return dict(dataId=visitId, newValue=newValue)

    def getCacheKey(self, params: dict) -> str:
        """
        Generate a stable cache key based on relevant parameters.

        Parameters
        ----------
        params : dict
            Dictionary of keyword arguments that affect plotting behavior.

        Returns
        -------
        str
            A hexadecimal MD5 hash string representing the cache key.
        """
        return hashlib.md5(pickle.dumps(params)).hexdigest()

    def plot(self, latestSpsVisit, visitStart=-10, visitEnd=-1,
             plotBy=("agc_exposure_id", "altitude", "insrot", "focus"),
             colorBy=("camera", "visit", "altitude", "insrot"),
             showPfiFocusPosition=False,
             averageByFocusPosition=False,
             showMedian=False,
             showOnlyMedian=False,
             connectMedian=False,
             showCameraId=False,
             showFocusSets=True,
             onlyGuideStars=True,
             plotFrac=1.0,
             ditherScale=5e-3,
             yLimitsMicron=220,
             useTraceRadius=True,
             magMin='None',
             magMax='None',
             minFWHM=0.3,
             maxFWHM=1.59,
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

        showAGActorFocus = True
        showOpdbFocus = False
        showFWHM = False

        plotBy = plotBy[0] if isinstance(plotBy, tuple) else plotBy
        colorBy = colorBy[0] if isinstance(colorBy, tuple) else colorBy
        magMin = None if magMin == 'None' else float(magMin)
        magMax = None if magMax == 'None' else float(magMax)
        forceAlpha = None if forceAlpha == 'None' else float(forceAlpha)

        plotParams = dict(plotBy=plotBy,
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
                          yLimits_um=yLimitsMicron,
                          useTraceRadius=useTraceRadius,
                          magMin=magMin,
                          magMax=magMax,
                          minFWHM_arcsec=minFWHM,
                          maxFWHM_arcsec=maxFWHM,
                          useM2Off3=useM2Off3,
                          forceAlpha=forceAlpha)

        # A tweak redraws the same visits without reading them again.
        cacheKey = self.getCacheKey(plotParams)
        useCache = self.agcData is not None and visits == self.visits and cacheKey != self.cacheKey

        agcData = self.agcData if useCache else agUtils.AgPlot.readAgcData(visits)

        drawn = guiderPlotting.plotFocus(agcData, **plotParams, fig=self.fig, axes=self.axes,
                                         colorbars=self.previousColorbars())
        self.keepColorbar(drawn)

        self.fig.tight_layout()

        self.cacheKey = cacheKey
        self.agcData = agcData
        self.visits = visits

        return True
