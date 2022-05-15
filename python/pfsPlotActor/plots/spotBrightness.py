from importlib import reload

import pfsPlotActor.utils.pfi as pfiUtils

reload(pfiUtils)


class SpotBrightness(pfiUtils.ConvergencePlot):
    key = 'convergenceId'
    # needs to be overridden by the user.
    actor = 'tests'

    def plot(self, convergeData, vmin='auto', vmax='auto'):
        """Plot the latest dataset."""
        fig = self.fig
        ax = self.axes[0]

        [visitId] = convergeData.pfs_visit_id.unique()

        # calculate the average brightness over the convergence
        peak = convergeData.groupby('cobra_id').peakvalue.mean()
        cInd = peak.index.to_numpy() - 1

        vmin = min(peak) if vmin == 'auto' else vmin
        vmax = max(peak) if vmax == 'auto' else vmax

        # do a scatter plot
        sc = ax.scatter(self.calibModel.centers.real[cInd], self.calibModel.centers.imag[cInd], c=peak, s=20, vmin=vmin,
                        vmax=vmax)

        if self.colorbar is None:
            # creating new colorbar.
            self.colorbar = fig.colorbar(sc, ax=ax)

        else:
            # or update existing one.
            self.colorbar.update_normal(sc)

        # label with the pfsvisit Id
        tString = f'Spot Brightness: pfsVisitId = {visitId:d}'
        ax.set_title(tString)
        ax.set_xlabel("X (mm)")
        ax.set_ylabel("Y (mm)")
        ax.set_aspect('equal')
        ax.format_coord = pfiUtils.cobraIdFiberIdFormatter
