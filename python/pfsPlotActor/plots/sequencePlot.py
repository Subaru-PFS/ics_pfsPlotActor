from importlib import reload

import matplotlib.pylab as plt
import numpy as np
import pfsPlotActor.utils.pfi as pfiUtils
from matplotlib.colors import to_hex

reload(pfiUtils)


class SequencePlot(pfiUtils.ConvergencePlot):

    def cobraIndices(self, cobraNum):
        indices = self.goodIdx if cobraNum is None else [cobraNum - 1]
        return indices

    def plot(self, convergeData, cobraNum='all', minIter=3, centrePos=True, hardStop=False, blackDots=True,
             badCobras=False, patrolRegion=True, ff=True, showDesign=True):
        """Plot the latest dataset."""
        fig = self.fig
        ax = self.axes[0]

        convergeData = convergeData.query(f'iteration>={minIter}')

        if not badCobras:
            convergeData = convergeData[convergeData.cobra_id.isin(self.goodIdx + 1)]

        [visitId] = convergeData.pfs_visit_id.unique()
        nIter = convergeData.iteration.max()
        cobraNum = None if cobraNum == 'all' else int(cobraNum)

        # sequential colourmap for plots
        cmap = plt.get_cmap('cool')
        cmap = cmap(np.linspace(1.0, 0, len(convergeData.iteration.unique())))
        colors = [to_hex(col) for col in cmap]

        # plot spots for each iteration in a given colour
        for i, (iterVal, cD) in enumerate(convergeData.groupby('iteration')):
            xM = cD['pfi_center_x_mm'].values
            yM = cD['pfi_center_y_mm'].values
            sc = ax.scatter(xM, yM, c=colors[i], marker='o', s=10)

        ax.set_aspect('equal')
        ax.set_xlabel("X (mm)")
        ax.set_ylabel("Y (mm)")

        tString = f'Cobra Motion: pfsVisitId = {visitId:d}'
        ax.set_title(tString)
        ax.format_coord = self.cobraIdFiberIdFormatter

        # various optional overlays
        if centrePos:
            self.overlayCentres(ax, cobraNum=cobraNum)
        if hardStop:
            self.overlayHardStop(ax, cobraNum=cobraNum)
        if blackDots:
            self.overlayBlackDots(ax, cobraNum=cobraNum)
        if patrolRegion:
            self.overlayPatrolRegion(ax, cobraNum=cobraNum)
        if ff:
            self.overlayFF(ax)
        if showDesign:
            self.overlayDesign(ax, visitId)

    def overlayFF(self, ax):
        """Overlay positions of fiducial fibres."""
        ax.scatter(self.fids['x_mm'], self.fids['y_mm'], marker="d")

    def overlayPatrolRegion(self, ax, cobraNum=None):
        """Overlay cobra patrol regions on given axis.
        if cobraNum == None do for all good cobras, else for cobraNum
        """
        ind = self.cobraIndices(cobraNum)
        armLength = self.calibModel.L1 + self.calibModel.L2

        for i in ind:
            circle = plt.Circle((self.calibModel.centers[i].real, self.calibModel.centers[i].imag), armLength[i],
                                fill=False, color='black')
            a = ax.add_artist(circle)

    def overlayCentres(self, ax, cobraNum=None):
        """Overlay centre positions of cobra patrol regions on given axis.
        if cobraNum == None do for all good cobras, else for cobraNum.
        """
        ind = self.cobraIndices(cobraNum)
        ax.scatter(self.calibModel.centers[ind].real, self.calibModel.centers[ind].imag, c='black', marker='o', s=25)

    def overlayHardStop(self, ax, cobraNum=None):
        """Overlay theta hard stops
        if cobraNum == None do for all good cobras, else for cobraNum
        """
        ind = self.cobraIndices(cobraNum)
        length = self.calibModel.L1 + self.calibModel.L1

        self._addLine(ax, self.calibModel.centers[ind], length[ind], self.calibModel.tht0[ind], color='orange',
                      linewidth=0.5, linestyle='--')

        self._addLine(ax, self.calibModel.centers[ind], length[ind], self.calibModel.tht1[ind], color='black',
                      linewidth=0.5, linestyle='-.')

    def overlayBlackDots(self, ax, cobraNum=None):
        """Overlay black dots.
        if cobraNum == None do for all good cobras, else for cobraNum
        """
        ind = self.cobraIndices(cobraNum)

        for i in ind:
            e = plt.Circle((self.dots['x'].values[i], self.dots['y'].values[i]), self.dots['r'].values[i],
                           color='grey', fill=True, alpha=0.5)
            ax.add_artist(e)

    def overlayDesign(self, ax, visitId):
        """Show cobra design positions."""

        try:
            pfsDesign = self.reloadDesign(visitId)
        except:
            pfsDesign = None

        if pfsDesign:
            ax.plot(pfsDesign.pfiNominal[:, 0], pfsDesign.pfiNominal[:, 1], 'x', color='k')

    def overlayBadCobras(self, ax):
        """Overlay centre positions of cobra patrol regions on given axis.
        if cobraNum == None do for all good cobras, else for cobraNum
        """
        ax.scatter(self.calibModel.centers[self.badIdx].real, self.calibModel.centers[self.badIdx].imag, c='black',
                   marker='*', s=25)

    def _addLine(self, ax, centers, length, angle, **kwargs):

        x = length * np.cos(angle)
        y = length * np.sin(angle)

        for i in range(len(centers)):
            ax.plot([centers.real[i], centers.real[i] + x[i]], [centers.imag[i], centers.imag[i] + y[i]], **kwargs)
