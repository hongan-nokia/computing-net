# -*- coding: utf-8 -*-
"""
@Time: 5/17/2024 11:47 AM
@Author: Honggang Yuan
@Email: honggang.yuan@nokia-sbell.com
Description: 
"""
import sys
from multiprocessing import Pipe, Queue

from PyQt5.QtChart import QChart, QSplineSeries, QDateTimeAxis, QValueAxis
from PyQt5.QtCore import Qt, QTimer, QDateTime, QPointF
from PyQt5.QtGui import QPen, QColor, QBrush, QFont


class HistoryWindow(QChart):

    def __init__(self, parent=None, cpu_q=None, delay_q=None):
        super(HistoryWindow, self).__init__()
        self.m_count = 5
        # 设置隐藏图例
        # self.legend().hide()
        # 设置画笔
        self.cpu_q = cpu_q
        # self.delay_q = delay_q
        self.cpu = QSplineSeries(self)
        self.cpu.setName("CPU")
        # self.delay = QSplineSeries(self)
        # self.delay.setName("Delay")

        self.setBackgroundBrush(Qt.white)

        self.cpu.setPen(
            QPen(QColor(38, 2, 190), 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        # self.delay.setPen(
        #     QPen(QColor(249, 132, 19), 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))

        self.addSeries(self.cpu)
        # self.addSeries(self.delay)
        # x轴
        self.m_axisX = QDateTimeAxis(self)
        self.m_axisX.setTickCount(self.m_count + 20)  # 设置刻度数量
        self.m_axisX.setFormat('mm')  # 设置时间显示格式
        now = QDateTime.currentDateTime()  # 前10秒到现在
        self.m_axisX.setRange(now.addSecs(-self.m_count - 20), now)
        self.addAxis(self.m_axisX, Qt.AlignBottom)
        self.m_axisX.setVisible(False)

        # 左边y轴
        self.m_axisY_left = QValueAxis(self)
        self.m_axisY_left.setLabelFormat('%d%')  # 设置文本格式为百分比
        self.m_axisY_left.setTickCount(self.m_count + 1)
        self.m_axisY_left.setRange(0, 40)  # 设置范围
        self.addAxis(self.m_axisY_left, Qt.AlignLeft)
        self.m_axisY_left.setLabelsColor(QColor(38, 2, 190))

        # 右边y轴
        # self.m_axisY_right = QValueAxis(self)
        # self.m_axisY_right.setLabelFormat('%dms')  # 设置文本格式为毫秒
        # self.m_axisY_right.setTickCount(self.m_count + 1)
        # self.m_axisY_right.setRange(0, 40)  # 设置范围
        # self.addAxis(self.m_axisY_right, Qt.AlignRight)
        # self.m_axisY_right.setLabelsColor(QColor(249, 132, 19))

        font = QFont("Arial", 10)
        font.setBold(True)
        self.m_axisX.setLabelsFont(font)
        # self.m_axisY_right.setLabelsFont(font)
        self.m_axisY_left.setLabelsFont(font)

        # 将CPU和延迟数据的曲线与左右两个y轴关联
        self.cpu.attachAxis(self.m_axisX)
        self.cpu.attachAxis(self.m_axisY_left)  # 左边y轴

        # self.delay.attachAxis(self.m_axisX)
        # self.delay.attachAxis(self.m_axisY_right)  # 右边y轴

        self.cpu.append(
            [QPointF(now.addSecs(-i).toMSecsSinceEpoch(), 0) for i in range(self.m_count + 20, -1, -1)])
        # self.delay.append(
        #     [QPointF(now.addSecs(-i).toMSecsSinceEpoch(), 0) for i in range(self.m_count + 20, -1, -1)])

        # 定时器获取数据
        self.m_timer = QTimer()
        self.m_timer.timeout.connect(self.update_data_home)
        # self.m_timer.timeout.connect(self.update_data_office)
        self.m_timer.start(5500)

    def update_data_home(self):
        h_cpu = 0
        max = 10
        if not self.cpu_q.empty():
            h_cpu = self.cpu_q.get()
        now = QDateTime.currentDateTime()  # 前10秒到现在
        self.m_axisX.setRange(now.addSecs(-self.m_count - 50), now)  # 重新调整x轴的时间范围
        # 获取原来的所有点,去掉第一个并追加新的一个
        points = self.cpu.pointsVector()
        if len(points) > 20:
            points.pop(0)
        # print(f"h_cpu is: {h_cpu}")
        points.append(QPointF(now.toMSecsSinceEpoch(), h_cpu))

        max_y = 0
        last_six_elements = points[-12:]
        for point in last_six_elements:
            y = point.y()
            if y > max_y:
                max_y = y
        if max_y > 90:
            max_y = 90
        self.m_axisY_left.setRange(0, max_y + 10)

        # 替换法速度更快
        self.cpu.replace(points)

    def update_data_office(self):
        h_cpu = 0
        max = 10
        if not self.delay_q.empty():
            h_cpu = self.delay_q.get()
        now = QDateTime.currentDateTime()  # 前10秒到现在
        self.m_axisX.setRange(now.addSecs(-self.m_count - 50), now)  # 重新调整x轴的时间范围
        # 获取原来的所有点,去掉第一个并追加新的一个
        points = self.delay.pointsVector()
        if len(points) > 20:
            points.pop(0)
        # print(f"h_cpu is: {h_cpu}")
        points.append(QPointF(now.toMSecsSinceEpoch(), h_cpu))

        max_y = 0
        # 图中只显示最新6个数据，所以只遍历最后6个
        last_six_elements = points[-12:]
        for point in last_six_elements:
            y = point.y()
            if y > max_y:
                max_y = y
        self.m_axisY_right.setRange(0, max_y + 10)

        # 替换法速度更快
        self.delay.replace(points)
