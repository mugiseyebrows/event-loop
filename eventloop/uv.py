
from . import base
from .common import debug_print, path_matches, EVENT_RENAME, EVENT_CHANGE
import signal
import sys
import os
import glob

try:
    import pyuv
except ImportError:
    pass

class EventLoop(base.EventLoop):

    def start(self):
        loop = pyuv.Loop.default_loop()
        handle = pyuv.Signal(loop)
        handle.start(lambda handle, signum: handle.close(), signal.SIGINT)
        loop.run()

    def stop(self):
        loop = pyuv.Loop.default_loop()
        loop.stop()

class Timer(base.Timer):
    def start(self, interval, callback, once = False):
        super().start(interval, callback, once)
        loop = pyuv.Loop.default_loop()
        timer = pyuv.Timer(loop)
        timer.start(self.on_timeout, interval, 0 if once else interval)
        timer.ref = False
        self._timer = timer

    def on_timeout(self, timer):
        self._callback()
        """
        if self._once:
            self._timer = None
            timer.stop()
            timer.close()
        """

    def stop(self):
        timer = self._timer
        self._timer = None
        if timer:
            timer.stop()
            timer.close()

class SingleShotTimer(Timer):
    def start(self, timeout, callback):
        super().start(timeout, callback, True)

class FileSystemWatch(base.FileSystemWatch):

    def start(self, path, callback, include = None, exclude = None, recursive = False):
        super().start(path, callback, include, exclude, recursive)
        if sys.platform not in ['win32','darwin'] and recursive:
            print("Warning: recursive not implemented for this platform")
            # TODO: workaround for recursive
        loop = pyuv.Loop.default_loop()

        if glob.has_magic(path):
            paths = glob.glob(path)
        else:
            paths = [path]

        handles = []

        UV_FS_EVENT_RECURSIVE = 4
        flags = UV_FS_EVENT_RECURSIVE if recursive else 0

        for path in paths:
            handle = pyuv.fs.FSEvent(loop)
            handle.start(path, flags, self.onChanged)
            handle.ref = False
            handles.append(handle)

        self._handles = handles
    def stop(self):
        pass

    def onChanged(self, handle, filename, events, error):
        events_ = []

        if os.path.isdir(handle.path):
            path = os.path.join(handle.path, filename)
            if not path_matches(path, self._include, self._exclude):
                return
        else:
            path = handle.path

        if events & pyuv.fs.UV_RENAME:
            events_.append(EVENT_RENAME)
            
        if events & pyuv.fs.UV_CHANGE:
            events_.append(EVENT_CHANGE)

        for event in events_:
            self._callback(path, event)
    