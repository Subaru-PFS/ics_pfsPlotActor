
import pfsPlotActor.livePlot as livePlot
from ics.cobraCharmer import pfiDesign
from ics.cobraCharmer import func
import numpy as np
from pfs.utils.butler import Butler
from opdb import opdb
import matplotlib.pylab as plt
import pandas as pd
import os

class ConvergenceMap(livePlot.LivePlot):
    
    key = 'convergenceId'
    # needs to be overridden by the user.
    actor = 'fps'

    # load pfi design file
    db = opdb.OpDB(hostname="localhost",username="karr",dbname="opdb")

    def __init__(self,xmlFile,dotFile):

        """calibration data only needs to be loaded once"""

        self.calibModel = pfiDesign.PFIDesign(xmlFile)
        self.dots = pd.read_csv(dotFile)

        butler = Butler(configRoot=os.path.join(os.environ["PFS_INSTDATA_DIR"], "data"))
        self.fids = butler.get('fiducials')
        
        #define goodIdx
        cobras = []

        #get goodIdx 
        for i in self.calibModel.findAllCobras():
            c = func.Cobra(self.calibModel.moduleIds[i],
                           self.calibModel.positionerIds[i])
            cobras.append(c)
        allCobras = np.array(cobras)
        nCobras = len(allCobras)
        
        goodNums = [i+1 for i,c in enumerate(allCobras) if
                self.calibModel.cobraIsGood(c.cobraNum, c.module)]
        badNums = [e for e in range(1, nCobras+1) if e not in goodNums]

        self.goodIdx = np.array(goodNums, dtype='i4') - 1
        self.badIdx = np.array(badNums, dtype='i4') - 1

        
    def initialize(self):
        """Initialize my an axis to plot the map"""

        self.ax = self.fig.add_subplot(111)
        return self.ax

    def identify(self, keyvar):

        """load the convergence data"""
        
        [visit] = keyvar.getValue()
        return self.loadConvergence(visit)

    def loadConvergence(self, visitId):

        """
        load data to plot the results of a convergence run.
        This does a join on cobra_target and cobra_match to get both target and actual positions.
        This loads the results at a given iteration
        """
        visitId = int(visitId)

        sql = f'select cm.pfs_visit_id, cm.iteration, cm.cobra_id, cm.pfi_center_x_mm, cm.pfi_center_y_mm, ct.pfi_target_x_mm, ct.pfi_target_y_mm, md.mcs_center_x_pix, md.mcs_center_y_pix, md.mcs_second_moment_x_pix,md.mcs_second_moment_y_pix, md.peakvalue  from cobra_match cm inner join cobra_target ct on ct.pfs_visit_id = cm.pfs_visit_id and ct.iteration = cm.iteration and ct.cobra_id = cm.cobra_id inner join mcs_data md on md.mcs_frame_id = cm.pfs_visit_id * 100 + cm.iteration and md.spot_id = cm.spot_id where cm.pfs_visit_id = {visitId} order by ct.cobra_id, ct.iteration'

        # get data
        convergeData = self.db.fetch_query(sql)

        # save the maximum iteration, as this is used a lot
        try:
            nIter = convergeData['iteration'].values.max()
        except:
            nIter = 0

        return dict(visitId=visitId, convergeData=convergeData, nIter=nIter)

    def plot(self, visitId, convergeData, iterVal):
        
        """Plot the latest dataset."""
        
        fig = self.fig
        ax = self.ax

        # calculate distance from targets at this iteration

        dist = np.sqrt((convergeData['pfi_center_x_mm'].values - convergeData['pfi_target_x_mm'].values) ** 2 +
                       (convergeData['pfi_center_y_mm'].values - convergeData['pfi_target_y_mm'].values) ** 2)

        # do a scatter plot
        sc = ax.scatter(self.calibModel.centers.real[convergeData['cobra_id'].values - 1],
                        self.calibModel.centers.imag[convergeData['cobra_id'].values - 1],
                        c=dist, marker='o', s=20)

        fig.colorbar(sc)

        # some labels
        ax.set_xlabel("X (mm)")
        ax.set_ylabel("Y (mm)")

        # label with the pfsvisit Id
        tString = f'pfsVisitId = {visitId:d}, iteration = {iterVal:d}'
        ax.set_title(tString)

        ax.set_aspect('equal')
