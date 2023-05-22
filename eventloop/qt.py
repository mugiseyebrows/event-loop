from . import base
import signal
from .common import debug_print, walk, EVENT_CHANGE, debug_print, path_matches
import glob
import os
from .common import flavour, FLAVOUR_NONE, FLAVOUR_PYUV, FLAVOUR_PYSIDE2, FLAVOUR_QT5, FLAVOUR_PYSIDE2_QASYNC, FLAVOUR_QT5_QASYNC
import sys

if flavour in [FLAVOUR_PYSIDE2, FLAVOUR_PYSIDE2_QASYNC]:
    from PySide2 import QtCore
elif flavour in [FLAVOUR_QT5, FLAVOUR_QT5_QASYNC]:
    from PyQt5 import QtCore

class EventLoop(base.EventLoop):

    def __init__(self, app = None):
        super().__init__()
        self._watchers = []
        debug_print("qt.EventLoop")
        if app is None:
            app = QtCore.QCoreApplication.instance()
        if app is None:
            app = QtCore.QCoreApplication([])
        self._app = app

    def start(self):
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        self._app.exec_()
        debug_print("EventLoop started")

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

    def __init__(self, loop):
        super().__init__()
        self._loop = loop

    def start(self, path, callback, include = None, exclude = None, recursive = False):
        super().start(path, callback, include, exclude, recursive)
        watcher = QtCore.QFileSystemWatcher()
        self._watch = watcher
        self._loop.addWatcher(watcher)

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

class Server(QtCore.QObject):
    def __init__(self, parent = None):
        super().__init__(parent)
        self._process = None
        self._terminated = None
        
    def restart(self, cmd, cwd = None):
        process = self._process
        if process is not None:
            if process.state() == QtCore.QProcess.ProcessState.Running:
                debug_print("terminating", process)
                process.kill()
                self._terminated = process
            self._process = None

        debug_print("Server.start cmd", cmd)

        process = QtCore.QProcess()
        process.setProgram(cmd[0])
        process.setArguments(cmd[1:])
        if cwd is not None:
            process.setWorkingDirectory(cwd)
        
        process.readyReadStandardOutput.connect(self.onStdOut)
        process.readyReadStandardError.connect(self.onStdErr)
        process.started.connect(self.onStarted)
        
        process.error.connect(self.onError)

        process.finished.connect(self.onFinished)

        process.start(QtCore.QIODevice.OpenModeFlag.ReadOnly)

        #debug_print("readChannelCount", process.readChannelCount())

        self._process = process

        debug_print("state", process.state())

        #QtCore.QTimer.singleShot(1000, lambda: debug_print("state", process.state()))
        #QtCore.QTimer.singleShot(1000, self.onStdErr)
        #QtCore.QTimer.singleShot(1000, self.onStdOut)
    
    def onError(self, code):
        debug_print("error", code)

    def onStarted(self):
        process = self._process
        debug_print(process, "started")

    def onFinished(self):
        debug_print("onFinished")

    def onStdOut(self):
        debug_print("onStdOut")
        process = self._process
        if process is None:
            return
        data = process.readAllStandardOutput()
        sys.stdout.buffer.write(data.data())
        sys.stdout.buffer.flush()
        
    def onStdErr(self):
        debug_print("onStdErr")
        process = self._process
        if process is None:
            return
        data = process.readAllStandardError()
        sys.stderr.buffer.write(data.data())
        sys.stderr.buffer.flush()