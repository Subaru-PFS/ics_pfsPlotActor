import logging

import actorcore.ICC


class OurActor(actorcore.ICC.ICC):
    def __init__(self, name, productName=None, modelNames=None, configFile=None, logLevel=logging.INFO):
        # This sets up the connections to/from the hub, the logger, and the twisted reactor.
        #
        modelNames = [] if modelNames is None else modelNames
        actorcore.ICC.ICC.__init__(self, name,
                                   productName=productName,
                                   configFile=configFile,
                                   modelNames=modelNames)

        self.logger.setLevel(logLevel)

    def disconnectActor(self):
        self.shuttingDown = True

    def requireModels(self, actorList, cmd=None):
        """ Make sure that we are listening for a given actor keywords. """
        cmd = self.bcast if cmd is None else cmd
        actorList = [actorName for actorName in actorList if actorName not in self.models.keys()]

        if actorList:
            cmd.inform(f"text='connecting model for actors {','.join(actorList)}'")
            self.addModels(actorList)


def connectActor(modelNames):
    theActor = OurActor('pfsplot',
                        productName='pfsPlotActor',
                        modelNames=modelNames,
                        logLevel=logging.DEBUG)

    theActor.run(doReactor=False)
    return theActor
