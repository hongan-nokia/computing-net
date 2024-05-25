from time import sleep
from math import sqrt
from multiprocessing import Process, Queue
from random import randint
import os
from copy import deepcopy
import numpy as np
from cv2 import imread


class FakeComputingLoad(object):
    """ put anything into the queue to stop this process """

    def __init__(self):
        self.q = Queue()
        self.n = 0
        self._running = False

    def start_load(self, n_process=1):
        """ n_process specifies the number of computing processes to spawn. """
        self.n = n_process
        if self._running:
            return
        for _ in range(self.n):
            proc = Process(target=self.computing_intensive, )  # args=[self.q]
            proc.start()
            print(f'@@@ pid-{proc.pid} start')
        self._running = True

    def computing_intensive(self):
        """ finish loop whenever there is something in queue."""
        a = 0
        while self.q.empty():
            a += sqrt(randint(1, 100000))
        stop = self.q.get()
        sleep(0.01)  # wierd things may happen to multiprocess contension
        print(f'@@@ pid-{os.getpid()} {stop}')

    def pause_load(self):
        if self._running:
            for i in range(self.n):
                self.q.put('stop')
        self._running = False

    def stop(self):
        self.pause_load()


class FakeCap:
    """
    simulate opencv VideoCapture class
    """

    def __init__(self, imgsrc, nframe: int, fps: int = 30, dutycycle: float = 0.5, reverse_img_blank=False):
        self.n_frame = nframe
        self.fps = fps
        self.img = imread(imgsrc)
        if not reverse_img_blank:
            self._blank = np.zeros_like(self.img)
        else:
            self._blank = deepcopy(self.img)
            self.img = np.zeros_like(self._blank)
        self._n_img = int(nframe * dutycycle)
        self._cnt = 0

    def read(self):
        sleep(1 / self.fps)
        self._cnt = self._cnt + 1
        if (self._cnt % self.n_frame) < self._n_img:
            return (True, self.img)
        else:
            return (True, self._blank)

    get = lambda self, i: self.fps if i == 5 else 0
    release = lambda x: None


def main():
    load = FakeComputingLoad()
    for i in range(6):
        if i % 2 == 0:
            print('starting...')
            load.start_load(int(i / 2 + 1))
            sleep(10)
        else:
            print('stopping...')
            load.stop()
            sleep(3)


if __name__ == '__main__':
    main()
