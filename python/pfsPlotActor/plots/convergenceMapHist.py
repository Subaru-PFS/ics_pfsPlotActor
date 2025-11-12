from importlib import reload

import matplotlib.pyplot as plt
import numpy as np
import pfsPlotActor.utils.pfi as pfiUtils
from mpl_toolkits.axes_grid1 import make_axes_locatable
from pfs.datamodel import TargetType, FiberStatus
from pfsPlotActor.utils.sgfm import calibModel

reload(pfiUtils)


class ConvergenceMapHist(pfiUtils.ConvergencePlot):
    units = dict(vmin='microns', vmax='microns')

    def initialize(self):
        """Initialize your axes and colorbar"""
        self.colorbar = None
        ax1 = [self.fig.add_subplot(121)]
        ax2 = [self.fig.add_subplot(122)]
        return ax1 + ax2

    def plot(self, latestVisitId, visitId=-1, nIter=-1, vmin=0, vmax=30, bins=30, minIter=3, showPercentiles='75,95'):
        """Plot the latest dataset."""
        fig = self.fig
        ax1 = self.axes[0]
        ax2 = self.axes[1]

        # Get convergence dataframe default is latest.
        convergeData = self.selectData(latestVisitId, visitId=visitId)
        if not len(convergeData):
            return

        [visitId] = convergeData.pfs_visit_id.unique()
        nIter = convergeData.iteration.max() if nIter == -1 else nIter

        # filter the dataframe for the iteration value.
        iterData = convergeData.query(f'iteration=={nIter}').reset_index(drop=True)
        if iterData.empty:
            return

        pfsConfigDf = self.loadPfsConfigFromDB(visitId)
        iterData = self.addPfsConfigInfo(iterData, pfsConfigDf)

        # show broken cobras.
        bad = iterData.loc[self.badIdx]
        ax1.scatter(calibModel.centers.real[bad['cobra_id'].values - 1],
                    calibModel.centers.imag[bad['cobra_id'].values - 1], marker='x', color='k', s=20,
                    alpha=0.5)

        # show moving cobras.
        iterData = self.selectMovingCobras(iterData)

        # calculate distance from targets at this iteration.
        dx = iterData.pfi_center_x_mm - iterData.pfi_target_x_mm
        dy = iterData.pfi_center_y_mm - iterData.pfi_target_y_mm
        dist = np.hypot(dx, dy)

        # converting to microns
        dist *= 1000

        vmin = min(dist) if vmin == 'auto' else float(vmin)
        vmax = max(dist) if vmax == 'auto' else float(vmax)

        sc = ax1.scatter(calibModel.centers.real[iterData['cobra_id'].values - 1],
                         calibModel.centers.imag[iterData['cobra_id'].values - 1],
                         c=dist, marker='o', s=20, vmin=vmin, vmax=vmax)

        if self.colorbar is None:
            # creating new colorbar.
            # cbar_ax = fig.add_axes([0.45, 0.15, 0.02, 0.7])
            # self.colorbar = fig.colorbar(sc, cax=cbar_ax)
            divider = make_axes_locatable(ax1)
            cax = divider.append_axes("right", size="5%", pad=0.05)
            self.colorbar = fig.colorbar(sc, cax=cax)

        else:
            # or update existing one.
            self.colorbar.update_normal(sc)

        # some labels
        ax1.set_xlabel("X (mm)")
        ax1.set_ylabel("Y (mm)")

        # label with the pfsvisit Id
        tString = f'Convergence Distance: pfsVisitId = {visitId:d}, iteration = {nIter:d}'
        ax1.set_title(tString)

        ax1.set_aspect('equal')
        ax1.format_coord = self.cobraIdFiberIdFormatter

        convergeData = convergeData.query(f'iteration>={minIter}')
        maxIter = convergeData.iteration.max()

        cmap = plt.get_cmap('viridis')
        cmap = cmap(np.linspace(1.0, 0, len(convergeData.iteration.unique())))

        for i, (iterVal, iterData) in enumerate(convergeData.groupby('iteration')):
            iterData = self.addPfsConfigInfo(iterData, pfsConfigDf).reset_index()
            # show moving cobras.
            iterData = self.selectMovingCobras(iterData)

            dx = iterData.pfi_center_x_mm - iterData.pfi_target_x_mm
            dy = iterData.pfi_center_y_mm - iterData.pfi_target_y_mm
            dist = np.hypot(dx, dy)
            # converting to microns
            dist *= 1000

            n, bins, patches = ax2.hist(dist, alpha=0.6, histtype='step', linewidth=3,
                                        label=f'{iterVal}-th Iteration', bins=bins, range=(vmin, vmax),
                                        color=cmap[i])

        ax2.legend(loc='upper right')
        ax2.set_title(f"Distance to Target: pfsVisitId = {visitId:d}")
        ax2.set_xlabel("Distance (microns)")
        ax2.set_ylabel("N")
        ax2.set_aspect('auto')
        ax2.grid()

        # adding percentiles
        try:
            showPercentiles = list(map(int, showPercentiles.split(',')))
        except:
            showPercentiles = [75, 95]

        percentiles = np.percentile(dist, showPercentiles)
        ymin, ymax = ax2.get_ylim()

        for value, perc in zip(percentiles, showPercentiles):
            color = 'r' if perc == 95 and value > 10 else 'k'
            ax2.vlines(value, ymin, ymax, label=f'{perc}th : {value:.1f} microns', color=color, alpha=0.5)
            label = ax2.legend().get_texts()[-1]
            label.set_color(color)

        fig.tight_layout()

        return True

    def selectMovingCobras(self, iterData):
        """Filter cobras returning only moving cobras."""
        # show moving cobras.
        iterData = iterData.loc[self.goodIdx]
        # do not show UNASSIGNED and  MASKED cobras.
        MASK = (iterData.targetType != TargetType.UNASSIGNED) & (iterData.fiberStatus != FiberStatus.MASKED)
        return iterData[MASK]
