@echo off
set DEBUG_EVENTLOOP=1
set USE_QASYNC=1
set USE_PYUV=0
set USE_PYSIDE2=1
set USE_PYQT5=0
python -m eventloop.test