import numpy as np
import pandas as pd

from pfsPlotActor.utils.mtp import GangConnector
from pfs.utils.butler import Butler as Nestor
from pfs.utils.fiberids import FiberIds

nestor = Nestor()

dots = nestor.get('black_dots')
calibModel = nestor.get('moduleXml', moduleName='ALL', version='')

gfm = pd.DataFrame(FiberIds().data)
sgfm = gfm.set_index('scienceFiberId').loc[np.arange(2394) + 1].reset_index().sort_values('cobraId')

# adding mtp info.
sgfm = pd.merge(sgfm, GangConnector.translateMtpA()[['fiberId', 'mtp', 'gang', 'mtpHoleId']], on='fiberId', how='inner')

# getting up-to-date cobras calibration.
xCob = np.array(calibModel.centers.real).astype('float32')
yCob = np.array(calibModel.centers.imag).astype('float32')
armLength = np.array(calibModel.L1 + calibModel.L2).astype('float32')
L1 = np.array(calibModel.L1).astype('float32')
L2 = np.array(calibModel.L2).astype('float32')
FIBER_BROKEN_MASK = (calibModel.status & calibModel.FIBER_BROKEN_MASK).astype('bool')
COBRA_OK_MASK = (calibModel.status & calibModel.COBRA_OK_MASK).astype('bool')

sgfm['x'] = xCob
sgfm['y'] = yCob
sgfm['FIBER_BROKEN_MASK'] = FIBER_BROKEN_MASK
sgfm['COBRA_OK_MASK'] = COBRA_OK_MASK
sgfm['armLength'] = armLength
sgfm['L1'] = L1
sgfm['L2'] = L2
# adding blackSpots position and radius.
np.testing.assert_equal(sgfm.cobraId.to_numpy(), dots.spotId.to_numpy())
sgfm['xDot'] = dots.x.to_numpy()
sgfm['yDot'] = dots.y.to_numpy()
sgfm['rDot'] = dots.r.to_numpy()

# make absolutely sure it's sorted per cobraId
sgfm = sgfm[['scienceFiberId', 'cobraId', 'fiberId', 'spectrographId', 'mtp', 'gang', 'mtpHoleId', 'fiberHoleId',
             'FIBER_BROKEN_MASK', 'COBRA_OK_MASK', 'x', 'y', 'xDot', 'yDot', 'rDot', 'armLength', 'L1', 'L2']].sort_values('cobraId')

fiducials = nestor.get('fiducials')
fiducials['FIDUCIALS_OK'] = (fiducials.flag & (1 | 2)) == 0
fiducials.sort_values('fiducialId')

np.testing.assert_array_equal(fiducials.index, fiducials.fiducialId.to_numpy() - 1)
