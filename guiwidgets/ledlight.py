# -*- coding: utf-8 -*-
"""
@Time: 5/17/2024 9:33 AM
@Author: Honggang Yuan
@Email: honggang.yuan@nokia-sbell.com
Description: 
"""

#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


# Python imports
# import numpy as np
# import pyautogui

# PyQt5 imports
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QPushButton


# User imports


class Led(QPushButton):
    # black = np.array([0x00, 0x00, 0x00], dtype=np.uint8)
    # white = np.array([0xff, 0xff, 0xff], dtype=np.uint8)
    # blue = np.array([0x73, 0xce, 0xf4], dtype=np.uint8)
    # green1 = np.array([0xad, 0xff, 0x2f], dtype=np.uint8)
    # green = np.array([0x01, 0xff, 0x53], dtype=np.uint8)
    # orange = np.array([0xff, 0xa5, 0x00], dtype=np.uint8)
    # purple = np.array([0xaf, 0x00, 0xff], dtype=np.uint8)
    # red = np.array([0xff, 0x00, 0x00], dtype=np.uint8)
    # red1 = np.array([0xf4, 0x37, 0x53], dtype=np.uint8)
    # yellow = np.array([0xff, 0xff, 0x00], dtype=np.uint8)
    # gray = np.array([0xc0, 0xc0, 0xc0], dtype=np.uint8)

    black = [0x00, 0x00, 0x00]
    white = [0xff, 0xff, 0xff]
    blue = [0x73, 0xce, 0xf4]
    green1 = [0xad, 0xff, 0x2f]
    green = [0x01, 0xff, 0x53]
    orange = [0xff, 0xa5, 0x00]
    purple = [0xaf, 0x00, 0xff]
    red = [0xff, 0x00, 0x00]
    red1 = [0xf4, 0x37, 0x53]
    yellow = [0xff, 0xff, 0x00]
    gray = [0xc0, 0xc0, 0xc0]

    capsule = 1
    circle = 2
    rectangle = 3

    shapecode = {'capsule': capsule, 'cap': capsule, 1: capsule,
                 'circle': circle, 'cir': circle, 2: circle,
                 'rectangle': rectangle, 'rect': rectangle, 3: rectangle}

    def __init__(self, parent, on_color=green, off_color=black,
                 warning_color=orange, shape=rectangle, clickable=False):
        super().__init__()
        if clickable:
            self.setEnabled(True)
        else:
            self.setDisabled(True)

        self._qss = 'QPushButton {{ \
                                   border: 3px solid lightgray; \
                                   border-radius: {}px; \
                                   background-color: \
                                       QLinearGradient( \
                                           y1: 0, y2: 1, \
                                           stop: 0 white, \
                                           stop: 0.2 #{}, \
                                           stop: 0.8 #{}, \
                                           stop: 1 #{} \
                                       ); \
                                 }}'
        self._on_qss = ''
        self._off_qss = ''
        self._warning_qss = ''

        self._status = 0  # 0-off, 1-on, -1-warning
        self._end_radius = 0

        # Properties that will trigger changes on qss.
        self.__on_color = None
        self.__off_color = None
        self.__warning_color = None
        self.__shape = None
        self.__height = 0

        self._on_color = on_color
        self._off_color = off_color
        self._warning_color = warning_color
        self._shape = Led.shapecode[shape]
        self._height = self.sizeHint().height()

        self.set_status(0)

    # =================================================== Reimplemented Methods
    def mousePressEvent(self, event):
        QPushButton.mousePressEvent(self, event)
        if self._status == 0:
            self.set_status(1)
        else:
            self.set_status(0)

    def sizeHint(self):
        # res_w, res_h = pyautogui.size()  # Available resolution geometry
        res_w, res_h = (1920, 1080)
        if self._shape == Led.capsule:
            base_w = 50
            base_h = 30
        elif self._shape == Led.circle:
            base_w = 30
            base_h = 30
        elif self._shape == Led.rectangle:
            base_w = 40
            base_h = 30
        width = int(base_w * res_h / 1080)
        height = int(base_h * res_h / 1080)
        return QSize(width, height)

    def resizeEvent(self, event):
        self._height = self.size().height()
        QPushButton.resizeEvent(self, event)

    def setFixedSize(self, width, height):
        self._height = height
        if self._shape == Led.circle:
            QPushButton.setFixedSize(self, height, height)
        else:
            QPushButton.setFixedSize(self, width, height)

    # ============================================================== Properties
    @property
    def _on_color(self):
        return self.__on_color

    @_on_color.setter
    def _on_color(self, color):
        self.__on_color = color
        self._update_on_qss()

    @_on_color.deleter
    def _on_color(self):
        del self.__on_color

    @property
    def _off_color(self):
        return self.__off_color

    @_off_color.setter
    def _off_color(self, color):
        self.__off_color = color
        self._update_off_qss()

    @_off_color.deleter
    def _off_color(self):
        del self.__off_color

    @property
    def _warning_color(self):
        return self.__warning_color

    @_warning_color.setter
    def _warning_color(self, color):
        self.__warning_color = color
        self._update_warning_qss()

    @_warning_color.deleter
    def _warning_color(self):
        del self.__warning_color

    @property
    def _shape(self):
        return self.__shape

    @_shape.setter
    def _shape(self, shape):
        self.__shape = shape
        self._update_end_radius()
        self._update_on_qss()
        self._update_off_qss()
        self._update_warning_qss()
        self.set_status(self._status)

    @_shape.deleter
    def _shape(self):
        del self.__shape

    @property
    def _height(self):
        return self.__height

    @_height.setter
    def _height(self, height):
        self.__height = height
        self._update_end_radius()
        self._update_on_qss()
        self._update_off_qss()
        self._update_warning_qss()
        self.set_status(self._status)

    @_height.deleter
    def _height(self):
        del self.__height

    # ================================================================= Methods
    def _update_on_qss(self):
        color, grad = self._get_gradient(self.__on_color)
        self._on_qss = self._qss.format(self._end_radius, grad, color, color)

    def _update_off_qss(self):
        color, grad = self._get_gradient(self.__off_color)
        self._off_qss = self._qss.format(self._end_radius, grad, color, color)

    def _update_warning_qss(self):
        color, grad = self._get_gradient(self.__warning_color)
        self._warning_qss = self._qss.format(self._end_radius, grad, color, color)

    def _get_gradient(self, color):
        # grad = ((self.white - color) / 2).astype(np.uint8) + color
        grad = [int((self.white[i] - color[i]) / 2 + color[i]) for i in range(3)]
        grad = '{:02X}{:02X}{:02X}'.format(grad[0], grad[1], grad[2])
        color = '{:02X}{:02X}{:02X}'.format(color[0], color[1], color[2])
        return color, grad

    def _update_end_radius(self):
        if self.__shape == Led.rectangle:
            self._end_radius = int(self.__height / 10)
        else:
            self._end_radius = int(self.__height / 2)

    def _toggle_on(self):
        self.setStyleSheet(self._on_qss)

    def _toggle_off(self):
        self.setStyleSheet(self._off_qss)

    def _toggle_warning(self):
        self.setStyleSheet(self._warning_qss)

    def set_on_color(self, color):
        self._on_color = color

    def set_off_color(self, color):
        self._off_color = color

    def set_warning_color(self, color):
        self._warning_color = color

    def set_shape(self, shape):
        self._shape = shape

    def set_status(self, status):
        self._status = status
        if (self._status == 1):  # on
            self._toggle_on()
        elif (self._status == 0):  # off
            self._toggle_off()
        elif (self._status == -1):  # warning
            self._toggle_warning()
        else:
            pass

    def turn_on(self, status=1):
        self.set_status(status)

    def turn_off(self, status=0):
        self.set_status(status)

    def turn_warning(self, status=-1):
        self.set_status(status)

    def revert_status(self):
        if self._status == 1:
            self.set_status(0)
        else:
            self.set_status(1)

    def is_on(self):
        return True if self._status == 1 else False

    def is_off(self):
        return True if self._status == 0 else False

    def is_warning(self):
        return True if self._status == -1 else False


