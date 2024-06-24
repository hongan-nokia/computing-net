import queue
from time import sleep

from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QLabel
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QTimer
from collections import deque

from utils.reversequeue import reverseQueue


class HeatMap(QWidget, QtCore.QObject):

    def __init__(self, parent=None, **kwargs):
        # self.image1_url = kwargs.pop('image_1', None)
        # self.image2_url = kwargs.pop('image_2', None)
        self.geo = kwargs.pop('geo', [0, 0, 0, 0])
        self.interval = kwargs.pop('interval', 1000)
        self.dataQ = kwargs.pop('data_q', None)

        super(HeatMap, self).__init__(parent, **kwargs)

        self.setGeometry(self.geo[0], self.geo[1], self.geo[2], self.geo[3])
        self.image1 = QPixmap('./images/hm3.png')
        self.image2 = QPixmap('./images/hm4.png')

        self.width1 = self.image1.width()
        self.height1 = self.image1.height()

        self.width2 = self.image2.width()
        self.height2 = self.image2.height()

        self.main_label = QLabel(self)
        self.main_label.setGeometry(0, 0, self.geo[2], self.geo[3])
        self.main_label.setPixmap(self.image1.copy(0, 0, self.width1, self.height1))
        self.main_label.setGeometry(0, 0, self.width1, self.height1)
        self.main_label.setVisible(True)

        self.tag_label = QLabel(parent=self)
        self.tag_label.setGeometry(3, 2, 0, self.geo[3])
        # self.tag_label.setPixmap(self.image2.copy(0, 0, self.width2, self.height2))
        # self.tag_label.setGeometry(0, 0, self.width2, int(self.height2 / 2))
        self.tag_label.setVisible(True)

        self.timer = QTimer(self)
        self.timer.setInterval(self.interval)
        self.timer.timeout.connect(self._load_tagLabel)

        self.index = 0
        self.avg_cpu = 0
        self.queue_cpu = deque([0] * 5, maxlen=5)


    def _load_tagLabel(self):
        # index = 10
        # if not self.dataQ.empty():
            # self.dataQ = reverseQueue(self.dataQ)
            # index = int(self.dataQ.get()[-1])
        # print(f"Heat map {self.index}")
        self.tag_label.setPixmap(self.image2.copy(0, 0, self.width2, self.height2))
        self.tag_label.setGeometry(3, 2, self.width2, int(self.height2 * ((100 - self.index) / 100)))
        self.tag_label.raise_()
