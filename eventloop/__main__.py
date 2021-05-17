from . import *

import os

def test_timer1():

    loop = EventLoop()

    timer1 = SingleShotTimer()
    timer2 = SingleShotTimer()
    timer3 = SingleShotTimer()
    timer4 = SingleShotTimer()
    timer5 = SingleShotTimer()

    def onTimer1():
        print("onTimer1")
        timer2.stop()

    def onTimer2():
        print("onTimer2")

    def onTimer3():
        print("onTimer3")

    def onTimer4():
        print("onTimer4")
        loop.stop()
    
    def onTimer5():
        print("onTimer5")

    timer1.start(1, onTimer1)
    timer2.start(2, onTimer2)
    timer3.start(1, onTimer3)
    timer4.start(4, onTimer4)
    timer5.start(5, onTimer5)

    timer3.stop()

    loop.start()

def test_timer2():
    loop = EventLoop()
    d = {"count": 0}
    def onTimer():
        d["count"] += 1
        print("onTimer", d["count"])
        if d["count"] > 4:
            loop.stop()
    timer = Timer()
    timer.start(1, onTimer)
    loop.start()

def test_watch():
    def onEvent(path, event):
        print(path, event)
    loop = EventLoop()
    watch = FileSystemWatch()
    watch.start(os.environ['TEST_DIR'], onEvent)
    loop.start()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("test",choices=['timer1','timer2','watch'])
    args = parser.parse_args()
    if args.test == 'timer1':
        test_timer1()
    elif args.test == 'timer2':
        test_timer2()
    elif args.test == 'watch':
        test_watch()