if __name__ == '__main__':
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtWidgets import QGridLayout
    from PyQt5.QtWidgets import QWidget
    import sys


    class Demo(QWidget):
        def __init__(self, parent=None):
            QWidget.__init__(self, parent)
            # self._shape = np.array(['capsule', 'circle', 'rectangle'])
            # self._color = np.array(['blue', 'green', 'orange', 'purple', 'red',
            #                         'yellow'])
            self._shape = ['capsule', 'circle', 'rectangle']
            self._color = ['blue', 'green', 'orange', 'purple', 'red', 'yellow']
            self._layout = QGridLayout(self)
            self._create_leds()
            self._arrange_leds()

        def keyPressEvent(self, e):
            if e.key() == Qt.Key_Escape:
                self.close()

        def _create_leds(self):
            for s in self._shape:
                for c in self._color:
                    exec('self._{}_{} = Led(self, on_color=Led.{}, \
                          shape=Led.{}, clickable=True)'.format(s, c, c, s))
                    exec('self._{}_{}.setFocusPolicy(Qt.NoFocus)'.format(s, c))

        def _arrange_leds(self):
            for r in range(3):
                for c in range(5):
                    exec('self._layout.addWidget(self._{}_{}, {}, {}, 1, 1, \
                          Qt.AlignCenter)'
                         .format(self._shape[r], self._color[c], r, c))
                    c += 1
                r += 1


    app = QApplication(sys.argv)
    demo = Demo()
    demo.show()
    sys.exit(app.exec_())
