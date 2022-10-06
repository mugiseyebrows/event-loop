import asyncio
import os
import sys
import locale
import argparse

try:
    import pyuv
except ImportError:
    pass

try:
    from PySide2 import QtCore
except ImportError:
    pass

try:
    from PyQt5 import QtCore
except ImportError:
    pass

try:
    import qasync
except ImportError:
    pass

stdout_codec = 'utf-8'
if sys.platform == 'win32':
    loc = locale.getlocale()
    if loc == ('Russian_Russia', '1251'):
        stdout_codec = 'cp1251'
    
def merge_dicts(dict1, dict2):
    return {**dict1, **dict2}

def create_env(env):
    return merge_dicts(os.environ, env)

async def run_test(name, env, quiet = True):
    if quiet:
        cmd = ["python", "-m", "eventloop.test", "-q"]
    else:
        cmd = ["python", "-m", "eventloop.test"]
    proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, env=create_env(env))
    stdout, stderr = await proc.communicate()
    print(name)
    print(stdout.decode(stdout_codec))
    print(stderr.decode(stdout_codec))
    await proc.wait()

async def main():

    DEBUG_EVENTLOOP = '0'

    env_pyuv = {
        'DEBUG_EVENTLOOP':DEBUG_EVENTLOOP,
        'USE_QASYNC':'0',
        'USE_PYUV':'1',
        'USE_PYSIDE2':'0',
        'USE_PYQT5':'0',
    }
    env_pyside2 = {
        'DEBUG_EVENTLOOP':DEBUG_EVENTLOOP,
        'USE_QASYNC':'0',
        'USE_PYUV':'0',
        'USE_PYSIDE2':'1',
        'USE_PYQT5':'0',
    }
    env_pyqt5 = {
        'DEBUG_EVENTLOOP':DEBUG_EVENTLOOP,
        'USE_QASYNC':'0',
        'USE_PYUV':'0',
        'USE_PYSIDE2':'0',
        'USE_PYQT5':'1',
    }
    env_pyside2_qasync = {
        'DEBUG_EVENTLOOP':DEBUG_EVENTLOOP,
        'USE_QASYNC':'1',
        'USE_PYUV':'0',
        'USE_PYSIDE2':'1',
        'USE_PYQT5':'0',
    }
    env_pyqt5_qasync = {
        'DEBUG_EVENTLOOP':DEBUG_EVENTLOOP,
        'USE_QASYNC':'1',
        'USE_PYUV':'0',
        'USE_PYSIDE2':'0',
        'USE_PYQT5':'1',
    }

    quiet = False

    has_pyuv = sys.modules.get('pyuv') is not None
    has_PySide2 = sys.modules.get('PySide2') is not None
    has_PyQt5 = sys.modules.get('PyQt5') is not None
    has_qasync = sys.modules.get('qasync') is not None

    parser = argparse.ArgumentParser()
    parser.add_argument('names', nargs='+', choices=['pyuv','qt5','pyside2','qt5a','pyside2a','all'])
    args = parser.parse_args()
    #print(args); exit(0)
    names = args.names

    do_pyuv = has_pyuv and ('all' in names or 'pyuv' in names)
    do_PySide2 = has_PySide2 and ('all' in names or 'pyside2' in names)
    do_PySide2_qasync = has_PySide2 and has_qasync and ('all' in names or 'pyside2a' in names)
    do_PyQt5 = has_PyQt5 and ('all' in names or 'qt5' in names)
    do_PyQt5_qasync = has_PyQt5 and has_qasync and ('all' in names or 'qt5a' in names)

    coros = []
    if do_pyuv:
        coros.append(run_test('env_pyuv', env_pyuv, quiet))
    if do_PySide2:
        coros.append(run_test('env_pyside2', env_pyside2, quiet))
    if do_PySide2_qasync:
        coros.append(run_test('env_pyside2_qasync', env_pyside2_qasync, quiet))
    if do_PyQt5:
        coros.append(run_test('env_pyqt5', env_pyqt5, quiet))
    if do_PyQt5_qasync:
        coros.append(run_test('env_pyqt5_qasync', env_pyqt5_qasync, quiet))
    
    print("{} envs to test".format(len(coros)))
    await asyncio.gather(*coros)

asyncio.run(main())