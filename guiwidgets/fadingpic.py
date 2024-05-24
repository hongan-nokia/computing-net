# -*- coding: utf-8 -*-
"""
@Time: 5/17/2024 9:31 AM
@Author: Honggang Yuan
@Email: honggang.yuan@nokia-sbell.com
Description: 
"""
from PyQt5.QtCore import QObject, QPointF, QPropertyAnimation, QParallelAnimationGroup, pyqtProperty, QTimer
from PyQt5.QtWidgets import QGraphicsPixmapItem
from PyQt5.QtGui import QPixmap


class FadingPic(QObject):
    """ Wrap a QGraphicsPixmapItem and implement the fade in/out animation"""

    def __init__(self, pixmap, parent=None, fade_in_time=800, fade_out_time=800,
                 fadein_key_values: dict = None, fadeout_key_values: dict = None):
        super().__init__(parent)
        self.pixmap_item = QGraphicsPixmapItem(pixmap, parent=parent)
        self.pixmap_item.fadeIn = self.fadeIn  # copy the fadeIn/fadeOut methods to pixmap_item
        self.pixmap_item.fadeOut = self.fadeOut
        self.pixmap_item.opacity_status = self.opacity_status
        self.fadein_duration = fade_in_time
        self.fadeout_duration = fade_out_time
        self.pixmap_item.show()
        self.fadein_key_values = fadein_key_values
        self.fadeout_key_values = fadeout_key_values

    def opacity_status(self):
        return self.pixmap_item.opacity()

    def _set_opacity(self, opc):
        self.pixmap_item.setOpacity(opc)

    def fadeIn(self):
        anim = QPropertyAnimation(self, b'opacity')
        anim.setDuration(self.fadein_duration)
        anim.setStartValue(0)
        anim.setEndValue(1)
        if self.fadein_key_values:
            for k, v in self.fadein_key_values.items():
                anim.setKeyValueAt(k, v)
        # anim.setLoopCount(1)
        return anim

    def fadeOut(self):
        anim = QPropertyAnimation(self, b'opacity')
        anim.setDuration(self.fadeout_duration)
        anim.setStartValue(1)
        anim.setEndValue(0)
        if self.fadeout_key_values:
            for k, v in self.fadeout_key_values.items():
                anim.setKeyValueAt(k, v)
        # anim.setLoopCount(1)
        return anim

    opacity = pyqtProperty(float, fset=_set_opacity)


class BlinkingPic(FadingPic):
    """ Based on FadingPic, use a timer to achieve blinking effect instead of fading animation. """

    def __init__(self, parent, *args, **kwargs):
        """
        the following keyword arguments can be used to control blinking effect:
        blink_period: int - blink timer interval in ms
        auto_dim: bool - if True, hide the pic when blinking stops. default False.
        dim_opacity: float - the opacity leval (0~1) when the pic is dimmed
        """
        self.setParent(parent)
        self._blink_period = kwargs.pop('blink_period', 600)
        self._auto_dim = kwargs.pop('auto_dim', False)
        self._dim_opacity = kwargs.pop('dim_opacity', 0)
        super().__init__(*args, **kwargs)
        self._state = 0  # switch between 0 and 1, which corresponds to opacity
        self.blink_timer = QTimer()
        self.blink_timer.setInterval(self._blink_period)
        self.blink_timer.timeout.connect(self.swap_state)
        self.pixmap_item.start_blink = self.start_blink
        self.pixmap_item.stop_blink = self.stop_blink
        self.pixmap_item.swap_state = self.swap_state

    def start_blink(self):
        self.blink_timer.start()

    def stop_blink(self):
        self.blink_timer.stop()
        if self._auto_dim:
            self._set_opacity(self._dim_opacity)

    def swap_state(self):
        if self._state == 0:
            self._set_opacity(1)
            self._state = 1
        else:
            self._set_opacity(self._dim_opacity)
            self._state = 0
        self.blink_timer.start()

    def set_blink_period(self, period):
        self._blink_period = period


