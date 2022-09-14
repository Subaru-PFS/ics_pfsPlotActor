from importlib import reload

import numpy as np
import pfsPlotActor.utils.pfi as pfiUtils

reload(pfiUtils)


class SeeingData(pfiUtils.ConvergencePlot):

    """
    calculate and plot the results of a seeing test. Data can be loaded the same way
    as for convergence data, only in this case the cobras aren't moving. 

    Two plots are produced, a colour map, and a histogram. The same vmin, vmax
    are used for both plots. 

    Note that this assumes that the pixel -> mm coordinate
    transformation has been updated for each frame; if it has only
    been done at the beginning of the sequence the values will be very
    dominated by the translation/scaling effect from frame to frame.
    """

    def initialize(self):
        """Initialize your axes and colorbar"""
        self.colorbar = None
        ax1 = [self.fig.add_subplot(211)]
        ax2 = [self.fig.add_subplot(212)]
        return ax1 + ax2
        
    
    def plot(self, convergeData, vmin='auto', vmax='auto'):
        """Plot the latest dataset."""
        fig = self.fig
        ax = self.axes[0]

        [visitId] = convergeData.pfs_visit_id.unique()
        nIter = convergeData.iteration.max()

        # use the centre points as reference
        cPosX = self.calibModel.centers.real[self.goodIdx]
        cPosY = self.calibModel.centers.imag[self.goodIdx]

        # array for the differences
        diffX = np.zeros(len(self.goodIdx),nIter)
        diffY = np.zeros(len(self.goodIdx),nIter)

        # calculate offset from reference position for each iteration
        for i in range(nIter):

            # filter data by iteration, sort by cobra_id, and filter out bad cobras
            iterData = convergeData.query(f'iteration=={nIter}').sort_values(by='cobra_id').loc(self.goodIdx).reset_index()
            diffX[:,i] = iterData.pfi_center_x_mm - cPosX
            diffY[:,i] = iterData.pfi_center_y_mm - cPosY
            diff[:,i] = np.sqrt(diffX[:,i]**2+diffY[:,i]**2)

        # and the RMS
        rmsVal=dd.std(axis=1)

        # converting to microns
        rmsVal *= 1000

        
        vmin = min(rmsVal) if vmin == 'auto' else float(vmin)
        vmax = max(rmsVal) if vmax == 'auto' else float(vmax)


        sc = ax.scatter(self.calibModel.centers.real[iterData['cobra_id'].values - 1],
                        self.calibModel.centers.imag[iterData['cobra_id'].values - 1], c=rmsVal, marker='o', s=20,
                        vmin=vmin, vmax=vmax)

        if self.colorbar is None:
            # creating new colorbar.
            self.colorbar = fig.colorbar(sc, ax=ax)

        else:
            # or update existing one.
            self.colorbar.update_normal(sc)

        # some labels
        ax1.set_xlabel("X (microns)")
        ax1.set_ylabel("Y (microns)")

        # label with the pfsvisit Id
        tString = f'RMS of position: pfsVisitId = {visitId:d}, {nIter:d} iterations'
        ax1.set_title(tString)

        ax1.set_aspect('equal')
        ax.format_coord = self.cobraIdFiberIdFormatter

        #calculate the bins
        binsize=(vmax-vmin)/nbins
        bins=np.arange(plotRange[0],plotRange[1]+binsize,binsize)
        
        hi = ax2.hist(rmsVal,bins=nbins,range=(vmin,vmax))
        tString = f'meanRMS = {rmsVal.mean()} microns'
        ax2.set_title(tString)
        ax2.set_xlabel('RMS (microns)')
        ax2.set_ylabel("N")


