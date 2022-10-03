from . import base
import signal
from .common import debug_print, walk, EVENT_CHANGE, debug_print, path_matches
import glob
import os

if os.environ.get('USE_PYSIDE2') == '1':
    import PySide2
    from PySide2 import QtCore
    debug_print("using PySide2")
elif os.environ.get('USE_PYQT5') == '1':
    import PyQt5
    from PyQt5 import QtCore
    debug_print("using PyQt5")
else:
    try:
        import PySide2
        from PySide2 import QtCore
    except ImportError:
        try:
            import PyQt5
            from PyQt5 import QtCore
        except ImportError:
            pass

class EventLoop(base.EventLoop):

    def __init__(self, app = None):
        super().__init__()
        if app is None:
            instance = QtCore.QCoreApplication.instance()
            if instance is not None:
                app = instance
            else:
                app = QtCore.QCoreApplication([])
        self._app = app

    def start(self):
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        self._app.exec_()
        debug_print("EventLoop started")
        
    def stop(self):
        if self._app:
            self._app.exit()
            self._app = None
            debug_print("EventLoop stoped")

class Timer(base.Timer):

    def start(self, interval, callback, once = False):
        super().start(interval, callback, once)
        timer = QtCore.QTimer()
        timer.timeout.connect(self.on_timeout)
        timer.setSingleShot(once)
        timer.start(int(interval * 1000))
        self._timer = timer

    def stop(self):
        timer = self._timer
        self._timer = None
        if timer:
            timer.stop()

    def on_timeout(self):
        self._callback()

class SingleShotTimer(Timer):
    def start(self, timeout, callback):
        super().start(timeout, callback, True)

class FileSystemWatch(base.FileSystemWatch):

    def start(self, path, callback, include = None, exclude = None, recursive = False):
        super().start(path, callback, include, exclude, recursive)
        watcher = QtCore.QFileSystemWatcher()
        self._watch = watcher

        if not recursive:
            if glob.has_magic(path):
                raise Exception('Not implemented')
            paths_to_add = [path]
            for root, dirs_, files in os.walk(path):
                for f in files:
                    p = os.path.join(root, f)
                    if path_matches(p, include, exclude):
                        paths_to_add.append(p)
            self._addPaths(paths_to_add)
        else:
            dirs, files = walk(path, include, exclude, all_dirs=True, recursive=recursive)
            self._addPaths(dirs + files)
        
        watcher.fileChanged.connect(self.on_file_changed)
        watcher.directoryChanged.connect(self.on_directory_changed)
        
    def on_directory_changed(self, path):
        include = self._include
        exclude = self._exclude
        watcher = self._watch

        # todo do glob instead of walk if _orig_path has magic
        dirs, files = walk(path, include, exclude, all_dirs=True, recursive=self._recursive)

        watched = watcher.files()
        if self._recursive:
            self._addPaths(dirs + files)
        else:
            self._addPaths(files)
            
        for path in files:
            if path not in watched:
                self._callback(path, EVENT_CHANGE)

    def _addPaths(self, paths):
        watcher = self._watch
        watcher.addPaths(paths)
        #debug_print('watcher.addPaths', paths)

    def on_file_changed(self, path):
        if not path_matches(path, self._include, self._exclude):
            return
        self._callback(path, EVENT_CHANGE)

    def stop(self):
        pass