from importlib import reload

import matplotlib.pyplot as plt
import numpy as np
import pfsPlotActor.utils.pfi as pfiUtils

reload(pfiUtils)


class ConvergenceHist(pfiUtils.ConvergencePlot):
    units = dict(vmin='microns', vmax='microns')

    def plot(self, latestVisitId, visitId=-1, vmin=0, vmax=30, bins=30, minIter=3):
        """Plot the latest dataset."""
        fig = self.fig
        ax = self.axes[0]
        cmap = plt.get_cmap('viridis')

        # Get convergence dataframe default is latest.
        convergeData = self.selectData(latestVisitId, visitId=visitId)
        if not len(convergeData):
            return

        [visitId] = convergeData.pfs_visit_id.unique()
        convergeData = convergeData.query(f'iteration>={minIter}')
        cmap = cmap(np.linspace(1.0, 0, len(convergeData.iteration.unique())))

        for i, (iterVal, iterData) in enumerate(convergeData.groupby('iteration')):
            dx = iterData.pfi_center_x_mm - iterData.pfi_target_x_mm
            dy = iterData.pfi_center_y_mm - iterData.pfi_target_y_mm
            dist = np.hypot(dx, dy)
            # converting to microns
            dist *= 1000

            n, bins, patches = ax.hist(dist, alpha=0.6, histtype='step', linewidth=3,
                                       label=f'{iterVal}-th Iteration', bins=bins, range=(vmin, vmax),
                                       color=cmap[i])

        ax.legend(loc='upper right')
        ax.set_title(f"Distance to Target: pfsVisitId = {visitId:d}")
        ax.set_xlabel("Distance (microns)")
        ax.set_ylabel("N")
        ax.set_aspect('auto')
        ax.grid()

        return True