class FadingMovingPixmap(QObject):
    def __init__(self, pixmap, parent=None, begin_pos=(0, 0), end_pos=(100, 100), duration=1):
        '''
        begin_pos: Tuple[int,int]
        end_pos: Tuple[int,int]
        duration: floatingpoint number in s
        '''
        super().__init__(parent)
        self.pixmap_item = QGraphicsPixmapItem(pixmap, parent=parent)
        self.pixmap_item.setOpacity(0)
        # self.pixmap_item.show()
        self.duration = int(duration * 1000)
        self.begin_pos = QPointF(*begin_pos)
        self.end_pos = QPointF(*end_pos)
        self.anim = self.initAnim()
        self.pixmap_item.anim = self.anim

    def initAnim(self):
        animation_fade = QPropertyAnimation(self, b'opacity')
        animation_fade.setStartValue(0)
        animation_fade.setKeyValueAt(0.2, 0.8)
        animation_fade.setKeyValueAt(0.4, 1)
        animation_fade.setKeyValueAt(0.6, 1)
        animation_fade.setKeyValueAt(0.8, 0.8)
        animation_fade.setEndValue(0)
        animation_fade.setDuration(self.duration)
        # animation_fade.setEasingCurve(QEasingCurve.InBack)

        animation_move = QPropertyAnimation(self, b'pos')
        animation_move.setStartValue(self.begin_pos)
        animation_move.setEndValue(self.end_pos)
        animation_move.setDuration(self.duration)
        # animation_move.setEasingCurve(QEasingCurve.InBack)

        anim = QParallelAnimationGroup()
        anim.addAnimation(animation_fade)
        anim.addAnimation(animation_move)
        return anim

    def _set_opacity(self, opc):
        self.pixmap_item.setOpacity(opc)

    def _set_pos(self, pos):
        self.pixmap_item.setPos(pos)

    opacity = pyqtProperty(float, fset=_set_opacity)
    pos = pyqtProperty(QPointF, fset=_set_pos)  # position


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QGraphicsPixmapItem, QMainWindow, QApplication, QGraphicsScene, \
        QPushButton, QGraphicsView


    class Window(QMainWindow):
        def __init__(self):
            super().__init__()

            self.title = "QGraphicsItem fade in/out animation"
            self.top = 60
            self.left = 60
            self.right = 60
            self.width = 680
            self.height = 500
            self.InitWindow()

        def InitWindow(self):
            self.button1 = QPushButton('fade in', self)
            self.button1.setGeometry(40, 420, 100, 50)
            self.button2 = QPushButton('fade out', self)
            self.button2.setGeometry(180, 420, 100, 50)
            self.button3 = QPushButton('blink', self)
            self.button3.setGeometry(320, 420, 100, 50)
            self.button4 = QPushButton('stop', self)
            self.button4.setGeometry(470, 420, 100, 50)
            # self.picture_Qobj = FadingPic(QPixmap("D:/PythonScripts/fog2020/guiwidgets/images/man_at_work.png"))
            # self.picture_fadeInAnim = self.picture_Qobj.fadeIn()
            # self.picture_fadeOutAnim = self.picture_Qobj.fadeOut()
            self.picture = FadingPic(QPixmap("E:/PycharmProjects/Intern-Nokia_Sbell/fog2020/guiwidgets/images/man_at_work.png"),
                                     fade_in_time=1600, fadein_key_values={0.5: 0}).pixmap_item
            # self.picture = FadingPic(QPixmap("D:/PythonScripts/fog2020/guiwidgets/images/man_at_work.png"),
            #                          fade_in_time=1600, fadein_key_values={0.5: 0}).pixmap_item
            self.picture_fadeInAnim = self.picture.fadeIn()
            self.picture_fadeOutAnim = self.picture.fadeOut()

            self.blink_pic = BlinkingPic(QPixmap("E:/PycharmProjects/Intern-Nokia_Sbell/fog2020/guiwidgets/images/man_at_work.png"),
                                         auto_dim=False, dim_opacity=0.2).pixmap_item
            # self.blink_pic = BlinkingPic(QPixmap("D:/PythonScripts/fog2020/guiwidgets/images/man_at_work.png"),
            #                              auto_dim=False, dim_opacity=0.2).pixmap_item

            scene = QGraphicsScene()
            scene.addItem(self.picture)
            scene.addItem(self.blink_pic)

            self.picture.setPos(70, 100)
            print(self.picture, self.picture.pos())
            self.blink_pic.setPos(220, 100)

            self.view = QGraphicsView(scene, self)
            self.view.setGeometry(0, 0, 680, 400)

            self.setWindowTitle(self.title)
            self.setGeometry(self.left, self.top, self.width, self.height)
            self.init_connections()
            self.show()

        def init_connections(self):
            self.button1.clicked.connect(self.picture_fadeInAnim.start)
            self.button2.clicked.connect(self.picture_fadeOutAnim.start)
            self.button3.clicked.connect(self.blink_pic.start_blink)
            self.button4.clicked.connect(self.blink_pic.stop_blink)


    app = QApplication(sys.argv)
    window = Window()
    sys.exit(app.exec())
