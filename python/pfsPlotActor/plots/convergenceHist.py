from importlib import reload

import numpy as np
import pfsPlotActor.utils.pfi as pfiUtils

reload(pfiUtils)


class ConvergenceHist(pfiUtils.ConvergencePlot):

    def plot(self, convergeData, vmin=0, vmax=0.1, bins=20, minIter=4):
        """Plot the latest dataset."""
        fig = self.fig
        ax = self.axes[0]
        [visitId] = convergeData.pfs_visit_id.unique()
        nIter = convergeData.iteration.max()

        for iterVal in range(nIter):
            if iterVal < minIter - 1:
                continue

            iterData = convergeData.query(f'iteration=={iterVal}')
            dx = iterData.pfi_center_x_mm - iterData.pfi_target_x_mm
            dy = iterData.pfi_center_y_mm - iterData.pfi_target_y_mm
            dist = np.hypot(dx, dy)

            n, bins, patches = ax.hist(dist, alpha=0.7, histtype='step', linewidth=3,
                                       label=f'{iterVal + 1}-th Iteration', bins=bins, range=(vmin, vmax))

            ax.legend(loc='upper right')
            ax.set_title(f"Distance to Target: pfsVisitId = {visitId:d}")
            ax.set_xlabel("Distance (mm)")
            ax.set_ylabel("N")
            ax.set_aspect('auto')
