# -*- coding: utf-8 -*-
"""
@Time: 5/17/2024 11:46 AM
@Author: Honggang Yuan
@Email: honggang.yuan@nokia-sbell.com
Description: 
"""
from PyQt5.QtCore import Qt, QRectF, QPointF, QSize, QPropertyAnimation, pyqtSlot
from PyQt5.QtGui import QColor, QConicalGradient, QPainterPath, QPainter, QFont, QFontMetrics
from PyQt5.QtWidgets import QWidget, QSizePolicy


class SpeedMeter(QWidget):
    """QWidget of a Speedometer
    Use `setSpeed(speed)` method to update display.
    Use `reset()` to reset back to 0 with an animation effect.

    To create animation of speed changing, use QPropertyAnimation on 'value':
        anim = QPropertyAnimation(Speedometer, b"value")
        anim.setStartValue(x)
        anim.setEndValue(y)
        anim.setDuration(ms)
        anim.start()

    NOTE: By default this is clickable, i.e. can emit a `clicked` signal. But this
          feature is implemented by overlading mouseReleaseEvent() method. Pass
          keyword agument clickable=False to prevent this behavior.
    """

    def __init__(self, title: str, unit: str, min_value: float, max_value: float,
                 init_value: float = None, parent: QWidget = None, clickable: bool = True):
        QWidget.__init__(self, parent)
        self.min_value = min_value
        self.max_value = max_value
        initv = 00
        if init_value:
            if init_value < 0:
                initv = 0
            elif init_value > max_value:
                initv = max_value
            else:
                initv = init_value
        self.speed = initv
        self.displayPowerPath = True
        self.title = title
        self.power = 100.0 * (self.speed - self.min_value) / (self.max_value - self.min_value)
        self.powerGradient = QConicalGradient(0, 0, 180)
        self.powerGradient.setColorAt(0, Qt.GlobalColor.red)
        self.powerGradient.setColorAt(0.375, Qt.GlobalColor.yellow)
        self.powerGradient.setColorAt(0.75, Qt.GlobalColor.green)
        self.unitTextColor = QColor(Qt.GlobalColor.white)
        self.speedTextColor = QColor(Qt.GlobalColor.white)
        self.powerPathColor = QColor(Qt.GlobalColor.gray)
        self.unit = unit
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Ignored)

        self.anim_reset = QPropertyAnimation(self, b"value")
        self.anim_reset.setDuration(500)
        self.anim_reset.setEndValue(0)

    @pyqtSlot(float)
    def setSpeed(self, speed):
        self.speed = speed
        self.power = 100.0 * (self.speed - self.min_value) / (self.max_value - self.min_value)
        self.update()

    def setUnit(self, unit):
        self.unit = unit

    def setPowerGradient(self, gradient):
        self.powerGradient = gradient

    def setDisplayPowerPath(self, displayPowerPath):
        self.displayPowerPath = displayPowerPath

    def setUnitTextColor(self, color):
        self.unitTextColor = color

    def setSpeedTextColor(self, color):
        self.speedTextColor = color

    def setPowerPathColor(self, color):
        self.powerPathColor = color

    def sizeHint(self):
        return QSize(100, 100)

    def reset(self):
        self.anim_reset.setStartValue(self.speed)
        self.anim_reset.start()

    def _emit_clicked_signal(self, e):
        self._click_signal_wraper.clicked_sgnl.emit()

    def paintEvent(self, evt):
        x1 = QPointF(0, -70)
        x2 = QPointF(0, -90)
        x3 = QPointF(-90, 0)
        x4 = QPointF(-70, 0)
        extRect = QRectF(-90, -90, 180, 180)
        intRect = QRectF(-70, -70, 140, 140)
        midRect = QRectF(-44, -80, 160, 160)
        unitRect = QRectF(-50, 60, 110, 50)

        speedInt = self.speed
        s_SpeedInt = speedInt.__str__()[0:4] + "%"

        powerAngle = self.power * 270.0 / 100.0

        dummyPath = QPainterPath()
        dummyPath.moveTo(x1)
        dummyPath.arcMoveTo(intRect, 90 - powerAngle)
        powerPath = QPainterPath()
        powerPath.moveTo(x1)
        powerPath.lineTo(x2)
        powerPath.arcTo(extRect, 90, -1 * powerAngle)
        powerPath.lineTo(dummyPath.currentPosition())
        powerPath.arcTo(intRect, 90 - powerAngle, powerAngle)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)
        side = min(self.width(), self.height())
        painter.scale(side / 200.0, side / 200.0)

        painter.save()
        painter.rotate(-135)

        if self.displayPowerPath:
            externalPath = QPainterPath()
            externalPath.moveTo(x1)
            externalPath.lineTo(x2)
            externalPath.arcTo(extRect, 90, -270)
            externalPath.lineTo(x4)
            externalPath.arcTo(intRect, 180, 270)

            painter.setPen(self.powerPathColor)
            painter.drawPath(externalPath)

        painter.setBrush(self.powerGradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(powerPath)
        painter.restore()
        painter.save()

        painter.translate(QPointF(0, -50))

        painter.setPen(self.unitTextColor)
        fontFamily = self.font().family()
        unitFont = QFont(fontFamily, 9)
        unitFont.setFamily("Arial")
        painter.setFont(unitFont)
        painter.drawText(unitRect, Qt.AlignmentFlag.AlignCenter, "{}".format(self.unit))

        painter.restore()

        painter.setPen(self.unitTextColor)
        fontFamily = self.font().family()
        unitFont = QFont(fontFamily, 12)
        painter.setFont(unitFont)
        painter.drawText(unitRect, Qt.AlignmentFlag.AlignCenter, "{}".format(self.title))

        # 调整数字的字体，大小，位置
        speedFont = QFont(fontFamily, 22)
        speedFont.setFamily("Arial")
        fm1 = QFontMetrics(speedFont)
        speedWidth = fm1.maxWidth()
        leftPos = -1 * speedWidth + 70
        topPos = 10
        painter.setPen(self.speedTextColor)
        painter.setFont(speedFont)
        painter.drawText(leftPos, topPos, s_SpeedInt)
        # del painter
