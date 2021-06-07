==================================================
eventloop: Abstraction layer for filesystem events
==================================================

Eventloop uses any of: `pyuv` or `PySide2` or `PyQt5` installed in the system 
to provide uniform callback interface for filesystem events. And also timers.

Package intended to be a building block for utility scripts for recompiling 
or pushing files or restarting tests.

`pyuv` is used preferably as it's most efficient. `uv` is a library that 
powers nodejs event loop. Imagine you can `fs.watch` in python. No need to 
imagine, you can.

Installing
==========

eventloop can be installed via pip as follows:

::

    pip install eventloop

Author
======

Stanislav Doronin <mugisbrows@gmail.com>

Usage
=====

In most simple case you can just use `on_file_changed` decorator. It creates event loop, system watcher and schedule, then connects them, then starts the loop.

::

    from eventloop import on_file_changed

    if __name__ == "__main__":

        @on_file_changed("/path/to/dir")
        def your_handler(file_path):
            print(file_path)

Decorator accepts optional include and exclude args (list of globs or names to include or exclude files from watch) and timeout arg (read about timeout below) and loop arg.

If you need to watch more than one path you need to build and start `EventLoop` explicitly and pass it to decorators.

:: 

    from eventloop import EventLoop, on_file_changed

    if __name__ == "__main__":

        loop = EventLoop()

        @on_file_changed("/path/to/first/dir", loop=loop)
        def first_handler(file_path):
            print(file_path)

        @on_file_changed("/path/to/second/dir", loop=loop)
        def second_handler(file_path):
            print(file_path)

        loop.start()

For finer control over things you can use classes, first example can be rewriten as

::

    from eventloop import EventLoop, FileSystemWatch, Schedule, base

    class Executor(base.Executor):
        def execute(self, file_path):
            print(file_path)

    if __name__ == "__main__":
        loop = EventLoop()
        def on_change(file_path, event):
            schedule.append(file_path, timeout=1)
        watch = FileSystemWatch()
        watch.start("/path/to/dir", on_change)
        executor = Executor()
        schedule = Schedule(executor)
        loop.start()

`Schedule` caches (deduplicates) tasks appended within `timeout` interval, so for example three immediate consecutive `changed` events in same file end up in just one `Executor.execute(task)` call. `on_file_changed` decorator also uses `Schedule` to cache events.

License
=======

Eventloop is distributed under the terms of MIT license, check `LICENSE` file.

Contributing
============

If you'd like to contribute, fork the project, make changes, and send a pull
request. Have a look at the surrounding code and please, make yours look
alike :-)