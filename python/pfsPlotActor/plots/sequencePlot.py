import numpy as np
import pfsPlotActor.livePlot as livePlot
from ics.cobraCharmer import func
from opdb import opdb
from pfs.utils.butler import Butler
import matplotlib.pylab as plt


def getCobraStatusIndex(calibModel):
    """Retrieve good/bad cobra index."""
    # get goodIdx
    allCobras = [func.Cobra(calibModel.moduleIds[i], calibModel.positionerIds[i]) for i in calibModel.findAllCobras()]
    nCobras = len(allCobras)

    goodNums = [i + 1 for i, c in enumerate(allCobras) if calibModel.cobraIsGood(c.cobraNum, c.module)]
    badNums = [e for e in range(1, nCobras + 1) if e not in goodNums]

    goodIdx = np.array(goodNums, dtype='i4') - 1
    badIdx = np.array(badNums, dtype='i4') - 1

    return goodIdx, badIdx


class sequencePlot(livePlot.LivePlot):
    key = 'convergenceId'
    # needs to be overridden by the user.
    actor = 'tests'

    # load pfi design file
    db = opdb.OpDB(hostname="db-ics", username="pfs", dbname="opdb")
    butler = Butler()

    dots = butler.get('black_dots')
    fids = butler.get('fiducials')
    calibModel = butler.get('moduleXml', moduleName='ALL', version='')

    goodIdx, badIdx = getCobraStatusIndex(calibModel)

    def initialize(self):
        """Initialize your axes and colorbar"""
        ax = self.fig.add_subplot(111)
        return ax

    def identify(self, keyvar):
        """load the convergence data"""
        visit = keyvar.getValue()
        return self.loadConvergence(visit)

    def loadConvergence(self, visitId):
        """
        load data to plot the results of a convergence run.
        This does a join on cobra_target and cobra_match to get both target and actual positions.
        This loads the results at a given iteration
        """
        visitId = int(visitId)

        sql = f'select cm.pfs_visit_id, cm.iteration, cm.cobra_id, cm.pfi_center_x_mm, cm.pfi_center_y_mm, ' \
              f'ct.pfi_target_x_mm, ct.pfi_target_y_mm, md.mcs_center_x_pix, md.mcs_center_y_pix, ' \
              f'md.mcs_second_moment_x_pix,md.mcs_second_moment_y_pix, md.peakvalue  from cobra_match ' \
              f'cm inner join cobra_target ct on ct.pfs_visit_id = cm.pfs_visit_id and ct.iteration = ' \
              f'cm.iteration and ct.cobra_id = cm.cobra_id inner join mcs_data md ' \
              f'on md.mcs_frame_id = cm.pfs_visit_id * 100 + cm.iteration and md.spot_id = cm.spot_id where cm.pfs_visit_id = {visitId} order by ct.cobra_id, ct.iteration'

        # get data
        convergeData = self.db.fetch_query(sql)

        # save the maximum iteration, as this is used a lot
        try:
            nIter = convergeData['iteration'].values.max()
        except:
            nIter = 0

        return dict(visitId=visitId, convergeData=convergeData, iterVal=nIter)

    def plot(self, visitId, convergeData, nIter, centrePos = True, hardStop = False, blackDots = False, patrolRegion = True, ff = True):
        """Plot the latest dataset."""
        fig = self.fig
        ax = self.axes[0]


        # sequential colourmap for plots
        cmap = plt.get_cmap('rainbow')
        cols = cmap(np.linspace(0, 1, self.nIter+1))
        colSeq = [] 

        # turn into hex values for plots
        for i in range(self.nIter):
            colSeq.append(to_hex(cols[i]))
        
        # plot spots for each iteration in a given colour
        for iterVal in range(nIter):
            filterInd = convergeData['iteration'] == iterVal
            cD = convergeData[filterInd]

            xM = cD['pfi_center_x_mm'].values
            yM = cD['pfi_center_y_mm'].values

            sc = ax.scatter(xM, yM, c=colSeq[iterVal], marker = 'o', s=10, **kwargs)
        ax.set_aspect('equal')
        ax.set_xlabel("X (mm)")
        ax.set_ylabel("Y (mm)")

        tString = f'pfsVisitId = {visitId:d}'
        ax.set_title(tString)
                
        # various optional overlays

        # centre of patrol region (home position)
        if(centrePos == True):
            ax.scatter(self.calibModel.centers[ind].real, self.calibModel.centers[ind].imag, c='black', marker = 'o', s=25)

        # theta hardstops
        if(hardStop == True):
            length=self.calibModel.L1+self.calibModel.L1 
            self._addLine(ax,self.calibModel.centers[ind],length[ind],self.calibModel.tht0[ind],color='orange',
                          linewidth=0.5,linestyle='--')

            self._addLine(ax,self.calibModel.centers[ind],length[ind],self.calibModel.tht1[ind],color='black',
                          linewidth=0.5,linestyle='-.')

        # black dots
        if(blackDots == True):
            for i in self.goodIdx:
                e = plt.Circle((self.dots['x'].values[i], self.dots['y'].values[i]), self.dots['r'].values[i], 
                        color='grey', fill=True, alpha=0.5)
                ax.add_artist(e)

        # circle for patrol region
        if(patrolRegion == True):
            armLength = self.calibModel.L1 + self.calibModel.L2
            for i in goodIdx:
                circle=plt.Circle((self.calibModel.centers[i].real, self.calibModel.centers[i].imag),armLength[i],fill=False,color='black')
                a=ax.add_artist(circle)

        # fiducial fibres
        if(ff == True):
            ax.scatter(self.fids['x_mm'],self.fids['y_mm'],marker="d")

        # add title
        tString = f'pfsVisitId = {self.visitId:d}'
        ax.set_title(tString)


    def _addLine(self, ax, centers, length, angle, cobraNum= None, **kwargs):
                
        x = length*np.cos(angle)
        y = length*np.sin(angle)
        
        for i in range(len(centers)):
                       
            ax.plot([centers.real[i],  centers.real[i]+x[i]],
                        [centers.imag[i],centers.imag[i]+y[i]],**kwargs)
