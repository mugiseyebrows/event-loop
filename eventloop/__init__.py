import os
import signal
import glob
import sys

from .common import debug_print, walk
from . import base
from . import uv
from . import qt
from . import qta

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

try:
    import qasync
except ImportError:
    pass

has_pyuv = 'pyuv' in globals()
has_PySide2 = 'PySide2' in globals()
has_PyQt5 = 'PyQt5' in globals()
has_qasync = 'qasync' in globals()

""" template
if has_pyuv:
    pass
elif has_PySide2 or has_PyQt5:
    pass
"""

def EventLoop(app = None):
    if has_pyuv:
        return uv.EventLoop()
    elif has_PySide2 or has_PyQt5:
        if has_qasync:
            return qta.EventLoop(app)
        else:    
            return qt.EventLoop(app)

def FileSystemWatch():
    if has_pyuv:
        return uv.FileSystemWatch()
    elif has_PySide2 or has_PyQt5:
        return qt.FileSystemWatch()

def SingleShotTimer():
    if has_pyuv:
        return uv.SingleShotTimer()
    elif has_PySide2 or has_PyQt5:
        return qt.SingleShotTimer()

def Timer():
    if has_pyuv:
        return uv.Timer()
    elif has_PySide2 or has_PyQt5:
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

def on_file_changed(path, include=None, exclude=None, timeout=1, loop=None, recursive=True):

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

        if loop is None:
            loop_.start()
    
        return func
    
    return decorator
    
