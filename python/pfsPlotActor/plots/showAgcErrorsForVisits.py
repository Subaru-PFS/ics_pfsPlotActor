from importlib import reload

import pfsPlotActor.utils.ag as agUtils
import pfs.drp.stella.utils.guiders as guiders

reload(agUtils)


class showAgcErrorsForVisits(agUtils.AgPlot):
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
    def initialize(self):
        """Initialize your axes"""
        ax1 = self.fig.add_subplot(311)
        ax2 = self.fig.add_subplot(312, sharex=ax1)
        ax3 = self.fig.add_subplot(313, sharex=ax1)
        return [ax1, ax2, ax3]


    def plot(self, latestVisitId, visitId=-1, includeAllVisitsInGroup=True):
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
        agcData = self.selectData(latestVisitId, visitId=visitId, includeAllVisitsInGroup=includeAllVisitsInGroup)

        if not len(agcData):
            return

        # Call the plotting routine
        guiders.showAgcErrorsForVisits(agcData, livePlot=self)
