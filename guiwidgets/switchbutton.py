# -*- coding: utf-8 -*-
"""
@Time: 5/17/2024 9:36 AM
@Author: Honggang Yuan
@Email: honggang.yuan@nokia-sbell.com
Description: 
"""
"""
A QSwitchButton class implemented based on QSlider (and QLabel).

"""

from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QObject
from PyQt5.QtWidgets import (QApplication, QLabel, QHBoxLayout, QVBoxLayout,
                             QSlider, QWidget, QDialog)
from PyQt5.QtGui import QFont

SLIDER_QSS = '''
QSlider::groove:horizontal {
border: 1px solid #bbb;
background: white;
height: 20px;
border-radius: 4px;
}

QSlider::sub-page:horizontal {
background: qlineargradient(x1: 0, y1: 0,    x2: 0, y2: 1,
    stop: 0 #66e, stop: 1 #bbf);
background: qlineargradient(x1: 0, y1: 0.2, x2: 1, y2: 1,
    stop: 0 #bbf, stop: 1 #55f);
border: 1px solid #777;
height: 20px;
border-radius: 4px;
}

QSlider::add-page:horizontal {
background: #fff;
border: 1px solid #777;
height: 20px;
border-radius: 4px;
}

QSlider::handle:horizontal {
background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
    stop:0 #eee, stop:1 #ccc);
border: 1px solid #777;
width: 30px;
margin-top: -2px;
margin-bottom: -2px;
border-radius: 2px;
}

QSlider::handle:horizontal:hover {
background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
    stop:0 #fff, stop:1 #ddd);
border: 1px solid #444;
border-radius: 4px;
}

QSlider::sub-page:horizontal:disabled {
background: #bbb;
border-color: #999;
}

QSlider::add-page:horizontal:disabled {
background: #eee;
border-color: #999;
}

QSlider::handle:horizontal:disabled {
background: #eee;
border: 1px solid #aaa;
border-radius: 4px;
}'''


class SigWrapper(QObject):
    turned_on = pyqtSignal()
    turned_off = pyqtSignal()


class QSwitchButton(QWidget):
    """
    QSwitchButton.switch is the slider switch in the middle
    QSwitchButton.off_option is a label on the left
    QSwitchButton.on_option is a label on the right

    Signals:
        QSwitchButton.turned_on
        QSwitchButton.turned_off

    Slots:
        QSwitchButton.turnOn()
        QSwitchButton.turnOff()

    other methods:
        QSwitchButton.value() - return -1(off) or 1(on)
        QSwitchButton.state() - return text string on the either of the label
    """

    def __init__(self, *args, **kwargs):
        """
        kwargs:
            off_option - string
            on_option  - string
            parent     - QWidget
        """
        off_opt = kwargs.pop('off_option', None)
        on_opt = kwargs.pop('on_option', None)
        super().__init__(*args, **kwargs)
        self.switch = QSlider(self)
        self.switch.setRange(-1, 1)
        self.switch.setTickInterval(2)
        self.switch.setSingleStep(2)
        self.switch.setStyleSheet(SLIDER_QSS)
        self.switch.setOrientation(Qt.Horizontal)
        self.switch.setFixedSize(60, 24)
        self.switch.setValue(-1)
        self.switch.setTracking(False)
        font = QFont("Nokia Pure Text", 11)
        layout = QHBoxLayout()
        if off_opt:
            self._off_option = off_opt
            self.off_label = QLabel(f"{off_opt} ")
            self.off_label.setFont(font)
            self.off_label.setAlignment(Qt.AlignRight)
            self.off_label.mousePressEvent = self._turnOff
            layout.addWidget(self.off_label)
        else:
            self._off_option = '-1'
        layout.addWidget(self.switch)
        if on_opt:
            self._on_option = on_opt
            self.on_label = QLabel(f" {on_opt}")
            self.on_label.setFont(font)
            self.on_label.setAlignment(Qt.AlignLeft)
            self.on_label.mousePressEvent = self._turnOn
            layout.addWidget(self.on_label)
        else:
            self._on_option = '1'

        self.setLayout(layout)
        self._sgnlwrapper = SigWrapper()
        self.turned_off = self._sgnlwrapper.turned_off
        self.turned_on = self._sgnlwrapper.turned_on
        self.switch.valueChanged.connect(self._emit_signal_on_val_change)

    def _emit_signal_on_val_change(self):
        if self.switch.value() == -1:
            self.turned_off.emit()
        else:
            self.turned_on.emit()

    def _turnOn(self, event):
        self.switch.setValue(1)

    def _turnOff(self, event):
        self.switch.setValue(-1)

    @pyqtSlot()
    def turnOn(self):
        self.switch.setValue(1)

    @pyqtSlot()
    def turnOff(self):
        self.switch.setValue(-1)

    def value(self):
        return self.switch.value()

    def state(self):
        return self._on_option if self.value() == 1 else self._off_option


if __name__ == '__main__':
    import sys


    class Window(QDialog):
        def __init__(self, parent=None):
            super(Window, self).__init__(parent)

            self.message = QLabel("switch turned off")
            self.switch = QSwitchButton(off_option='off', on_option='on')

            layout = QVBoxLayout()
            layout.addWidget(self.message)
            layout.addWidget(self.switch)

            self.switch.turned_off.connect(self.changeText)
            self.switch.turned_on.connect(self.changeText)

            self.setLayout(layout)

        def changeText(self):
            self.message.setText(f"switch turned {self.switch.state().strip()}")


    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
