# -*- coding: utf-8 -*-
"""
@Time: 5/17/2024 9:36 AM
@Author: Honggang Yuan
@Email: honggang.yuan@nokia-sbell.com
Description: 
"""
from PyQt5.QtCore import QObject, QPropertyAnimation, pyqtProperty, pyqtSlot
from PyQt5.QtWidgets import QGraphicsPixmapItem
from PyQt5.QtGui import QPixmap


class RotatableItem(QObject):
    """ Wraps a QGraphicsPixmapItem with the ability to show rotation animation.

    To use this class, initiate an object with the target QPixmap, and
    then add the pixmap_item into your QGraphicsScene.

    To rotate the item, either call RoatableItem.rotate(dgr), or use the reference of
    the pixmap item: RoatableItem.pixmap_item.rotate(dgr)

    To show spinning animation, first get an QPropertyAnimation object by calling
        `example_anim = RoatableItem.RotationAnimation()`
    Then simply call example_anim.start() or example_anim.stpp().

    """

    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self.pixmap_item = QGraphicsPixmapItem(pixmap, parent=parent)
        self.pixmap_item.setTransformOriginPoint(self.pixmap_item.boundingRect().center())
        # self.clickedSgnlWrapper = itemClickedSgnlWrapper()
        # self.clicked = self.clickedSgnlWrapper.sgnl
        # self.pixmap_item.mousePressEvent = self.clickEventHandler
        self.pixmap_item.rotate = self.rotate
        self.pixmap_item.RotationAnimation = self.RotationAnimation
        self._current_dgr = 0

    @pyqtSlot(float)
    def rotate_dgr(self, dgr: float = 15):
        self._current_dgr += dgr
        if self._current_dgr >= 360: self._current_dgr = 0
        self.pixmap_item.setRotation(self._current_dgr)

    def rotate(self):
        self.rotate_dgr()

    def _set_rotation_dgr(self, dgr):
        self.pixmap_item.setRotation(dgr)

    def RotationAnimation(self):
        anim = QPropertyAnimation(self, b'rotation')
        anim.setDuration(1000)
        anim.setStartValue(0)
        anim.setEndValue(360)
        anim.setLoopCount(-1)
        return anim

    # define a property named as 'rotation', and designate a setter function.
    rotation = pyqtProperty(float, fset=_set_rotation_dgr)
