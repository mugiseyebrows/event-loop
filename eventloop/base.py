
from .common import debug_print

class EventLoop:

    def start(self):
        pass

    def stop(self):
        pass

class Executor:
    def execute(self, task):
        return True

class Logger:
    def print_info(self, msg):
        print(msg)
    def print_error(self, msg):
        print(msg)

class FileSystemWatch:

    def start(self, path, callback, include = None, exclude = None, recursive = False):
        self._callback = callback
        self._path = path
        if include is None:
            include = []
        if exclude is None:
            exclude = []
        self._include = include
        self._exclude = exclude
    
    def stop(self):
        pass

class Timer:
    def start(self, interval, callback, once = False):
        self._callback = callback
        self._once = once

    def stop(self):
        pass