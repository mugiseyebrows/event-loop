import os
import signal
import glob
import sys

def debug_print_on(*args):
    print(*args)

def debug_print_off(*args):
    pass

if 'DEBUG_EVENTLOOP' in os.environ and os.environ['DEBUG_EVENTLOOP'] == "1":
    debug_print = debug_print_on
else:
    debug_print = debug_print_off

try:
    import pyuv
    debug_print("using pyuv")
except ImportError:
    try:
        import PySide2
        from PySide2 import QtCore
        debug_print("using PySide2")
    except ImportError:
        try:
            import PyQt5
            from PyQt5 import QtCore
            debug_print("using PyQt5")
        except ImportError:
            raise Exception("eventloop needs one of: pyuv or PySide2 or PyQt5 packages to work, none found")

has_pyuv = 'pyuv' in globals()
has_PySide2 = 'PySide2' in globals()
has_PyQt5 = 'PyQt5' in globals()

""" template
if has_pyuv:
    pass
elif has_PySide2 or has_PyQt5:
    pass
"""

class EventLoop:
    def __init__(self, app = None):
        if has_pyuv:
            pass
        elif has_PySide2 or has_PyQt5:
            if app is None:
                app = QtCore.QCoreApplication([])
        self._app = app

    def start(self):
        if has_pyuv:
            loop = pyuv.Loop.default_loop()
            handle = pyuv.Signal(loop)
            handle.start(lambda handle, signum: handle.close(), signal.SIGINT)
            loop.run()
        elif has_PySide2 or has_PyQt5:
            signal.signal(signal.SIGINT, signal.SIG_DFL)
            self._app.exec_()

    def stop(self):
        if has_pyuv:
            loop = pyuv.Loop.default_loop()
            loop.stop()
        elif has_PySide2 or has_PyQt5:
            QtCore.QCoreApplication.quit()
        
def path_matches(path, include, exclude):
    name = os.path.basename(path)
    if include is not None and len(include) > 0:
        ok = False
        for pat in include:
            if glob.fnmatch.fnmatch(name, pat) or glob.fnmatch.fnmatch(path, pat):
                ok = True
                break
        if not ok:
            return False
    if exclude is not None:
        for pat in exclude:
            if glob.fnmatch.fnmatch(name, pat) or glob.fnmatch.fnmatch(path, pat):
                return False
    return True

def walk(path, include, exclude):
    """
    Examples:
        return only cpp files that don't start with moc_:
            include = ["*.cpp"] exclude = ["moc_*"]
        return all files and directories but .git and node_modules:
            include = [] exclude = [".git", "node_modules"]
        return all files and directories:
            include = [] exclude = []
    Initial path is not checked and always returned.
    """
    queue = []
    dirs = []
    files = []
    if os.path.isfile(path):
        files.append(path)
    else:
        dirs.append(path)
        queue.append(path)

    while len(queue) > 0:
        path = queue.pop(0)
        for n in os.listdir(path):
            path_ = os.path.join(path, n)
            if path_matches(path_, include, exclude):
                if os.path.isfile(path_):
                    files.append(path_)
                else:
                    dirs.append(path_)
                    queue.append(path_)
    return dirs, files

class FileSystemWatch:

    (
        EVENT_RENAME,
        EVENT_CHANGE
    ) = range(2)

    def start(self, path, callback, include = None, exclude = None, recursive = False):
        self._callback = callback
        self._path = path
        if include is None:
            include = []
        if exclude is None:
            exclude = []
        self._include = include
        self._exclude = exclude
        if has_pyuv:
            if sys.platform not in ['win32','darwin'] and recursive:
                print("Warning: recursive not implemented for this platform")
                # TODO: workaround for recursive
            loop = pyuv.Loop.default_loop()
            handle = pyuv.fs.FSEvent(loop)
            UV_FS_EVENT_RECURSIVE = 4
            handle.start(path, UV_FS_EVENT_RECURSIVE if recursive else 0, self.onPyuvChanged)
            handle.ref = False
            self._watch = handle
        elif has_PySide2 or has_PyQt5:
            watcher = QtCore.QFileSystemWatcher()
            dirs, files = walk(path, include, exclude)
            watcher.addPaths(dirs + files)
            watcher.fileChanged.connect(self.onQtFileChanged)
            watcher.directoryChanged.connect(self.onQtDirectoryChanged)
            self._watch = watcher

    def onQtDirectoryChanged(self, path):
        #print("onQtDirectoryChanged")
        include = self._include
        exclude = self._exclude
        watcher = self._watch
        dirs, files = walk(path, include, exclude)
        watched = watcher.files()
        watcher.addPaths(dirs + files)
        for path in files:
            if path not in watched:
                self._callback(path, self.EVENT_CHANGE)

    def onQtFileChanged(self, path):
        #print("onQtFileChanged")
        self._callback(path, self.EVENT_CHANGE)

    def onPyuvChanged(self, handle, filename, events, error):
        events_ = []

        if os.path.isfile(self._path):
            path = self._path
        else:
            path = os.path.join(self._path, filename)
        
        if not path_matches(path, self._include, self._exclude):
            return

        if events & pyuv.fs.UV_RENAME:
            events_.append(self.EVENT_RENAME)
            
        if events & pyuv.fs.UV_CHANGE:
            events_.append(self.EVENT_CHANGE)

        for event in events_:
            self._callback(path, event)
            

    def stop(self):
        if has_pyuv:
            pass
        elif has_PySide2 or has_PyQt5:
            pass

class Timer:
    def __init__(self):
        pass

    def start(self, interval, callback, once = False):
        self._callback = callback
        self._once = once
        if has_pyuv:
            loop = pyuv.Loop.default_loop()
            timer = pyuv.Timer(loop)
            timer.start(self.onPyUvTimer, interval, 0 if once else interval)
            timer.ref = False
            self._timer = timer
        elif has_PySide2 or has_PyQt5:
            timer = QtCore.QTimer()
            timer.timeout.connect(self.onPySide2Timer)
            timer.start(int(interval * 1000))
            timer.setSingleShot(once)
            self._timer = timer

    def onPyUvTimer(self, timer):
        self._callback()
        """
        if self._once:
            self._timer = None
            timer.stop()
            timer.close()
        """

    def onPySide2Timer(self):
        self._callback()
        
    def stop(self):
        if has_pyuv:
            timer = self._timer
            self._timer = None
            if timer:
                timer.stop()
                timer.close()
        elif has_PySide2 or has_PyQt5:
            timer = self._timer
            self._timer = None
            if timer:
                timer.stop()

class SingleShotTimer(Timer):

    def start(self, timeout, callback):
        super().start(timeout, callback, True)