import os
import sys

from .common import debug_print, walk
from . import base
from . import uv
from . import qt
from . import qta
from .common import flavour, FLAVOUR_NONE, FLAVOUR_PYUV, FLAVOUR_PYSIDE2, FLAVOUR_PYQT5, FLAVOUR_PYQT6, FLAVOUR_PYSIDE6, USE_QASYNC

"""
set DEBUG_EVENTLOOP=1
set DEBUG_EVENTLOOP=0
"""

def EventLoop(app = None):
    if USE_QASYNC:
        return qta.EventLoop(app)
    if flavour == FLAVOUR_PYUV:
        return uv.EventLoop()
    return qt.EventLoop(app)

def Server(app = None, parent = None):

    def psutil_server(app, parent):
        from . import ps
        return ps.Server()

    if flavour == FLAVOUR_PYUV:
        return psutil_server(app, parent)

    return qt.Server(parent)

def FileSystemWatch(loop):
    if flavour == FLAVOUR_PYUV:
        return uv.FileSystemWatch(loop)
    else:
        return qt.FileSystemWatch(loop)

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
            debug_print("executing copy task", task)
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
        
        watch = FileSystemWatch(loop_)
        schedule = Schedule(executor)
        watch.start(path, on_change, recursive=recursive, include=include, exclude=exclude)

        terminate_timer = None
        if terminate_after is not None:
            terminate_timer = SingleShotTimer()
            terminate_timer.start(terminate_after, loop_.stop)

        if loop is None:
            loop_.start()
        
        loop_._handles.append(watch)
        loop_._handles.append(schedule)
        loop_._handles.append(executor)
        loop_._handles.append(terminate_timer)

        return func
    
    return decorator
    
