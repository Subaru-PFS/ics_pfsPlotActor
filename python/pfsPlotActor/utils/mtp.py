import numpy as np
import pandas as pd
from pfs.utils.fiberids import FiberIds

gfm = FiberIds()
gfmDf = pd.DataFrame(gfm.data)

scienceFiberId = np.arange(2394) + 1
scienceFiber = gfmDf.set_index('scienceFiberId').loc[scienceFiberId].reset_index()


class MTP(object):
    holePerRow = 8
    nHoles = 32
    spacing = 0.3

    @staticmethod
    def getHolePosition(xOrigin, yOrigin):
        x = np.array([i % MTP.holePerRow * MTP.spacing for i in range(32)]) + xOrigin
        y = np.array([i // MTP.holePerRow * MTP.spacing for i in range(32)]) * -1 + yOrigin
        return pd.DataFrame(dict(x=x, y=y))


class GangConnector(object):
    xDistMTP = 11.273
    yDistMTP = 6.85
    nMtpPerCol = 2

    @staticmethod
    def getHolePosition(df):
        dfs = []
        iMtp = 0
        for mtpName, perMtp in df.groupby('mtp', sort=False):
            mtpProperties = perMtp.copy()

            xOrigin = iMtp % GangConnector.nMtpPerCol * GangConnector.xDistMTP
            yOrigin = iMtp // GangConnector.nMtpPerCol * GangConnector.yDistMTP * -1
            mtpCoord = MTP.getHolePosition(xOrigin, yOrigin)

            mtpProperties['xGang'] = mtpCoord.loc[perMtp.mtpHoleId - 1].x.to_numpy()
            mtpProperties['yGang'] = mtpCoord.loc[perMtp.mtpHoleId - 1].y.to_numpy()
            dfs.append(mtpProperties)

            iMtp += 1

        return pd.concat(dfs)

    @staticmethod
    def translateMtpA():
        res = []

        for j, row in scienceFiber.iterrows():
            n, i, specId, mtpHole, mtpScience = row.mtp_A.split('-')
            res.append((row.fiberId, specId, f'{n}-{i}', n[0], int(mtpHole)))

        return pd.DataFrame(res, columns=['fiberId', 'specId', 'mtp', 'gang', 'mtpHoleId'])

    @staticmethod
    def allPositions():
        translateMtpA = GangConnector.translateMtpA()

        dfs = []

        for (specId, gang), df in translateMtpA.groupby(['specId', 'gang']):
            holePosition = GangConnector.getHolePosition(df)
            holePosition['gang'] = gang
            dfs.append(holePosition)

        return pd.concat(dfs).sort_values('fiberId')
