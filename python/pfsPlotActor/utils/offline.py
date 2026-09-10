"""Recording and replay of the opdb queries a plot issues.

Lets a plot be drawn without a database: a recording taken once from a real visit answers
every query that plot repeats on each redraw. Queries are keyed by their SQL text, so a
recording covers one visit whatever the tweaks are set to, the tweaks not reaching the SQL.
"""

import argparse
import importlib
import io
import json
import re
import zipfile
from contextlib import contextmanager

import pandas as pd
import pfsPlotActor.utils.pfi as pfiUtils

MANIFEST = 'manifest.json'


def queryKey(sql):
    """The lookup key for a query: its text with runs of whitespace collapsed."""
    return re.sub(r'\s+', ' ', sql).strip()


class RecordedOpDB:
    """Answers query_dataframe from a recording, standing in for pfs_utils' OpDB.

    An unrecorded query raises, rather than returning an empty frame that would reach the
    caller as a blank plot. Answers are copies, callers adding columns to what they get.
    ``visitId`` is the visit the recording was taken from, the only one it can answer for.
    """

    def __init__(self, results, visitId=None):
        self.results = results
        self.visitId = visitId

    def query_dataframe(self, sql):
        key = queryKey(sql)
        if key not in self.results:
            raise KeyError(f'nothing recorded for this query, only for another visit: {key}')
        return self.results[key].copy()


class RecordingOpDB:
    """Passes queries through to ``opdb`` and keeps the answers."""

    def __init__(self, opdb):
        self.opdb = opdb
        self.results = {}

    def query_dataframe(self, sql):
        self.results[queryKey(sql)] = df = self.opdb.query_dataframe(sql)
        return df


@contextmanager
def recording(plotClass=None):
    """Keep every query issued through ``plotClass.opdb``, yielding the recorder.

    opdb is a class attribute, so recording the base class covers all of its plots. That
    base defaults to the one the plot modules are bound to now, which importing them
    replaces: each reloads pfi, rebinding ConvergencePlot to a fresh class object.
    """
    plotClass = pfiUtils.ConvergencePlot if plotClass is None else plotClass
    recorder = RecordingOpDB(plotClass.opdb)
    plotClass.opdb = recorder
    try:
        yield recorder
    finally:
        plotClass.opdb = recorder.opdb


def save(results, path, visitId):
    """Write ``results`` to ``path`` as one parquet per query, indexed by a manifest."""
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as archive:
        queries = []
        for index, (sql, frame) in enumerate(sorted(results.items())):
            name = f'{index:03d}.parquet'
            buffer = io.BytesIO()
            frame.to_parquet(buffer)
            archive.writestr(name, buffer.getvalue())
            queries.append(dict(sql=sql, file=name, rows=len(frame)))
        archive.writestr(MANIFEST, json.dumps(dict(visitId=visitId, queries=queries), indent=2))


def load(path):
    """Read a recording back, as an opdb the plots can be pointed at."""
    results = {}
    with zipfile.ZipFile(path) as archive:
        manifest = json.loads(archive.read(MANIFEST))
        for entry in manifest['queries']:
            results[entry['sql']] = pd.read_parquet(io.BytesIO(archive.read(entry['file'])))
    return RecordedOpDB(results, visitId=manifest['visitId'])


def showRecording(tabWidget, path, modulePath='pfsPlotActor.plots.convergenceAndFiducials',
                  className='ConvergenceAndFiducials'):
    """Open a tab on ``tabWidget`` drawing the recording at ``path``, and return its plots.

    The plots read the recording rather than opdb, and take their visit from it rather than
    from a keyword, nothing publishing one with no actor behind them. Both substitutions are
    made on the classes, so they hold for every plot of that kind this process goes on to
    make.
    """
    recorded = load(path)
    pfiUtils.ConvergencePlot.opdb = recorded

    def identify(self, keyvar, newValue):
        """The visit to draw, which offline is the only one there is."""
        return dict(dataId=recorded.visitId, newValue=newValue)

    plotClass = getattr(importlib.import_module(modulePath), className)
    plotClass.addCallback = False
    plotClass.identify = identify

    plots = tabWidget.loadLayout([dict(name=f'visit {recorded.visitId}',
                                       plots=[dict(modulePath=modulePath, className=className,
                                                   actor=plotClass.actor, key=plotClass.key,
                                                   row=0, col=0)])])
    for plot in plots:
        plot.update()

    return plots


def drawOffScreen(plotClass, visitId):
    """Draw ``plotClass`` for ``visitId`` on an Agg canvas, returning the plot."""
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    plot = plotClass(None, FigureCanvasAgg(Figure(figsize=(18.5, 8.0))))
    plot.plot(visitId)
    return plot


def record(visitId, plotClass):
    """The queries ``plotClass`` issues to draw ``visitId``, drawn once against the database."""
    with recording() as recorder:
        drawOffScreen(plotClass, visitId)
    return recorder.results


def main(argv=None):
    """Record one visit for one plot, so it can be redrawn without a database."""
    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument('visitId', type=int, help='visit to record')
    parser.add_argument('output', help='path of the recording to write')
    parser.add_argument('--plot', default='convergenceAndFiducials.ConvergenceAndFiducials',
                        help='module.ClassName under pfsPlotActor.plots')
    args = parser.parse_args(argv)

    moduleName, className = args.plot.rsplit('.', 1)
    module = importlib.import_module(f'pfsPlotActor.plots.{moduleName}')

    results = record(args.visitId, getattr(module, className))
    save(results, args.output, args.visitId)
    print(f'recorded {len(results)} queries from visit {args.visitId} to {args.output}')


if __name__ == '__main__':
    main()
