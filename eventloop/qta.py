import signal
from . import base

try:
    import PySide2
    from PySide2 import QtCore
except ImportError:
    try:
        import PyQt5
        from PyQt5 import QtCore
    except ImportError:
        pass

try:
    import asyncio
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

    def start(self):
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        self._loop.run_forever()
        
    def stop(self):
        if self._app:
            self._app.exit()
            self._app = None
            debug_print("EventLoop stoped")