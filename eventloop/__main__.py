from . import EventLoop, SingleShotTimer, FileSystemWatch, Schedule, Timer
from functools import partial
import os
from .base import Executor

def test_timer1():

    loop = EventLoop()

    timer0 = SingleShotTimer()
    timer1 = SingleShotTimer()
    timer2 = SingleShotTimer()
    timer3 = SingleShotTimer()
    timer4 = SingleShotTimer()
    timer5 = SingleShotTimer()

    def on_timer0():
        print("on_timer0")

    def on_timer1():
        print("on_timer1")
        timer2.stop()

    def on_timer2():
        print("on_timer2")

    def on_timer3():
        print("on_timer3")

    def on_timer4():
        print("on_timer4")
        loop.stop()
    
    def on_timer5():
        print("on_timer5")

    timer0.start(0, on_timer0) # fires
    timer1.start(1, on_timer1) # fires
    timer2.start(2, on_timer2) # not fires, stoped by timer1
    timer3.start(1, on_timer3) # not fires, stoped below
    timer4.start(4, on_timer4) # fires
    timer5.start(5, on_timer5) # not fires, evenloop stoped by timer4

    timer3.stop()

    loop.start()

def test_timer2():
    loop = EventLoop()
    d = {"count": 0}
    def on_timer():
        d["count"] += 1
        print("onTimer", d["count"])
        if d["count"] > 4:
            loop.stop()
    timer = Timer()
    timer.start(1, on_timer)
    loop.start()

def test_watch():
    def on_event(path, event):
        print(path, event)
    loop = EventLoop()
    watch = FileSystemWatch()
    watch.start(os.environ['TEST_DIR'], on_event)
    loop.start()

class TestExecutor(Executor):
    def execute(self, task):
        print("execute", task)
        return True

def test_schedule():
    loop = EventLoop()

    executor = TestExecutor()

    schedule = Schedule(executor)

    def add_item(task):
        schedule.append(task, 1)

    timer1 = SingleShotTimer()
    timer2 = SingleShotTimer()
    timer1.start(0.5, partial(add_item,1))
    timer2.start(0.5, partial(add_item,2))

    loop.start()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("test", choices=['timer1','timer2','watch','schedule'])
    args = parser.parse_args()
    func = globals()['test_' + args.test]
    func()

