import asyncio
import os
import sys
import locale

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

    coros = []
    if has_pyuv:
        coros.append(run_test('env_pyuv', env_pyuv, quiet))
    if has_PySide2:
        coros.append(run_test('env_pyside2', env_pyside2, quiet))
        if has_qasync:
            coros.append(run_test('env_pyside2_qasync', env_pyside2_qasync, quiet))
    if has_PyQt5:
        coros.append(run_test('env_pyqt5', env_pyqt5, quiet))
        if has_qasync:
            coros.append(run_test('env_pyqt5_qasync', env_pyqt5_qasync, quiet))
    
    print("{} envs to test".format(len(coros)))
    await asyncio.gather(*coros)

asyncio.run(main())