import os
import glob
import re
import sys

if os.environ.get('DEBUG_EVENTLOOP') == "1":
    debug_print = lambda *args, **kwargs: print(*args, **kwargs, file=sys.stderr)
else:
    debug_print = lambda *args, **kwargs: None

def fnmatch(path, pat):
    #debug_print('fnmatch(path, pat)', path, pat)
    if glob.has_magic(pat):
        return False
    if '/' in pat or '\\' in pat:
        # todo
        return False
    if sys.platform == 'win32':
        path_ = [e.lower() for e in re.split('[\\\\/]', path)]
        return pat.lower() in path_
    else:
        path_ = [e for e in re.split('[\\\\/]', path)]
        return pat in path_
    
def path_matches(path, include, exclude):
    name = os.path.basename(path)
    if include is not None and len(include) > 0:
        ok = False
        #debug_print("name path include", name, path, include)
        for pat in include:
            if glob.fnmatch.fnmatch(name, pat):
                #debug_print("ok = True")
                #debug_print("glob.fnmatch.fnmatch(name, pat)", name, pat)
                ok = True
                break
            if glob.fnmatch.fnmatch(path, pat):
                #debug_print("ok = True")
                #debug_print("glob.fnmatch.fnmatch(path, pat)", path, pat)
                ok = True
                break
            if fnmatch(path, pat):
                #debug_print("ok = True")
                #debug_print("fnmatch(path, pat)", path, pat)
                ok = True
                break
        if not ok:
            #debug_print("not ok")
            return False
    if exclude is not None:
        for pat in exclude:
            if glob.fnmatch.fnmatch(name, pat):
                return False
            if glob.fnmatch.fnmatch(path, pat):
                return False
            if fnmatch(path, pat):
                return False
    return True

def walk(path, include, exclude, all_dirs = False, recursive=True):
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

    if glob.has_magic(path):
        paths = glob.glob(path)
    else:
        paths = [path]

    queue = []
    dirs = []
    files = []

    for path in paths:
        if os.path.isfile(path):
            files.append(path)
        else:
            dirs.append(path)
            queue.append(path)

    while len(queue) > 0:
        path = queue.pop(0)
        try:
            for n in os.listdir(path):
                path_ = os.path.join(path, n)
                is_dir = os.path.isdir(path_)
                if path_matches(path_, include, exclude):
                    if is_dir:
                        dirs.append(path_)
                        queue.append(path_)
                    else:
                        files.append(path_)
                elif all_dirs and is_dir:
                    dirs.append(path_)
                if is_dir and recursive:
                    queue.append(path_)
        except PermissionError as e:
            debug_print(e)
        except FileNotFoundError as e:
            debug_print(e)
        except NotADirectoryError as e:
            debug_print(e)
    return dirs, files

(
    EVENT_RENAME,
    EVENT_CHANGE
) = range(2)

(
    FLAVOUR_NONE,
    FLAVOUR_PYUV,
    FLAVOUR_PYSIDE6,
    FLAVOUR_PYQT6,
    FLAVOUR_PYSIDE2,
    FLAVOUR_PYQT5,
) = range(6)

flavour = FLAVOUR_NONE

"""
test = {n: os.environ.get(n) for n in ['USE_PYUV', 'USE_PYSIDE2', 'USE_PYQT5']}
ones = [v for v in test.values() if v == '1']
if len(ones) > 1:
    keys = [k for k in test.keys() if test[k] == '1']
    print("warning: {} env variables are set to 1, you should only set one of them".format(" and ".join(keys)))
"""

if os.environ.get('USE_PYUV') is not None:
    import pyuv
    flavour = FLAVOUR_PYUV
else:
    QT_API = os.environ.get('QT_API')
    if QT_API is not None:
        flavour = {
            'pyqt5':FLAVOUR_PYQT5,
            'pyside2':FLAVOUR_PYSIDE2,
            'pyqt6':FLAVOUR_PYQT6,
            'pyside6':FLAVOUR_PYSIDE6,
        }[QT_API]
    else:
        try:
            import pyuv
            flavour = FLAVOUR_PYUV
        except ImportError:
            try:
                from PySide6 import QtCore
                flavour = FLAVOUR_PYSIDE6
            except ImportError:
                try:
                    from PyQt6 import QtCore
                    flavour = FLAVOUR_PYQT6
                except ImportError:
                    try:
                        from PySide2 import QtCore
                        flavour = FLAVOUR_PYSIDE2
                    except ImportError:
                        try:
                            from PyQt5 import QtCore
                            flavour = FLAVOUR_PYQT5
                        except ImportError:
                            raise ValueError('Eventloop needs one of packages: pyuv, pyqt5, pyside2, pyqt6, pyside6')

USE_QASYNC = False
if os.environ.get('USE_QASYNC') is not None:
    import qasync
    USE_QASYNC = True