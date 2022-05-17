from importlib import reload

import numpy as np
import pfsPlotActor.utils.pfi as pfiUtils

reload(pfiUtils)


class ConvergenceMap(pfiUtils.ConvergencePlot):

    def plot(self, convergeData, nIter=-1, vmin='auto', vmax='auto'):
        """Plot the latest dataset."""
        fig = self.fig
        ax = self.axes[0]

        [visitId] = convergeData.pfs_visit_id.unique()
        nIter = convergeData.iteration.max() if nIter == -1 else nIter

        # filter the dataframe for the iteration value
        iterData = convergeData.query(f'iteration=={nIter}')
        if iterData.empty:
            return

        # calculate distance from targets at this iteration
        dx = iterData.pfi_center_x_mm - iterData.pfi_target_x_mm
        dy = iterData.pfi_center_y_mm - iterData.pfi_target_y_mm
        dist = np.hypot(dx, dy)

        vmin = min(dist) if vmin == 'auto' else float(vmin)
        vmax = max(dist) if vmax == 'auto' else float(vmax)

        sc = ax.scatter(self.calibModel.centers.real[iterData['cobra_id'].values - 1],
                        self.calibModel.centers.imag[iterData['cobra_id'].values - 1], c=dist, marker='o', s=20,
                        vmin=vmin, vmax=vmax)

        if self.colorbar is None:
            # creating new colorbar.
            self.colorbar = fig.colorbar(sc, ax=ax)

        else:
            # or update existing one.
            self.colorbar.update_normal(sc)

        # some labels
        ax.set_xlabel("X (mm)")
        ax.set_ylabel("Y (mm)")

        # label with the pfsvisit Id
        tString = f'pfsVisitId = {visitId:d}, iteration = {nIter:d}'
        ax.set_title(tString)

        ax.set_aspect('equal')
        ax.format_coord = self.cobraIdFiberIdFormatter
