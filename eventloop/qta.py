import signal
from . import base
from .common import debug_print
import os
from .common import flavour, FLAVOUR_NONE, FLAVOUR_PYUV, FLAVOUR_PYSIDE2, FLAVOUR_QT5, FLAVOUR_PYSIDE2_QASYNC, FLAVOUR_QT5_QASYNC

if flavour in [FLAVOUR_PYSIDE2, FLAVOUR_PYSIDE2_QASYNC]:
    from PySide2 import QtCore
elif flavour in [FLAVOUR_QT5, FLAVOUR_QT5_QASYNC]:
    from PyQt5 import QtCore
else:
    pass

try:
    import asyncio
except ImportError:
    pass

try:
    import qasync
except ImportError:
    pass

class EventLoop(base.EventLoop):

    def __init__(self, app = None):
        super().__init__()
        debug_print("qta.EventLoop")
        if app is None:
            app = QtCore.QCoreApplication.instance()
        if app is None:
            app = QtCore.QCoreApplication([])
        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)
        self._app = app
        self._loop = loop
        self._watchers = []

    def start(self):
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        self._loop.run_forever()

    def addWatcher(self, watcher):
        self._watchers.append(watcher)

    def _cleanWatchers(self):
        watcher: QtCore.QFileSystemWatcher
        for watcher in self._watchers:
            paths = watcher.files() + watcher.directories()
            if len(paths):
                watcher.removePaths(paths)
        self._watchers = []

    def stop(self):
        self._cleanWatchers()
        if self._app:
            self._app = None
            
        if self._loop:
            self._loop.stop()
            self._loop = None
        debug_print("EventLoop stoped")