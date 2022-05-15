from importlib import reload

import numpy as np
import pfsPlotActor.utils.pfi as pfiUtils

reload(pfiUtils)


class SpotSize(pfiUtils.ConvergencePlot):
    key = 'convergenceId'
    # needs to be overridden by the user.
    actor = 'tests'

    def initialize(self):
        """Initialize your axes and colorbar"""
        self.colorbar = None
        ax1 = [self.fig.add_subplot(211)]
        ax2 = [self.fig.add_subplot(212)]
        return ax1 + ax2

    def plot(self, convergeData, vmin='auto', vmax='auto'):
        """Plot the latest dataset."""
        fig = self.fig
        ax1 = self.axes[0]
        ax2 = self.axes[1]

        [visitId] = convergeData.pfs_visit_id.unique()

        # calculate the average brightness over the convergence
        perCobra = convergeData.groupby('cobra_id').mean()
        fx = perCobra.mcs_second_moment_x_pix
        fy = perCobra.mcs_second_moment_y_pix
        cInd = perCobra.index.to_numpy() - 1

        # set the same range for both plots
        cRange = np.array([fx, fy])
        std = np.nanstd(cRange)
        avg = np.nanmean(cRange)

        vmin = avg - 3 * std if vmin == 'auto' else vmin
        vmax = avg + 3 * std if vmax == 'auto' else vmax

        # do the scatter plots
        sc = ax1.scatter(self.calibModel.centers.real[cInd], self.calibModel.centers.imag[cInd], c=fx, s=20, vmin=vmin,
                         vmax=vmax)
        sc = ax2.scatter(self.calibModel.centers.real[cInd], self.calibModel.centers.imag[cInd], c=fy, s=20, vmin=vmin,
                         vmax=vmax)

        # some labels
        ax1.set_aspect('equal')
        ax2.set_aspect('equal')
        ax1.set_title("Spot Size (x)")
        ax2.set_title("Spot Size (y)")
        ax1.set_xlabel("X (mm)")
        ax1.set_xlabel("X (mm)")
        ax1.set_ylabel("Y (mm)")

        ax1.format_coord = pfiUtils.cobraIdFiberIdFormatter
        ax2.format_coord = pfiUtils.cobraIdFiberIdFormatter

        # colour bar stuff
        if self.colorbar is None:
            # creating new colorbar.
            fig.subplots_adjust(right=0.8)
            cbar_ax = fig.add_axes([0.82, 0.15, 0.03, 0.7])
            self.colorbar = fig.colorbar(sc, cax=cbar_ax)
        else:
            # or update existing one.
            self.colorbar.update_normal(sc)

        # label with the pfsvisit Id
        tString = f'Spot Size: pfsVisitId = {visitId:d}'
        fig.suptitle(tString)
