import os
import sys

from .common import debug_print, walk
from . import base
from . import uv
from . import qt
from . import qta

(
    FLAVOUR_NONE,
    FLAVOUR_PYUV,
    FLAVOUR_PYSIDE2,
    FLAVOUR_QT5,
    FLAVOUR_PYSIDE2_QASYNC,
    FLAVOUR_QT5_QASYNC
) = range(6)

flavour = FLAVOUR_NONE

if os.environ.get('USE_PYUV') == '1':
    import pyuv
    flavour = FLAVOUR_PYUV
elif os.environ.get('USE_PYSIDE2') == '1':
    from PySide2 import QtCore
    flavour = FLAVOUR_PYSIDE2
elif os.environ.get('USE_PYQT5') == '1':
    from PyQt5 import QtCore
    flavour = FLAVOUR_QT5
else:
    try:
        import pyuv
        flavour = FLAVOUR_PYUV
    except ImportError:
        try:
            from PySide2 import QtCore
            flavour = FLAVOUR_PYSIDE2
        except ImportError:
            try:
                from PyQt5 import QtCore
                flavour = FLAVOUR_QT5
            except ImportError:
                raise Exception("eventloop needs one of: pyuv or PySide2 or PyQt5 packages to work, none found")

if flavour in [FLAVOUR_PYSIDE2, FLAVOUR_QT5]:
    if os.environ.get('USE_QASYNC') == '1':
        import qasync
        if flavour == FLAVOUR_PYSIDE2:
            flavour = FLAVOUR_PYSIDE2_QASYNC
        else:
            flavour = FLAVOUR_QT5_QASYNC
    elif os.environ.get('USE_QASYNC') == '0':
        pass
    else:
        try:
            import qasync
            if flavour == FLAVOUR_PYSIDE2:
                flavour = FLAVOUR_PYSIDE2_QASYNC
            else:
                flavour = FLAVOUR_QT5_QASYNC
        except ImportError:
            pass


def EventLoop(app = None):
    return {
        FLAVOUR_NONE: lambda app: print("eventloop needs one of: pyuv or PySide2 or PyQt5 packages to work, none found"),
        FLAVOUR_PYUV: lambda app: uv.EventLoop(),
        FLAVOUR_PYSIDE2: lambda app: qt.EventLoop(app),
        FLAVOUR_QT5: lambda app: qt.EventLoop(app),
        FLAVOUR_PYSIDE2_QASYNC: lambda app: qta.EventLoop(app),
        FLAVOUR_QT5_QASYNC: lambda app: qta.EventLoop(app),
    }[flavour](app)

def FileSystemWatch():
    if flavour == FLAVOUR_PYUV:
        return uv.FileSystemWatch()
    else:
        return qt.FileSystemWatch()

def SingleShotTimer():
    if flavour == FLAVOUR_PYUV:
        return uv.SingleShotTimer()
    else:
        return qt.SingleShotTimer()

def Timer():
    if flavour == FLAVOUR_PYUV:
        return uv.Timer()
    else:
        return qt.Timer()

class Schedule:

    def __init__(self, executor):
        self._executor = executor
        self._tasks = []
        self._timeout = 10
        self._timer = None
    
    def append(self, task, timeout):
        if isinstance(task, list):
            tasks = task
        else:
            tasks = [task]
        for task in tasks:
            if task not in self._tasks:
                self._tasks.append(task)
        self._schedule(timeout)

    def on_timeout(self):
        debug_print("Schedule.on_timeout")
        executor = self._executor
        tasks = []
        for task in self._tasks:
            debug_print("executing", task)
            res = executor.execute(task)
            if res == False:
                debug_print("failed to execute task", task)
                tasks.append(task)
        self._tasks = tasks
        if len(tasks) > 0:
            debug_print("rescheduling failed tasks")
            self._schedule(self._timeout)

    def _schedule(self, timeout):
        timer = self._timer
        if timer:
            timer.stop()
        timer = SingleShotTimer()
        timer.start(timeout, self.on_timeout)
        self._timer = timer

def on_file_changed(path, include=None, exclude=None, timeout=1, loop=None, recursive=True, terminate_after=None):

    def decorator(func):

        loop_ = loop
        if loop is None:
            loop_ = EventLoop()

        def on_change(file_path, event):
            debug_print("on_change", file_path)
            schedule.append(file_path, timeout)

        executor = base.FuncExecutor(func)
        
        watch = FileSystemWatch()
        schedule = Schedule(executor)
        watch.start(path, on_change, recursive=recursive, include=include, exclude=exclude)

        terminate_timer = None
        if terminate_after is not None:
            terminate_timer = SingleShotTimer()
            terminate_timer.start(terminate_after, loop_.stop)

        if loop is None:
            loop_.start()
        else:
            loop._handles.append(watch)
            loop._handles.append(schedule)
            loop._handles.append(executor)
            loop._handles.append(terminate_timer)

        return func
    
    return decorator
    
