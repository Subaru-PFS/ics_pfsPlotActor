from importlib import reload

import numpy as np
import pfsPlotActor.utils.pfi as pfiUtils

reload(pfiUtils)


class ConvergenceBool(pfiUtils.ConvergencePlot):

    def plot(self, convergeData, nIter=-1, tolerance=0.01):
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

        cobraConverged = dist <= tolerance

        # scatter plots, one colour for converged, one for non converged
        sc = ax.scatter(self.calibModel.centers.real[iterData.cobra_id.values - 1][cobraConverged],
                        self.calibModel.centers.imag[iterData.cobra_id.values - 1][cobraConverged], c='purple',
                        marker='o', s=20)
        sc = ax.scatter(self.calibModel.centers.real[iterData.cobra_id.values - 1][~cobraConverged],
                        self.calibModel.centers.imag[iterData.cobra_id.values - 1][~cobraConverged], c='green',
                        marker='o', s=20)

        # some labels
        ax.set_xlabel("X (mm)")
        ax.set_ylabel("Y (mm)")

        # label with the pfsvisit Id
        tString = f'Convergence Success: pfsVisitId = {visitId:d}, iteration = {nIter:d}'
        ax.set_title(tString)

        ax.set_aspect('equal')
        ax.format_coord = self.cobraIdFiberIdFormatter
