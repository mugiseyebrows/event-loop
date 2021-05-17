==================================================
eventloop: Abstraction layer for filesystem events
==================================================

Eventloop uses any of: `pyuv` or `PySide2` or `PyQt5` installed in the system 
to provide uniform callback interface for filesystem events. And also timers.

Package intended to be a building block for utility scripts for recompiling 
or pushing files or restarting tests.

`pyuv` is used preferably as it's most efficient. `uv` is a library that 
powers nodejs event loop. Imagine you can `fs.watch` in python. No need to 
imagine, now you can.

Author
======

Stanislav Doronin <mugisbrows@gmail.com>

License
=======

Eventloop is distributed under the terms of MIT license, check LICENSE file.

Contributing
============

If you'd like to contribute, fork the project, make changes, and send a pull
request. Have a look at the surrounding code and please, make yours look
alike :-)