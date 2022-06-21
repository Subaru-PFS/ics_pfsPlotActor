from importlib import reload

import matplotlib.pyplot as plt
import numpy as np
import pfsPlotActor.utils.pfi as pfiUtils

reload(pfiUtils)


class ConvergenceHist(pfiUtils.ConvergencePlot):

    def plot(self, convergeData, vmin=0, vmax=0.03, bins=30, minIter=4):
        """Plot the latest dataset."""
        fig = self.fig
        ax = self.axes[0]
        cmap = plt.get_cmap('viridis')

        [visitId] = convergeData.pfs_visit_id.unique()
        convergeData = convergeData.query(f'iteration>={minIter - 1}')
        cmap = cmap(np.linspace(1.0, 0, len(convergeData.iteration.unique())))

        for i, (iterVal, iterData) in enumerate(convergeData.groupby('iteration')):
            dx = iterData.pfi_center_x_mm - iterData.pfi_target_x_mm
            dy = iterData.pfi_center_y_mm - iterData.pfi_target_y_mm
            dist = np.hypot(dx, dy)

            n, bins, patches = ax.hist(dist, alpha=0.6, histtype='step', linewidth=3,
                                       label=f'{iterVal + 1}-th Iteration', bins=bins, range=(vmin, vmax),
                                       color=cmap[i])

        ax.legend(loc='upper right')
        ax.set_title(f"Distance to Target: pfsVisitId = {visitId:d}")
        ax.set_xlabel("Distance (mm)")
        ax.set_ylabel("N")
        ax.set_aspect('auto')
        ax.grid()
