# -*- coding: utf-8 -*-
"""
@Time: 5/16/2024 10:51 AM
@Author: Honggang Yuan
@Email: honggang.yuan@nokia-sbell.com
Description: 
"""
from threading import Thread, Lock, Event


class repeatTimer(Thread):
    """
    Call a function after a specified number of seconds, repetitively:
    Threads' start()/stop() methods can only be called once. But this class wraps around the
    start() method to support multiple-time call, which is more intuitive for a repeatTimer.
    However, stop() method closes the thread permanently and cannot be called multiple times.
    But resume() and pause() can be used without limitation, and is recommended for the timer
    behavior control.

    Usage:
        t = repeatTimer(30.0, f, args=None, kwargs=None, autostart=True)
        t.start()      # start timer.
        t.cancel()     # stop the timer's action, thread ends.
        t.stop()       # alias for cancel(), end thread.
        t.pause()      # timer is still alive but do not execute function.
        t.resume()     # resume from pause
    """

    def __init__(self, interval, function, autostart=True, name='', args=None, kwargs=None):
        """
        Arguments:
        interval - can be a real value or callable. If callable, should return a number which is
                   used as the timer's interval. For example, let interval = random.Random, can create
                   a random interval timer.
        function - the function that will be called whenever the timer reaches interval.
        """
        Thread.__init__(self)

        if callable(interval):
            self.interval_fn = interval
        else:
            self.interval_fn = lambda: interval

        self.function = function  # quote of function
        self.autostart = autostart
        self.name = name
        self.args = args if args is not None else []  # tuple
        self.kwargs = kwargs if kwargs is not None else {}  # dict

        self.finished = Event()
        self.lock = Lock()

        if self.autostart:
            self.start()
        else:
            self._pause = True

    def start(self):
        """ overload the start() method to add self._pause attribute """
        if self.is_alive():
            self.resume()
        else:  # first time start
            self._pause = False
            super().start()

    def cancel(self):
        """Stop the timer."""
        self.finished.set()
        print(f'repeat_timer {self.name} canceled!')

    def stop(self):
        self.cancel()

    def pause(self):  # pause
        """
        Pause function execution (timer is still alive).
        """
        self._pause = True

    def resume(self):
        """ Resume function execution. """
        self._pause = False

    def is_running(self):
        return not self._pause

    def is_paused(self):
        return self._pause

    def set_interval(self, interval):
        """
        interval = can be a real value or callable. If callable, should return a number which is
                   used as the timer's interval. For example, let interval = random.Random, can create
                   a random interval timer.
        """
        self.lock.acquire()
        if callable(interval):
            self.interval_fn = interval
        else:
            self.interval_fn = lambda: interval
        self.lock.release()

    def run(self):
        while True:
            self.lock.acquire()
            self.finished.wait(self.interval_fn())
            self.lock.release()
            if not self.finished.is_set():
                if self._pause:
                    pass
                else:
                    self.function(*self.args, **self.kwargs)
            else:
                break


if __name__ == '__main__':

    from time import sleep
    from random import uniform
    from functools import partial

    # the 1st demo: print hello world per 0.6 second, then change interval to 0.2 second
    print('the first demo:\n')


    def hello(greeting, name):
        print(f'{greeting}, {name}!')


    rt = repeatTimer(0.6, hello, args=["Hello", "World"], autostart=True)  # default is autostart=True
    rt.start()

    try:
        sleep(4)  # your long-running job goes here...
        print("changing interval to 0.2!")
        rt.set_interval(0.2)
        sleep(2.5)  # your long-running job goes here...
        print('Demo 1 finishes.\n')
    finally:
        rt.stop()  # better in a try/finally block to make sure the program ends!

    # the 2nd demo: random interval
    print('the 2nd demo:\n')
    rt = repeatTimer(partial(uniform, 0.01, 1.5), hello, args=["random", "interval"], autostart=True)
    rt.start()

    try:
        sleep(7)  # your long-running job goes here...
    finally:
        rt.stop()  # better in a try/finally block to make sure the program ends!
