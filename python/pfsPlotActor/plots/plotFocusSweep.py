from importlib import reload

import pfs.drp.stella.utils.guiders as guiders
import pfs.drp.stella.utils.sysUtils as sysUtils
import pfsPlotActor.utils.ag as agUtils

reload(agUtils)


class FocusSweepPlot(agUtils.AgPlot):
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

        # Define the first three subplots (1 row, 2 columns each)
        axs = self.fig.subplots(2, 1, sharex=True, height_ratios=[2, 3], squeeze=False)
        axs = axs.flatten()
        # self.fig.subplots_adjust(hspace=0.025)

        return axs

    def plot(self, latestFocusVisitId, visitId=-1, plotBy="focus",
             colorBy="camera",
             showPfiFocusPosition=False,
             averageByFocusPosition=False,
             showMedian=True,
             showOnlyMedian=False,
             connectMedian=False,
             showCameraId=False,
             showFocusSets=False,
             onlyGuideStars=True,
             plotFrac=1,
             ditherScale=5e-3,
             yLimitsMicron=220,
             useTraceRadius=True,
             magMin='None',
             magMax='None',
             minFWHM=0.45,
             maxFWHM=1.95,
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
        visit = self.selectVisit(latestFocusVisitId, visitId=visitId)
        visits = [visit]

        showAGActorFocus = False
        showOpdbFocus = True
        showFWHM = True

        magMin = None if magMin == 'None' else float(magMin)
        magMax = None if magMax == 'None' else float(magMax)
        forceAlpha = None if forceAlpha == 'None' else float(forceAlpha)

        AGC = [1, 2, 3, 4, 5, 6]

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

    def identify(self, keyvar, newValue):
        """load the ag data"""
        # if no callback just return.
        if newValue:
            exposureId, dRA, dDec, dInR, dAz, dAlt, dZ, dScale = keyvar.getValue()
            sql = f'select pfs_visit_id from agc_exposure where agc_exposure_id={exposureId}'
            [visitId, ] = sysUtils.pd_read_sql(sql, agUtils.AgPlot.opdb).pfs_visit_id.to_numpy()

            sql = f"""select pfs_visit_id FROM visit_set INNER JOIN iic_sequence ON """ \
                  """visit_set.iic_sequence_id = iic_sequence.iic_sequence_id """ \
                  f"""WHERE iic_sequence.sequence_type = 'agFocusSweep' and pfs_visit_id={visitId}"""

            if not len(sysUtils.pd_read_sql(sql, agUtils.AgPlot.opdb)):
                return dict(skipPlotting=True)

        sql = """SELECT max(pfs_visit_id) FROM visit_set INNER JOIN iic_sequence """ \
              """ON visit_set.iic_sequence_id = iic_sequence.iic_sequence_id """ \
              """WHERE iic_sequence.sequence_type = 'agFocusSweep'"""

        lastFocusVisit = sysUtils.pd_read_sql(sql, agUtils.AgPlot.opdb).squeeze()

        return dict(dataId=lastFocusVisit)

    def selectVisit(self, latestFocusVisitId, visitId):
        """The user might choose another visitId."""
        selectedVisit = latestFocusVisitId if visitId == -1 else visitId
        selectedVisit = -1 if selectedVisit is None else selectedVisit

        return selectedVisit
