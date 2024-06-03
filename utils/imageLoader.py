import sys

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QTimer, QObject, pyqtSignal, QSize


class ImageLoaderSignals(QObject):
    anim_over = pyqtSignal(str)  # node_id


class ImageLoader(QWidget, QtCore.QObject):

    def __init__(self, parent=None, **kwargs):
        self.direction = kwargs.pop('direction', None)
        self.image_url = kwargs.pop('image_url', None)
        self.img_scale_w = kwargs.pop('img_scale_w', 0)
        self.img_scale_h = kwargs.pop('img_scale_h', 0)
        self.geo = kwargs.pop('geo', [0, 0, 0, 0])
        self.interval = kwargs.pop('interval', 1)
        self.tag = kwargs.pop('title', "")
        self.tag_geo = kwargs.pop('tag_geo', [0, 0, 0, 0])
        super(ImageLoader, self).__init__(parent, **kwargs)
        self.setGeometry(self.geo[0], self.geo[1], self.geo[2], self.geo[3])

        # self.anim = self.initAnim()
        # self.setStyleSheet(
        #     "border-radius:0px;border-style:outset;border:none;background-color: {}".format(QColor(0, 0, 0).name()))
        self.label = QLabel(self)
        self.label.setGeometry(0, 0, 0, self.geo[3])
        # font = QtGui.QFont("微软雅黑", 10, QtGui.QFont.Bold)
        font = QtGui.QFont("微软雅黑", 16)
        self.tag_label = QLabel(parent=self)
        self.tag_label.setText(self.tag)
        self.tag_label.setWordWrap(True)
        self.tag_label.setGeometry(self.tag_geo[0], self.tag_geo[1], self.tag_geo[2], self.tag_geo[3])
        self.tag_label.setFont(font)
        self.tag_label.setVisible(False)

        self.scheduling_label = QLabel(parent=self)
        self.scheduling_label.setText("2. Joint scheduling, selecting optimal serving instance & optimal path")
        self.scheduling_label.setWordWrap(True)
        self.scheduling_label.setFont(font)
        self.scheduling_label.setGeometry(1070, 30, 180, 90)
        self.scheduling_label.setVisible(False)
        self.timer = None
        self.image = QPixmap(self.image_url).scaled(QSize(self.img_scale_w, self.img_scale_h))
        self.width = self.image.width()
        self.height = self.image.height()
        self.index = None
        self.destination = ''
        self.QtSignals = ImageLoaderSignals()

    # def show(self):
    #     self.setVisible(True)
    #     self.tag_label.setVisible(True)
    #
    # def hide(self):
    #     self.setVisible(False)
    #     self.tag_label.setVisible(False)

    def start(self, target_node):
        self.tag_label.setVisible(True)
        self.label.setVisible(True)
        self.destination = target_node
        self.timer = QTimer(self)
        # print(f">>>>>>>>>>> ImageLoad  target_node is {target_node}")
        # print(f">>>>>>>>>>> ImageLoad  target_node is {type(target_node)}")
        if self.direction == 'l2r':
            self.index = 0
            self.timer.timeout.connect(self.load_image_l2r)
        elif self.direction == 'r2l':
            self.index = self.width
            self.timer.timeout.connect(self.load_image_r2l)
        elif self.direction == 'lr2m':
            self.timer.timeout.connect(self.load_image_lr2m)
        elif self.direction == 'u2d':
            self.index = 0
            self.timer.timeout.connect(self.load_image_u2d)
        elif self.direction == 'd2u':
            self.index = self.height
            self.timer.timeout.connect(self.load_image_d2u)
        else:
            self.close()
        self.timer.start(self.interval)
        self.show()
        # self.lower()

    def load_image_l2r(self):
        if self.index < self.width:
            self.label.setPixmap(self.image.copy(0, 0, self.index, self.height))
            self.label.setGeometry(0, 0, self.index, self.height)
            self.index += 1
        else:
            # print(f"self.tag is : {self.tag}")
            if 'First' in self.tag:
                print(f"self.tag is : {self.tag}")
                self.scheduling_label.setVisible(True)
            self.timer.stop()
            # self.timer = None
            self.QtSignals.anim_over.emit(self.destination)
            self.index = 0
            print(f"l2r >>>  self.QtSignals.anim_over.emit({self.destination})")

    def load_image_r2l(self):
        if self.index > 0:
            self.label.setPixmap(self.image.copy(self.index, 0, self.width - self.index, self.height))
            self.label.setGeometry(self.index, 0, self.width - self.index, self.height)
            self.index -= 1
        else:
            self.timer.stop()
            # self.timer = None
            self.QtSignals.anim_over.emit(self.destination)
            # self.tag_label.setVisible(True)
            self.index = self.width
            print(f"r2l >>>  self.QtSignals.anim_over.emit({self.destination})")

    def load_image_u2d(self):
        if self.index < self.height:
            self.label.setPixmap(self.image.copy(0, 0, self.width, self.index))
            self.label.setGeometry(0, 0, self.width, self.index)
            self.index += 1
        else:
            self.tag_label.setVisible(True)
            self.timer.stop()
            # self.timer = None
            self.QtSignals.anim_over.emit(self.destination)
            self.index = 0
            print(f"u2d >>>  self.QtSignals.anim_over.emit({self.destination})")

    def load_image_d2u(self):
        if self.index > 0:
            self.label.setPixmap(self.image.copy(0, self.index, self.width, self.height - self.index))
            self.label.setGeometry(0, self.index, self.width, self.height - self.index)
            self.index -= 1
        else:
            self.tag_label.setVisible(True)
            self.timer.stop()
            # self.timer = None
            self.QtSignals.anim_over.emit(self.destination)
            self.index = self.height
            print(f"d2u >>>  self.QtSignals.anim_over.emit({self.destination})")

    def load_image_lr2m(self):
        if self.index_left < self.width / 2:
            self.label.setPixmap(self.image.copy(0, 0, self.index_left, self.height))
            self.label.setGeometry(self.width / 2 - self.index_left, 0, self.index_left * 2, self.height)
            self.index_left += 1
        elif self.index_right > self.width / 2:
            self.label.setPixmap(self.image.copy(self.index_right, 0, self.width - self.index_right, self.height))
            self.label.setGeometry(self.width / 2, 0, (self.width - self.index_right) * 2, self.height)
            self.index_right -= 1
        else:
            self.tag_label.setVisible(True)
            self.timer.stop()
            # self.timer = None
            self.QtSignals.anim_over.emit(self.destination)
            print(f"self.QtSignals.anim_over.emit({self.destination})")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    loader = ImageLoader(parent=None, geo=[270, 530, 1100, 600],
                         image_url='./guiwidgets/images/2023/service_provision.png',
                         direction="r2l", interval=3)
    loader.show()
    sys.exit(app.exec_())
