from . import EventLoop, on_file_changed
import unittest
import time
import tempfile
from multiprocessing import Process
import os

pjoin = os.path.join

def modify_files(paths):
    time.sleep(0.1)
    for path in paths:
        dirname = os.path.dirname(path)
        os.makedirs(dirname, exist_ok=True)
        with open(path, 'a') as f:
            f.write('bump')
        time.sleep(0.01)

def rmfiles(paths):
    for path in paths:
        try:
            os.remove(path)
        except Exception as e:
            print(e)

class TestEventLoop(unittest.TestCase):
    def test_terminate(self):
        tmp = tempfile.mkdtemp()
        #print(tmp)
        t1 = time.time()
        @on_file_changed(tmp, terminate_after=2)
        def handler(path):
            pass
        t2 = time.time()
        self.assertAlmostEqual(t2 - t1, 2, delta=0.1)
        os.rmdir(tmp)

    def test_create(self):
        tmp = tempfile.mkdtemp()
        paths = [pjoin(tmp, "file.c")]
        proc = Process(target=modify_files, args=(paths,))
        proc.start()
        changed = []
        @on_file_changed(tmp, timeout=0.1, terminate_after=2)
        def handler(path):
            changed.append(path)
        proc.join()
        expected = paths
        rmfiles(expected)
        os.rmdir(tmp)
        self.assertEqual(changed, expected)

    def test_deduplicate(self):
        tmp = tempfile.mkdtemp()
        paths = [
            pjoin(tmp, "file.c"),
            pjoin(tmp, "file.c"),
            pjoin(tmp, "file.c"),
        ]
        proc = Process(target=modify_files, args=(paths,))
        proc.start()
        changed = []
        @on_file_changed(tmp, timeout=0.1, terminate_after=2)
        def handler(path):
            changed.append(path)
        proc.join()
        expected = [pjoin(tmp, "file.c")]
        rmfiles(expected)
        os.rmdir(tmp)
        self.assertEqual(changed, expected)

    def _test(self, tmp, ign, notign, recursive, include, exclude, expected):
        paths = [
            pjoin(tmp, "file.c"),
            pjoin(tmp, "file.o"),
            pjoin(ign, "file.c"),
            pjoin(ign, "file.o"),
            pjoin(notign, "file.c"),
            pjoin(notign, "file.o"),
        ]
        proc = Process(target=modify_files, args=(paths,))
        proc.start()
        changed = []
        @on_file_changed(tmp, recursive=recursive, include=include, exclude=exclude, timeout=0.1, terminate_after=2)
        def handler(path):
            changed.append(path)
        proc.join()
        rmfiles(paths)
        os.rmdir(ign)
        os.rmdir(notign)
        os.rmdir(tmp)
        if expected != changed:
            print("expected", expected)
            print("actual", changed)
        self.assertEqual(changed, expected)

    def test_recursive1(self):
        tmp = tempfile.mkdtemp()
        ign = os.path.join(tmp, 'ign')
        notign = os.path.join(tmp, 'notign')
        expected = [
            pjoin(tmp, "file.c"),
            pjoin(notign, "file.c"),
        ]
        
        self._test(tmp, ign, notign, recursive=True, include=None, exclude=['*.o', 'ign'], expected=expected)
        
    def test_recursive2(self):
        tmp = tempfile.mkdtemp()
        ign = os.path.join(tmp, 'ign')
        notign = os.path.join(tmp, 'notign')
        expected = [
            pjoin(tmp, "file.c"),
            pjoin(notign, "file.c"),
        ]
        self._test(tmp, ign, notign, recursive=True, include=['*.c'], exclude=['ign'], expected=expected)

    def test_not_recursive(self):
        tmp = tempfile.mkdtemp()
        ign = os.path.join(tmp, 'ign')
        notign = os.path.join(tmp, 'notign')
        expected = [
            pjoin(tmp, "file.c"),
        ]
        self._test(tmp, ign, notign, recursive=False, include=['*.c'], exclude=None, expected=expected)

if __name__ == "__main__":
    unittest.main()