import psutil
import subprocess
from .common import debug_print
import sys

class Server:
    def __init__(self, parent = None):
        self._pid = None

    def restart(self, cmd, cwd = None):
        if self._pid is not None:
            try:
                proc = psutil.Process(self._pid)
                debug_print("killing")
                proc.kill()
                debug_print("killed")
            except psutil.NoSuchProcess:
                debug_print("psutil.NoSuchProcess")
        proc = subprocess.Popen(cmd, cwd=cwd)
        self._pid = proc.pid
        debug_print("self._pid", self._pid)