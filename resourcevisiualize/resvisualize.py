# -*- coding: utf-8 -*-
"""
@Time: 5/17/2024 11:47 AM
@Author: Honggang Yuan
@Email: honggang.yuan@nokia-sbell.com
Description: 
"""

import random
from multiprocessing import Queue
from time import sleep
from typing import List, Dict

import requests
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QTimer
from PyQt5.QtChart import QChartView
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QGroupBox, QPushButton

from nodemodels.cfndemomanager import CfnDemoManager
from resourcevisiualize.resourcehistory import HistoryWindow
from resourcevisiualize.speedmeter import SpeedMeter
from utils.repeatimer import repeatTimer
from utils.reversequeue import reverseQueue

from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from datetime import datetime


def net_formatter(net_tx_bytes, net_rx_bytes):
    if (net_tx_bytes / 1000) < 1:
        tx_tag = f"{round(net_tx_bytes, 1)} bps"
    elif 1 < (net_tx_bytes / 1000) < 1000:
        tx_tag = f"{round(net_tx_bytes / 1000, 1)} kbps"
    elif 1 < (net_tx_bytes / 1000000):
        tx_tag = f"{round(net_tx_bytes / 1000000, 1)} Mbps"
    else:
        tx_tag = f"{round(net_tx_bytes / 1000000000, 1)} Gbps"

    if (net_rx_bytes / 1000) < 1:
        rx_tag = f"{round(net_rx_bytes, 1)} bps"
    elif 1 < (net_rx_bytes / 1000) < 1000:
        rx_tag = f"{round(net_rx_bytes / 1000, 1)} kbps"
    elif 1 < (net_rx_bytes / 1000000):
        rx_tag = f"{round(net_rx_bytes / 1000000, 1)} Mbps"
    else:
        rx_tag = f"{round(net_rx_bytes / 1000000000, 1)} Gbps"
    return tx_tag, rx_tag


def disk_formatter(disk_read_bytes, disk_write_bytes):
    if (disk_read_bytes / 1000) < 1:
        r_tag = f"{round(disk_read_bytes, 1)} B/s"
    elif 1 < (disk_read_bytes / 1000) < 1000:
        r_tag = f"{round(disk_read_bytes / 1000, 1)} KB/s"
    elif 1 < (disk_read_bytes / 1000000) < 1000:
        r_tag = f"{round(disk_read_bytes / 1000000, 1)} MB/s"
    else:
        r_tag = f"{round(disk_read_bytes / 1000000000, 1)} GB/s"

    if (disk_write_bytes / 1000) < 1:
        w_tag = f"{round(disk_write_bytes, 1)} B/s"
    elif 1 < (disk_write_bytes / 1000) < 1000:
        w_tag = f"{round(disk_write_bytes / 1000, 1)} KB/s"
    elif 1 < (disk_write_bytes / 1000000) < 1000:
        w_tag = f"{round(disk_write_bytes / 1000000, 1)} MB/s"
    else:
        w_tag = f"{round(disk_write_bytes / 1000000000, 1)} GB/s"
    return r_tag, w_tag


class MplCanvas(FigureCanvas):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig, self.ax = plt.subplots(figsize=(width, height), dpi=dpi)
        super(MplCanvas, self).__init__(fig)


class RateUpdater(QObject):
    rate_updated = pyqtSignal(float)

    def __init__(self):
        super().__init__()

    def update_rate(self, rate):
        self.rate_updated.emit(rate)


class DataVisualizationWindow(QWidget):
    def __init__(self, cpu_q, delay_q, windowTitle="History"):
        super().__init__()
        self.cpu_queue = cpu_q
        self.delay_queue = delay_q
        self.setWindowTitle(windowTitle)
        self.setGeometry(100, 100, 600, 450)
        self._initView()

    def _initView(self):
        # self.setWindowFlag(Qt.FramelessWindowHint)
        self.view = QtWidgets.QGraphicsView(parent=self)
        self.view.setCacheMode(QtWidgets.QGraphicsView.CacheBackground)
        self.view.setScene(QtWidgets.QGraphicsScene())

        self.drawRateAndTime()

    def drawRateAndTime(self):
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)

        self.plot_widget = QWidget()  # 创建一个包装了 MplCanvas 的 QWidget
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.plot_widget.setLayout(layout)

        # self.canvas.setMinimumSize(400, 300)  # 设置最小尺寸
        # self.canvas.setMaximumSize(800, 600)  # 设置最大尺寸

        self.y_data = [0]
        self.x_data = [0]  # 使用索引作为横坐标

        # main_layout = QVBoxLayout()
        # main_layout.addWidget(self.plot_widget)

        self.plot_widget.setGeometry(80, 80, 600, 450)

        self.view.scene().addWidget(self.plot_widget)

        self.rate_updater = RateUpdater()
        self.rate_updater.rate_updated.connect(lambda rate: self.update_plot(rate))

        # self.timer = QTimer()
        # self.timer.setInterval(1000)  # 更新间隔为1000毫秒，即1秒
        # self.timer.timeout.connect(self.update_plot)
        # self.timer.start()

    # def simulate_rate_update(self):
    #     # 生成0到100之间的随机速率值
    #     simulated_rate = random.uniform(0, 100)
    #     self.rate_updater.update_rate(simulated_rate)

    def update_plot(self):
        current_cpu = self.cpu_queue.get()

        self.y_data.append(current_cpu)
        self.x_data.append(len(self.x_data))  # 添加索引

        self.canvas.ax.clear()
        self.canvas.ax.plot(self.x_data, self.y_data, label="Rate")

        self.canvas.ax.set_xlabel('Time/s')
        self.canvas.ax.set_ylabel('Rate/%')
        self.canvas.ax.legend()
        self.canvas.ax.grid(True)

        self.canvas.draw()


class data_visualize(QWidget):

    updateHeatMap = pyqtSignal(list)

    def __init__(self, parent, demo_manager, res_queue_dict):
        super().__init__()
        self.cfn_manager = demo_manager
        self._initResourceUri()
        # self.setWindowFlag(Qt.FramelessWindowHint)
        self.updateFlag = False
        self.layout = QtWidgets.QHBoxLayout(self)
        self.setParent(parent)
        self.groupBox = QGroupBox(self)
        self.groupBox.setStyleSheet("color: rgb(255, 255, 255);\n"
                                    "border: none;\n"
                                    "border-radius: 3px;\n"
                                    "background-color: #001135;")
        self.node_res_monitor_queue_dict = res_queue_dict
        geo = {
            'top': 0,
            'left': 0,
            'width': 1920,
            'height': 1060}
        self.setGeometry(geo['left'], geo['top'], geo['width'], geo['height'])

        self.node1_info = {
            "cpu": 0,
            "mem": 0,
            "disk": [0, 0],
            "net": [0, 0]
        }

        self.node2_info = {
            "cpu": 0,
            "mem": 0,
            "disk": [0, 0],
            "net": [0, 0]
        }

        self.node3_info = {
            "cpu": 0,
            "mem": 0,
            "disk": [0, 0],
            "net": [0, 0]
        }

        self.node4_info = {
            "cpu": 0,
            "mem": 0,
            "disk": [0, 0],
            "net": [0, 0]
        }

        self.node1_globe_info = [[0, 0], [0, 0]]
        self.node2_globe_info = [[0, 0], [0, 0]]
        self.node3_globe_info = [[0, 0], [0, 0]]
        self.node4_globe_info = [[0, 0], [0, 0]]

        """
        包含3个node展示页面的主框架，布局为Horizontal，3个node水平展示
        """
        self.horizontalLayout = QtWidgets.QVBoxLayout(self.groupBox)
        self.horizontalLayout.setObjectName("horizontalLayout")

        self.main_title = QtWidgets.QLabel("实时感知的算网资源")
        self.main_title_font = QtGui.QFont("Arial", 30, QtGui.QFont.Bold)
        self.main_title.setFont(self.main_title_font)
        self.main_title.setStyleSheet("color:rgb(146,208,80)\n;"
                                      "border: none")
        self.main_title.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignCenter)
        self.horizontalLayout.addWidget(self.main_title)

        self.status_monitor_layout = QtWidgets.QHBoxLayout(self.groupBox)
        self.status_monitor_layout.setSpacing(12)
        self.status_monitor_layout.setObjectName("status_monitor")

        """
        第一个node窗口，布局Vertical，包含5个部件
        窗口label、资源窗口、网络占用码表、Disk、File
        """
        self.node1 = QtWidgets.QGroupBox(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node1.sizePolicy().hasHeightForWidth())
        self.node1.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(19)
        font.setBold(True)
        font.setWeight(75)
        self.node1.setFont(font)
        self.node1.setStyleSheet("color: rgb(255, 255, 255);\n"
                                 "border: 4px solid #2F528F;\n"
                                 "border-radius: 10px;")
        self.node1.setTitle("")
        self.node1.setObjectName("node1")
        self.node1_verticalLayout = QtWidgets.QVBoxLayout(self.node1)
        self.node1_verticalLayout.setContentsMargins(-1, 8, -1, 4)
        self.node1_verticalLayout.setObjectName("node1_verticalLayout")

        # 第一个部件，展示node名称，之后切换时需要动态变动
        self.node1_label = QtWidgets.QLabel(self.node1)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(20)
        font.setBold(True)
        font.setWeight(75)
        self.node1_label.setFont(font)
        self.node1_label.setStyleSheet("border: none;")
        self.node1_label.setObjectName("label")
        self.node1_verticalLayout.addWidget(self.node1_label)

        self.node1_wl_label = QtWidgets.QLabel(self.node1)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(20)
        font.setBold(True)
        font.setWeight(75)
        self.node1_wl_label.setFont(font)
        self.node1_wl_label.setStyleSheet("border: none;")
        self.node1_wl_label.setObjectName("net_label_1")
        self.node1_verticalLayout.addWidget(self.node1_wl_label)

        self.node1_net = QtWidgets.QGroupBox(self.node1)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node1_net.sizePolicy().hasHeightForWidth())
        self.node1_net.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(19)
        font.setBold(True)
        font.setWeight(75)
        self.node1_net.setFont(font)
        self.node1_net.setStyleSheet("color: rgb(255, 255, 255);border: none;")
        self.node1_net.setObjectName("net_1")
        self.node1_net.setMinimumSize(250, 250)
        self.node1_verticalLayout.addWidget(self.node1_net)

        # 第三个部件，展示资源占用，包括CPU、内存、网络延迟
        self.node1_resource = QtWidgets.QGroupBox(self.node1)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node1_resource.sizePolicy().hasHeightForWidth())
        self.node1_resource.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(19)
        self.node1_resource.setFont(font)
        self.node1_resource.setStyleSheet("color: rgb(255, 255, 255);\n"
                                          "border: none;")
        self.node1_resource.setTitle("")
        self.node1_resource.setObjectName("resource_1")
        self.node1_res_gridLayout = QtWidgets.QGridLayout(self.node1_resource)
        self.node1_res_gridLayout.setObjectName("node1_res_gridLayout")

        # cpu
        self.node1_cpu_label = QtWidgets.QLabel(self.node1_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node1_cpu_label.sizePolicy().hasHeightForWidth())
        self.node1_cpu_label.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(18)
        self.node1_cpu_label.setFont(font)
        self.node1_cpu_label.setStyleSheet("color: rgb(255, 255, 255);")
        self.node1_cpu_label.setObjectName("cpu_1")
        self.node1_res_gridLayout.addWidget(self.node1_cpu_label, 0, 0, 1, 1)

        # cpu bar
        self.node1_cpu_bar = QtWidgets.QProgressBar(self.node1_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node1_cpu_bar.sizePolicy().hasHeightForWidth())
        self.node1_cpu_bar.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        font.setKerning(True)
        self.node1_cpu_bar.setFont(font)
        self.node1_cpu_bar.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.node1_cpu_bar.setAutoFillBackground(False)
        self.node1_cpu_bar.setStyleSheet("color: rgb(255, 255, 255);")
        self.node1_cpu_bar.setProperty("value", 0)
        self.node1_cpu_bar.setTextVisible(False)
        self.node1_cpu_bar.setFixedHeight(28)
        self.node1_cpu_bar.setObjectName("cpu_bar_1")
        self.node1_res_gridLayout.addWidget(self.node1_cpu_bar, 0, 1, 1, 2)

        # cpu num
        self.node1_cpu_num = QtWidgets.QLabel(self.node1_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node1_cpu_num.sizePolicy().hasHeightForWidth())
        self.node1_cpu_num.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node1_cpu_num.setFont(font)
        self.node1_cpu_num.setStyleSheet("color: rgb(255, 255, 255);")
        self.node1_cpu_num.setObjectName("cpu_num_1")
        self.node1_res_gridLayout.addWidget(self.node1_cpu_num, 0, 4, 1, 1)

        # mem
        self.node1_mem_label = QtWidgets.QLabel(self.node1_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node1_mem_label.sizePolicy().hasHeightForWidth())
        self.node1_mem_label.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(18)
        self.node1_mem_label.setFont(font)
        self.node1_mem_label.setStyleSheet("color: rgb(255, 255, 255);")
        self.node1_mem_label.setObjectName("mem_1")
        self.node1_res_gridLayout.addWidget(self.node1_mem_label, 1, 0, 1, 1)

        # mem bar
        self.node1_mem_bar = QtWidgets.QProgressBar(self.node1_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node1_mem_bar.sizePolicy().hasHeightForWidth())
        self.node1_mem_bar.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        self.node1_mem_bar.setFont(font)
        self.node1_mem_bar.setStyleSheet("color: rgb(255, 255, 255);")
        self.node1_mem_bar.setProperty("value", 0)
        self.node1_mem_bar.setTextVisible(False)
        self.node1_mem_bar.setFixedHeight(28)
        self.node1_mem_bar.setObjectName("mem_bar_1")
        self.node1_res_gridLayout.addWidget(self.node1_mem_bar, 1, 1, 1, 2)

        # mem num
        self.node1_mem_num = QtWidgets.QLabel(self.node1_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node1_mem_num.sizePolicy().hasHeightForWidth())
        self.node1_mem_num.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node1_mem_num.setFont(font)
        self.node1_mem_num.setStyleSheet("color: rgb(255, 255, 255);")
        self.node1_mem_num.setObjectName("mem_usage_1")
        self.node1_res_gridLayout.addWidget(self.node1_mem_num, 1, 4, 1, 1)

        # Disk
        self.node1_net_label = QtWidgets.QLabel(self.node1_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node1_net_label.sizePolicy().hasHeightForWidth())
        self.node1_net_label.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(18)
        self.node1_net_label.setFont(font)
        self.node1_net_label.setStyleSheet("color: rgb(255, 255, 255);")
        self.node1_net_label.setObjectName("node1_net_label")
        self.node1_res_gridLayout.addWidget(self.node1_net_label, 2, 0, 1, 1)

        # disk_read
        self.node1_net_read_label = QtWidgets.QLabel(self.node1_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node1_net_read_label.sizePolicy().hasHeightForWidth())
        self.node1_net_read_label.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node1_net_read_label.setFont(font)
        self.node1_net_read_label.setStyleSheet("color: rgb(255, 255, 255);")
        self.node1_net_read_label.setObjectName("node1_net_read_label")
        self.node1_res_gridLayout.addWidget(self.node1_net_read_label, 2, 2, 1, 1)

        # disk_write
        self.node1_net_read_v = QtWidgets.QLabel(self.node1_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node1_net_read_v.sizePolicy().hasHeightForWidth())
        self.node1_net_read_v.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node1_net_read_v.setFont(font)
        self.node1_net_read_v.setStyleSheet("color: rgb(255, 255, 255);")
        self.node1_net_read_v.setObjectName("node1_net_read_v")
        self.node1_res_gridLayout.addWidget(self.node1_net_read_v, 2, 4, 1, 1)

        self.node1_net_name = QtWidgets.QLabel(self.node1_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node1_net_name.sizePolicy().hasHeightForWidth())
        self.node1_net_name.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node1_net_name.setFont(font)
        self.node1_net_name.setStyleSheet("color: rgb(0, 17, 53);")
        self.node1_net_name.setObjectName("node1_net_name")
        self.node1_res_gridLayout.addWidget(self.node1_net_name, 3, 0, 1, 1)

        # disk_read
        self.node1_net_write_label = QtWidgets.QLabel(self.node1_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node1_net_write_label.sizePolicy().hasHeightForWidth())
        self.node1_net_write_label.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node1_net_write_label.setFont(font)
        self.node1_net_write_label.setStyleSheet("color: rgb(255, 255, 255);")
        self.node1_net_write_label.setObjectName("node1_net_write_label")
        self.node1_res_gridLayout.addWidget(self.node1_net_write_label, 3, 2, 1, 1)

        # disk_write
        self.node1_net_write_v = QtWidgets.QLabel(self.node1_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node1_net_write_v.sizePolicy().hasHeightForWidth())
        self.node1_net_write_v.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node1_net_write_v.setFont(font)
        self.node1_net_write_v.setStyleSheet("color: rgb(255, 255, 255);")
        self.node1_net_write_v.setObjectName("node1_net_write_v")
        self.node1_res_gridLayout.addWidget(self.node1_net_write_v, 3, 4, 1, 1)
        #################################
        # Disk
        self.node1_disk_label = QtWidgets.QLabel(self.node1_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node1_disk_label.sizePolicy().hasHeightForWidth())
        self.node1_disk_label.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(18)
        self.node1_disk_label.setFont(font)
        self.node1_disk_label.setStyleSheet("color: rgb(255, 255, 255);")
        self.node1_disk_label.setObjectName("delay_1")
        self.node1_res_gridLayout.addWidget(self.node1_disk_label, 4, 0, 1, 1)

        # disk_read
        self.node1_disk_read_label = QtWidgets.QLabel(self.node1_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node1_disk_read_label.sizePolicy().hasHeightForWidth())
        self.node1_disk_read_label.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node1_disk_read_label.setFont(font)
        self.node1_disk_read_label.setStyleSheet("color: rgb(255, 255, 255);")
        self.node1_disk_read_label.setObjectName("node1_disk_read_label")
        self.node1_res_gridLayout.addWidget(self.node1_disk_read_label, 4, 2, 1, 1)

        # disk_write
        self.node1_disk_read_v = QtWidgets.QLabel(self.node1_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node1_disk_read_v.sizePolicy().hasHeightForWidth())
        self.node1_disk_read_v.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node1_disk_read_v.setFont(font)
        self.node1_disk_read_v.setStyleSheet("color: rgb(255, 255, 255);")
        self.node1_disk_read_v.setObjectName("node1_disk_read_v")
        self.node1_res_gridLayout.addWidget(self.node1_disk_read_v, 4, 4, 1, 1)

        self.node1_disk_name = QtWidgets.QLabel(self.node1_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node1_disk_name.sizePolicy().hasHeightForWidth())
        self.node1_disk_name.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node1_disk_name.setFont(font)
        self.node1_disk_name.setStyleSheet("color: rgb(255, 255, 255);")
        self.node1_disk_name.setObjectName("node1_disk_name")
        self.node1_res_gridLayout.addWidget(self.node1_disk_name, 5, 0, 1, 2)

        # disk_read
        self.node1_disk_write_label = QtWidgets.QLabel(self.node1_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node1_disk_write_label.sizePolicy().hasHeightForWidth())
        self.node1_disk_write_label.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node1_disk_write_label.setFont(font)
        self.node1_disk_write_label.setStyleSheet("color: rgb(255, 255, 255);")
        self.node1_disk_write_label.setObjectName("node1_disk_write_label")
        self.node1_res_gridLayout.addWidget(self.node1_disk_write_label, 5, 2, 1, 1)

        # disk_write
        self.node1_disk_write_v = QtWidgets.QLabel(self.node1_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node1_disk_write_v.sizePolicy().hasHeightForWidth())
        self.node1_disk_write_v.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node1_disk_write_v.setFont(font)
        self.node1_disk_write_v.setStyleSheet("color: rgb(255, 255, 255);")
        self.node1_disk_write_v.setObjectName("node1_disk_write_v")
        self.node1_res_gridLayout.addWidget(self.node1_disk_write_v, 5, 4, 1, 1)

        self.node1_res_gridLayout.setColumnStretch(0, 2)
        self.node1_res_gridLayout.setColumnStretch(1, 1)
        self.node1_res_gridLayout.setColumnStretch(2, 0)
        self.node1_res_gridLayout.setColumnStretch(3, 1)

        self.node1_verticalLayout.addWidget(self.node1_resource)
        self.node1_verticalLayout.setStretch(0, 1)
        self.node1_verticalLayout.setStretch(1, 1)
        self.node1_verticalLayout.setStretch(2, 4)
        self.node1_verticalLayout.setStretch(3, 4)
        self.status_monitor_layout.addWidget(self.node1)

        ################################################################################################################################################
        # -------------------------------------------------------------------------------------------------------------------------------------------- #
        ################################################################################################################################################
        self.node2 = QtWidgets.QGroupBox(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node2.sizePolicy().hasHeightForWidth())
        self.node2.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(19)
        font.setBold(True)
        font.setWeight(75)
        self.node2.setFont(font)
        self.node2.setStyleSheet("color: rgb(255, 255, 255);\n"
                                 "border: 4px solid #2F528F;\n"
                                 "border-radius: 10px;")
        self.node2.setTitle("")
        self.node2.setObjectName("node2")
        self.node2_verticalLayout = QtWidgets.QVBoxLayout(self.node2)
        self.node2_verticalLayout.setContentsMargins(-1, 8, -1, 4)
        self.node2_verticalLayout.setObjectName("node2_verticalLayout")

        # 第一个部件，展示node名称，之后切换时需要动态变动
        self.node2_label = QtWidgets.QLabel(self.node2)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(20)
        font.setBold(True)
        font.setWeight(75)
        self.node2_label.setFont(font)
        self.node2_label.setStyleSheet("border: none;")
        self.node2_label.setObjectName("node2_label")
        self.node2_verticalLayout.addWidget(self.node2_label)

        self.node2_wl_label = QtWidgets.QLabel(self.node2)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(20)
        font.setBold(True)
        font.setWeight(75)
        self.node2_wl_label.setFont(font)
        self.node2_wl_label.setStyleSheet("border: none;")
        self.node2_wl_label.setObjectName("node2_wl_label")
        self.node2_verticalLayout.addWidget(self.node2_wl_label)

        self.node2_net = QtWidgets.QGroupBox(self.node2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node2_net.sizePolicy().hasHeightForWidth())
        self.node2_net.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(19)
        font.setBold(True)
        font.setWeight(75)
        self.node2_net.setFont(font)
        self.node2_net.setStyleSheet("color: rgb(255, 255, 255);border: none;")
        self.node2_net.setObjectName("node2_net")
        self.node2_net.setMinimumSize(250, 250)
        self.node2_verticalLayout.addWidget(self.node2_net)

        # 第三个部件，展示资源占用，包括CPU、内存、网络延迟
        self.node2_resource = QtWidgets.QGroupBox(self.node2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node2_resource.sizePolicy().hasHeightForWidth())
        self.node2_resource.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(19)
        self.node2_resource.setFont(font)
        self.node2_resource.setStyleSheet("color: rgb(255, 255, 255);\n"
                                          "border: none;")
        self.node2_resource.setTitle("")
        self.node2_resource.setObjectName("node2_resource")
        self.node2_res_gridLayout = QtWidgets.QGridLayout(self.node2_resource)
        self.node2_res_gridLayout.setObjectName("node2_res_gridLayout")

        # node2
        # cpu
        self.node2_cpu_label = QtWidgets.QLabel(self.node2_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node2_cpu_label.sizePolicy().hasHeightForWidth())
        self.node2_cpu_label.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(18)
        self.node2_cpu_label.setFont(font)
        self.node2_cpu_label.setStyleSheet("color: rgb(255, 255, 255);")
        self.node2_cpu_label.setObjectName("node2_cpu_label")
        self.node2_res_gridLayout.addWidget(self.node2_cpu_label, 0, 0, 1, 1)

        # cpu bar
        self.node2_cpu_bar = QtWidgets.QProgressBar(self.node2_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node2_cpu_bar.sizePolicy().hasHeightForWidth())
        self.node2_cpu_bar.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        font.setKerning(True)
        self.node2_cpu_bar.setFont(font)
        self.node2_cpu_bar.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.node2_cpu_bar.setAutoFillBackground(False)
        self.node2_cpu_bar.setStyleSheet("color: rgb(255, 255, 255);")
        self.node2_cpu_bar.setProperty("value", 0)
        self.node2_cpu_bar.setTextVisible(False)
        self.node2_cpu_bar.setFixedHeight(28)
        self.node2_cpu_bar.setObjectName("cpu_bar_1")
        self.node2_res_gridLayout.addWidget(self.node2_cpu_bar, 0, 1, 1, 2)

        # cpu num
        self.node2_cpu_num = QtWidgets.QLabel(self.node2_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node2_cpu_num.sizePolicy().hasHeightForWidth())
        self.node2_cpu_num.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node2_cpu_num.setFont(font)
        self.node2_cpu_num.setStyleSheet("color: rgb(255, 255, 255);")
        self.node2_cpu_num.setObjectName("cpu_num_1")
        self.node2_res_gridLayout.addWidget(self.node2_cpu_num, 0, 4, 1, 1)

        # mem
        self.node2_mem_label = QtWidgets.QLabel(self.node2_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node2_mem_label.sizePolicy().hasHeightForWidth())
        self.node2_mem_label.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(18)
        self.node2_mem_label.setFont(font)
        self.node2_mem_label.setStyleSheet("color: rgb(255, 255, 255);")
        self.node2_mem_label.setObjectName("mem_1")
        self.node2_res_gridLayout.addWidget(self.node2_mem_label, 1, 0, 1, 1)

        # mem bar
        self.node2_mem_bar = QtWidgets.QProgressBar(self.node2_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node2_mem_bar.sizePolicy().hasHeightForWidth())
        self.node2_mem_bar.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        self.node2_mem_bar.setFont(font)
        self.node2_mem_bar.setStyleSheet("color: rgb(255, 255, 255);")
        self.node2_mem_bar.setProperty("value", 0)
        self.node2_mem_bar.setTextVisible(False)
        self.node2_mem_bar.setFixedHeight(28)
        self.node2_mem_bar.setObjectName("mem_bar_1")
        self.node2_res_gridLayout.addWidget(self.node2_mem_bar, 1, 1, 1, 2)

        # mem num
        self.node2_mem_num = QtWidgets.QLabel(self.node2_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node2_mem_num.sizePolicy().hasHeightForWidth())
        self.node2_mem_num.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node2_mem_num.setFont(font)
        self.node2_mem_num.setStyleSheet("color: rgb(255, 255, 255);")
        self.node2_mem_num.setObjectName("node2_mem_num")
        self.node2_res_gridLayout.addWidget(self.node2_mem_num, 1, 4, 1, 1)

        # Disk
        self.node2_net_label = QtWidgets.QLabel(self.node2_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node2_net_label.sizePolicy().hasHeightForWidth())
        self.node2_net_label.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(18)
        self.node2_net_label.setFont(font)
        self.node2_net_label.setStyleSheet("color: rgb(255, 255, 255);")
        self.node2_net_label.setObjectName("node1_net_label")
        self.node2_res_gridLayout.addWidget(self.node2_net_label, 2, 0, 1, 1)

        # disk_read
        self.node2_net_read_label = QtWidgets.QLabel(self.node2_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node2_net_read_label.sizePolicy().hasHeightForWidth())
        self.node2_net_read_label.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node2_net_read_label.setFont(font)
        self.node2_net_read_label.setStyleSheet("color: rgb(255, 255, 255);")
        self.node2_net_read_label.setObjectName("node2_net_read_label")
        self.node2_res_gridLayout.addWidget(self.node2_net_read_label, 2, 2, 1, 1)

        # disk_write
        self.node2_net_read_v = QtWidgets.QLabel(self.node2_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node2_net_read_v.sizePolicy().hasHeightForWidth())
        self.node2_net_read_v.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node2_net_read_v.setFont(font)
        self.node2_net_read_v.setStyleSheet("color: rgb(255, 255, 255);")
        self.node2_net_read_v.setObjectName("node1_net_read_v")
        self.node2_res_gridLayout.addWidget(self.node2_net_read_v, 2, 4, 1, 1)

        self.node2_net_name = QtWidgets.QLabel(self.node2_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node2_net_name.sizePolicy().hasHeightForWidth())
        self.node2_net_name.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node2_net_name.setFont(font)
        self.node2_net_name.setStyleSheet("color: rgb(0, 17, 53);")
        self.node2_net_name.setObjectName("node2_net_name")
        self.node2_res_gridLayout.addWidget(self.node2_net_name, 3, 0, 1, 1)

        # disk_read
        self.node2_net_write_label = QtWidgets.QLabel(self.node2_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node2_net_write_label.sizePolicy().hasHeightForWidth())
        self.node2_net_write_label.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node2_net_write_label.setFont(font)
        self.node2_net_write_label.setStyleSheet("color: rgb(255, 255, 255);")
        self.node2_net_write_label.setObjectName("node2_net_write_label")
        self.node2_res_gridLayout.addWidget(self.node2_net_write_label, 3, 2, 1, 1)

        # disk_write
        self.node2_net_write_v = QtWidgets.QLabel(self.node2_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node2_net_write_v.sizePolicy().hasHeightForWidth())
        self.node2_net_write_v.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node2_net_write_v.setFont(font)
        self.node2_net_write_v.setStyleSheet("color: rgb(255, 255, 255);")
        self.node2_net_write_v.setObjectName("node1_net_write_v")
        self.node2_res_gridLayout.addWidget(self.node2_net_write_v, 3, 4, 1, 1)
        #################################
        # Disk
        self.node2_disk_label = QtWidgets.QLabel(self.node2_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node2_disk_label.sizePolicy().hasHeightForWidth())
        self.node2_disk_label.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(18)
        self.node2_disk_label.setFont(font)
        self.node2_disk_label.setStyleSheet("color: rgb(255, 255, 255);")
        self.node2_disk_label.setObjectName("delay_1")
        self.node2_res_gridLayout.addWidget(self.node2_disk_label, 4, 0, 1, 1)

        # disk_read
        self.node2_disk_read_label = QtWidgets.QLabel(self.node2_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node2_disk_read_label.sizePolicy().hasHeightForWidth())
        self.node2_disk_read_label.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node2_disk_read_label.setFont(font)
        self.node2_disk_read_label.setStyleSheet("color: rgb(255, 255, 255);")
        self.node2_disk_read_label.setObjectName("node1_disk_read_label")
        self.node2_res_gridLayout.addWidget(self.node2_disk_read_label, 4, 2, 1, 1)

        # disk_write
        self.node2_disk_read_v = QtWidgets.QLabel(self.node2_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node2_disk_read_v.sizePolicy().hasHeightForWidth())
        self.node2_disk_read_v.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node2_disk_read_v.setFont(font)
        self.node2_disk_read_v.setStyleSheet("color: rgb(255, 255, 255);")
        self.node2_disk_read_v.setObjectName("node1_disk_read_v")
        self.node2_res_gridLayout.addWidget(self.node2_disk_read_v, 4, 4, 1, 1)

        self.node2_disk_name = QtWidgets.QLabel(self.node2_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node2_disk_name.sizePolicy().hasHeightForWidth())
        self.node2_disk_name.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node2_disk_name.setFont(font)
        self.node2_disk_name.setStyleSheet("color: rgb(255, 255, 255);")
        self.node2_disk_name.setObjectName("node2_disk_name")
        self.node2_res_gridLayout.addWidget(self.node2_disk_name, 5, 0, 1, 2)

        # disk_read
        self.node2_disk_write_label = QtWidgets.QLabel(self.node2_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node2_disk_write_label.sizePolicy().hasHeightForWidth())
        self.node2_disk_write_label.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node2_disk_write_label.setFont(font)
        self.node2_disk_write_label.setStyleSheet("color: rgb(255, 255, 255);")
        self.node2_disk_write_label.setObjectName("node2_disk_write_label")
        self.node2_res_gridLayout.addWidget(self.node2_disk_write_label, 5, 2, 1, 1)

        # disk_write
        self.node2_disk_write_v = QtWidgets.QLabel(self.node2_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node2_disk_write_v.sizePolicy().hasHeightForWidth())
        self.node2_disk_write_v.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node2_disk_write_v.setFont(font)
        self.node2_disk_write_v.setStyleSheet("color: rgb(255, 255, 255);")
        self.node2_disk_write_v.setObjectName("node2_disk_write_v")
        self.node2_res_gridLayout.addWidget(self.node2_disk_write_v, 5, 4, 1, 1)

        self.node2_res_gridLayout.setColumnStretch(0, 2)
        self.node2_res_gridLayout.setColumnStretch(1, 1)
        self.node2_res_gridLayout.setColumnStretch(2, 0)
        self.node2_res_gridLayout.setColumnStretch(3, 1)

        self.node2_verticalLayout.addWidget(self.node2_resource)
        self.node2_verticalLayout.setStretch(0, 1)
        self.node2_verticalLayout.setStretch(1, 1)
        self.node2_verticalLayout.setStretch(2, 4)
        self.node2_verticalLayout.setStretch(3, 4)
        self.status_monitor_layout.addWidget(self.node2)

        ################################################################################################################################################
        # -------------------------------------------------------------------------------------------------------------------------------------------- #
        ################################################################################################################################################
        self.node3 = QtWidgets.QGroupBox(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node3.sizePolicy().hasHeightForWidth())
        self.node3.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(19)
        font.setBold(True)
        font.setWeight(75)
        self.node3.setFont(font)
        self.node3.setStyleSheet("color: rgb(255, 255, 255);\n"
                                 "border: 4px solid #2F528F;\n"
                                 "border-radius: 10px;")
        self.node3.setTitle("")
        self.node3.setObjectName("node3")
        self.node3_verticalLayout = QtWidgets.QVBoxLayout(self.node3)
        self.node3_verticalLayout.setContentsMargins(-1, 8, -1, 4)
        self.node3_verticalLayout.setObjectName("node3_verticalLayout")

        # 第一个部件，展示node名称，之后切换时需要动态变动
        self.node3_label = QtWidgets.QLabel(self.node3)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(20)
        font.setBold(True)
        font.setWeight(75)
        self.node3_label.setFont(font)
        self.node3_label.setStyleSheet("border: none;")
        self.node3_label.setObjectName("node3_label")
        self.node3_verticalLayout.addWidget(self.node3_label)

        self.node3_wl_label = QtWidgets.QLabel(self.node3)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(20)
        font.setBold(True)
        font.setWeight(75)
        self.node3_wl_label.setFont(font)
        self.node3_wl_label.setStyleSheet("border: none;")
        self.node3_wl_label.setObjectName("node3_wl_label")
        self.node3_verticalLayout.addWidget(self.node3_wl_label)

        self.node3_net = QtWidgets.QGroupBox(self.node3)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node3_net.sizePolicy().hasHeightForWidth())
        self.node3_net.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(19)
        font.setBold(True)
        font.setWeight(75)
        self.node3_net.setFont(font)
        self.node3_net.setStyleSheet("color: rgb(255, 255, 255);border: none;")
        self.node3_net.setObjectName("node3_net")
        self.node3_net.setMinimumSize(250, 250)
        self.node3_verticalLayout.addWidget(self.node3_net)

        # 第三个部件，展示资源占用，包括CPU、内存、网络延迟
        self.node3_resource = QtWidgets.QGroupBox(self.node3)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node3_resource.sizePolicy().hasHeightForWidth())
        self.node3_resource.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(19)
        self.node3_resource.setFont(font)
        self.node3_resource.setStyleSheet("color: rgb(255, 255, 255);\n"
                                          "border: none;")
        self.node3_resource.setTitle("")
        self.node3_resource.setObjectName("node3_resource")
        self.node3_res_gridLayout = QtWidgets.QGridLayout(self.node3_resource)
        self.node3_res_gridLayout.setObjectName("node3_res_gridLayout")

        # node2
        # cpu
        self.node3_cpu_label = QtWidgets.QLabel(self.node3_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node3_cpu_label.sizePolicy().hasHeightForWidth())
        self.node3_cpu_label.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(18)
        self.node3_cpu_label.setFont(font)
        self.node3_cpu_label.setStyleSheet("color: rgb(255, 255, 255);")
        self.node3_cpu_label.setObjectName("node3_cpu_label")
        self.node3_res_gridLayout.addWidget(self.node3_cpu_label, 0, 0, 1, 1)

        # cpu bar
        self.node3_cpu_bar = QtWidgets.QProgressBar(self.node3_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node3_cpu_bar.sizePolicy().hasHeightForWidth())
        self.node3_cpu_bar.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        font.setKerning(True)
        self.node3_cpu_bar.setFont(font)
        self.node3_cpu_bar.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.node3_cpu_bar.setAutoFillBackground(False)
        self.node3_cpu_bar.setStyleSheet("color: rgb(255, 255, 255);")
        self.node3_cpu_bar.setProperty("value", 0)
        self.node3_cpu_bar.setTextVisible(False)
        self.node3_cpu_bar.setFixedHeight(28)
        self.node3_cpu_bar.setObjectName("node3_cpu_bar")
        self.node3_res_gridLayout.addWidget(self.node3_cpu_bar, 0, 1, 1, 2)

        # cpu num
        self.node3_cpu_num = QtWidgets.QLabel(self.node3_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node3_cpu_num.sizePolicy().hasHeightForWidth())
        self.node3_cpu_num.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node3_cpu_num.setFont(font)
        self.node3_cpu_num.setStyleSheet("color: rgb(255, 255, 255);")
        self.node3_cpu_num.setObjectName("node3_cpu_num")
        self.node3_res_gridLayout.addWidget(self.node3_cpu_num, 0, 4, 1, 1)

        # mem
        self.node3_mem_label = QtWidgets.QLabel(self.node3_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node3_mem_label.sizePolicy().hasHeightForWidth())
        self.node3_mem_label.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(18)
        self.node3_mem_label.setFont(font)
        self.node3_mem_label.setStyleSheet("color: rgb(255, 255, 255);")
        self.node3_mem_label.setObjectName("node3_mem_label")
        self.node3_res_gridLayout.addWidget(self.node3_mem_label, 1, 0, 1, 1)

        # mem bar
        self.node3_mem_bar = QtWidgets.QProgressBar(self.node3_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node3_mem_bar.sizePolicy().hasHeightForWidth())
        self.node3_mem_bar.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        self.node3_mem_bar.setFont(font)
        self.node3_mem_bar.setStyleSheet("color: rgb(255, 255, 255);")
        self.node3_mem_bar.setProperty("value", 0)
        self.node3_mem_bar.setTextVisible(False)
        self.node3_mem_bar.setFixedHeight(28)
        self.node3_mem_bar.setObjectName("node3_mem_bar")
        self.node3_res_gridLayout.addWidget(self.node3_mem_bar, 1, 1, 1, 2)

        # mem num
        self.node3_mem_num = QtWidgets.QLabel(self.node3_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node3_mem_num.sizePolicy().hasHeightForWidth())
        self.node3_mem_num.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node3_mem_num.setFont(font)
        self.node3_mem_num.setStyleSheet("color: rgb(255, 255, 255);")
        self.node3_mem_num.setObjectName("node3_mem_num")
        self.node3_res_gridLayout.addWidget(self.node3_mem_num, 1, 4, 1, 1)

        # Disk
        self.node3_net_label = QtWidgets.QLabel(self.node3_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node3_net_label.sizePolicy().hasHeightForWidth())
        self.node3_net_label.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(18)
        self.node3_net_label.setFont(font)
        self.node3_net_label.setStyleSheet("color: rgb(255, 255, 255);")
        self.node3_net_label.setObjectName("node3_net_label")
        self.node3_res_gridLayout.addWidget(self.node3_net_label, 2, 0, 1, 1)

        # disk_read
        self.node3_net_read_label = QtWidgets.QLabel(self.node3_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node3_net_read_label.sizePolicy().hasHeightForWidth())
        self.node3_net_read_label.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node3_net_read_label.setFont(font)
        self.node3_net_read_label.setStyleSheet("color: rgb(255, 255, 255);")
        self.node3_net_read_label.setObjectName("node3_net_read_label")
        self.node3_res_gridLayout.addWidget(self.node3_net_read_label, 2, 2, 1, 1)

        # disk_write
        self.node3_net_read_v = QtWidgets.QLabel(self.node3_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node3_net_read_v.sizePolicy().hasHeightForWidth())
        self.node3_net_read_v.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node3_net_read_v.setFont(font)
        self.node3_net_read_v.setStyleSheet("color: rgb(255, 255, 255);")
        self.node3_net_read_v.setObjectName("node3_net_read_v")
        self.node3_res_gridLayout.addWidget(self.node3_net_read_v, 2, 4, 1, 1)

        self.node3_net_name = QtWidgets.QLabel(self.node3_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node3_net_name.sizePolicy().hasHeightForWidth())
        self.node3_net_name.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node3_net_name.setFont(font)
        self.node3_net_name.setStyleSheet("color: rgb(0, 17, 53);")
        self.node3_net_name.setObjectName("node3_net_name")
        self.node3_res_gridLayout.addWidget(self.node3_net_name, 3, 0, 1, 1)

        # disk_read
        self.node3_net_write_label = QtWidgets.QLabel(self.node3_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node3_net_write_label.sizePolicy().hasHeightForWidth())
        self.node3_net_write_label.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node3_net_write_label.setFont(font)
        self.node3_net_write_label.setStyleSheet("color: rgb(255, 255, 255);")
        self.node3_net_write_label.setObjectName("node3_net_write_label")
        self.node3_res_gridLayout.addWidget(self.node3_net_write_label, 3, 2, 1, 1)

        # disk_write
        self.node3_net_write_v = QtWidgets.QLabel(self.node3_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node3_net_write_v.sizePolicy().hasHeightForWidth())
        self.node3_net_write_v.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node3_net_write_v.setFont(font)
        self.node3_net_write_v.setStyleSheet("color: rgb(255, 255, 255);")
        self.node3_net_write_v.setObjectName("node3_net_write_v")
        self.node3_res_gridLayout.addWidget(self.node3_net_write_v, 3, 4, 1, 1)
        #################################
        # Disk
        self.node3_disk_label = QtWidgets.QLabel(self.node3_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node3_disk_label.sizePolicy().hasHeightForWidth())
        self.node3_disk_label.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(18)
        self.node3_disk_label.setFont(font)
        self.node3_disk_label.setStyleSheet("color: rgb(255, 255, 255);")
        self.node3_disk_label.setObjectName("node3_disk_label")
        self.node3_res_gridLayout.addWidget(self.node3_disk_label, 4, 0, 1, 1)

        # disk_read
        self.node3_disk_read_label = QtWidgets.QLabel(self.node3_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node3_disk_read_label.sizePolicy().hasHeightForWidth())
        self.node3_disk_read_label.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node3_disk_read_label.setFont(font)
        self.node3_disk_read_label.setStyleSheet("color: rgb(255, 255, 255);")
        self.node3_disk_read_label.setObjectName("node3_disk_read_label")
        self.node3_res_gridLayout.addWidget(self.node3_disk_read_label, 4, 2, 1, 1)

        # disk_write
        self.node3_disk_read_v = QtWidgets.QLabel(self.node3_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node3_disk_read_v.sizePolicy().hasHeightForWidth())
        self.node3_disk_read_v.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node3_disk_read_v.setFont(font)
        self.node3_disk_read_v.setStyleSheet("color: rgb(255, 255, 255);")
        self.node3_disk_read_v.setObjectName("node3_disk_read_v")
        self.node3_res_gridLayout.addWidget(self.node3_disk_read_v, 4, 4, 1, 1)

        self.node3_disk_name = QtWidgets.QLabel(self.node3_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node3_disk_name.sizePolicy().hasHeightForWidth())
        self.node3_disk_name.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node3_disk_name.setFont(font)
        self.node3_disk_name.setStyleSheet("color: rgb(255, 255, 255);")
        self.node3_disk_name.setObjectName("node3_disk_name")
        self.node3_res_gridLayout.addWidget(self.node3_disk_name, 5, 0, 1, 2)

        # disk_read
        self.node3_disk_write_label = QtWidgets.QLabel(self.node3_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node3_disk_write_label.sizePolicy().hasHeightForWidth())
        self.node3_disk_write_label.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node3_disk_write_label.setFont(font)
        self.node3_disk_write_label.setStyleSheet("color: rgb(255, 255, 255);")
        self.node3_disk_write_label.setObjectName("node3_disk_write_label")
        self.node3_res_gridLayout.addWidget(self.node3_disk_write_label, 5, 2, 1, 1)

        # disk_write
        self.node3_disk_write_v = QtWidgets.QLabel(self.node3_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node3_disk_write_v.sizePolicy().hasHeightForWidth())
        self.node3_disk_write_v.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node3_disk_write_v.setFont(font)
        self.node3_disk_write_v.setStyleSheet("color: rgb(255, 255, 255);")
        self.node3_disk_write_v.setObjectName("node3_disk_write_v")
        self.node3_res_gridLayout.addWidget(self.node3_disk_write_v, 5, 4, 1, 1)

        self.node3_res_gridLayout.setColumnStretch(0, 2)
        self.node3_res_gridLayout.setColumnStretch(1, 1)
        self.node3_res_gridLayout.setColumnStretch(2, 0)
        self.node3_res_gridLayout.setColumnStretch(3, 1)

        self.node3_verticalLayout.addWidget(self.node3_resource)
        self.node3_verticalLayout.setStretch(0, 1)
        self.node3_verticalLayout.setStretch(1, 1)
        self.node3_verticalLayout.setStretch(2, 4)
        self.node3_verticalLayout.setStretch(3, 4)
        self.status_monitor_layout.addWidget(self.node3)

        ################################################################################################################################################
        # -------------------------------------------------------------------------------------------------------------------------------------------- #
        ################################################################################################################################################
        self.node4 = QtWidgets.QGroupBox(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node4.sizePolicy().hasHeightForWidth())
        self.node4.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(19)
        font.setBold(True)
        font.setWeight(75)
        self.node4.setFont(font)
        self.node4.setStyleSheet("color: rgb(255, 255, 255);\n"
                                 "border: 4px solid #2F528F;\n"
                                 "border-radius: 10px;")
        self.node4.setTitle("")
        self.node4.setObjectName("node4")
        self.node4_verticalLayout = QtWidgets.QVBoxLayout(self.node4)
        self.node4_verticalLayout.setContentsMargins(-1, 8, -1, 4)
        self.node4_verticalLayout.setObjectName("node4_verticalLayout")

        # 第一个部件，展示node名称，之后切换时需要动态变动
        self.node4_label = QtWidgets.QLabel(self.node4)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(20)
        font.setBold(True)
        font.setWeight(75)
        self.node4_label.setFont(font)
        self.node4_label.setStyleSheet("border: none;")
        self.node4_label.setObjectName("node4_label")
        self.node4_verticalLayout.addWidget(self.node4_label)

        self.node4_wl_label = QtWidgets.QLabel(self.node4)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(20)
        font.setBold(True)
        font.setWeight(75)
        self.node4_wl_label.setFont(font)
        self.node4_wl_label.setStyleSheet("border: none;")
        self.node4_wl_label.setObjectName("node4_wl_label")
        self.node4_verticalLayout.addWidget(self.node4_wl_label)

        self.node4_net = QtWidgets.QGroupBox(self.node4)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node4_net.sizePolicy().hasHeightForWidth())
        self.node4_net.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(19)
        font.setBold(True)
        font.setWeight(75)
        self.node4_net.setFont(font)
        self.node4_net.setStyleSheet("color: rgb(255, 255, 255);border: none;")
        self.node4_net.setObjectName("node4_net")
        self.node4_net.setMinimumSize(250, 250)
        self.node4_verticalLayout.addWidget(self.node4_net)

        # 第三个部件，展示资源占用，包括CPU、内存、网络延迟
        self.node4_resource = QtWidgets.QGroupBox(self.node4)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node4_resource.sizePolicy().hasHeightForWidth())
        self.node4_resource.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(19)
        self.node4_resource.setFont(font)
        self.node4_resource.setStyleSheet("color: rgb(255, 255, 255);\n"
                                          "border: none;")
        self.node4_resource.setTitle("")
        self.node4_resource.setObjectName("node4_resource")
        self.node4_res_gridLayout = QtWidgets.QGridLayout(self.node4_resource)
        self.node4_res_gridLayout.setObjectName("node4_res_gridLayout")

        # node2
        # cpu
        self.node4_cpu_label = QtWidgets.QLabel(self.node4_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node4_cpu_label.sizePolicy().hasHeightForWidth())
        self.node4_cpu_label.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(18)
        self.node4_cpu_label.setFont(font)
        self.node4_cpu_label.setStyleSheet("color: rgb(255, 255, 255);")
        self.node4_cpu_label.setObjectName("node4_cpu_label")
        self.node4_res_gridLayout.addWidget(self.node4_cpu_label, 0, 0, 1, 1)

        # cpu bar
        self.node4_cpu_bar = QtWidgets.QProgressBar(self.node4_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node4_cpu_bar.sizePolicy().hasHeightForWidth())
        self.node4_cpu_bar.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        font.setKerning(True)
        self.node4_cpu_bar.setFont(font)
        self.node4_cpu_bar.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.node4_cpu_bar.setAutoFillBackground(False)
        self.node4_cpu_bar.setStyleSheet("color: rgb(255, 255, 255);")
        self.node4_cpu_bar.setProperty("value", 0)
        self.node4_cpu_bar.setTextVisible(False)
        self.node4_cpu_bar.setFixedHeight(28)
        self.node4_cpu_bar.setObjectName("node4_cpu_bar")
        self.node4_res_gridLayout.addWidget(self.node4_cpu_bar, 0, 1, 1, 2)

        # cpu num
        self.node4_cpu_num = QtWidgets.QLabel(self.node4_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node4_cpu_num.sizePolicy().hasHeightForWidth())
        self.node4_cpu_num.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node4_cpu_num.setFont(font)
        self.node4_cpu_num.setStyleSheet("color: rgb(255, 255, 255);")
        self.node4_cpu_num.setObjectName("node4_cpu_num")
        self.node4_res_gridLayout.addWidget(self.node4_cpu_num, 0, 4, 1, 1)

        # mem
        self.node4_mem_label = QtWidgets.QLabel(self.node4_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node4_mem_label.sizePolicy().hasHeightForWidth())
        self.node4_mem_label.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(18)
        self.node4_mem_label.setFont(font)
        self.node4_mem_label.setStyleSheet("color: rgb(255, 255, 255);")
        self.node4_mem_label.setObjectName("node4_mem_label")
        self.node4_res_gridLayout.addWidget(self.node4_mem_label, 1, 0, 1, 1)

        # mem bar
        self.node4_mem_bar = QtWidgets.QProgressBar(self.node4_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node4_mem_bar.sizePolicy().hasHeightForWidth())
        self.node4_mem_bar.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        self.node4_mem_bar.setFont(font)
        self.node4_mem_bar.setStyleSheet("color: rgb(255, 255, 255);")
        self.node4_mem_bar.setProperty("value", 0)
        self.node4_mem_bar.setTextVisible(False)
        self.node4_mem_bar.setFixedHeight(28)
        self.node4_mem_bar.setObjectName("node4_mem_bar")
        self.node4_res_gridLayout.addWidget(self.node4_mem_bar, 1, 1, 1, 2)

        # mem num
        self.node4_mem_num = QtWidgets.QLabel(self.node4_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node4_mem_num.sizePolicy().hasHeightForWidth())
        self.node4_mem_num.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node4_mem_num.setFont(font)
        self.node4_mem_num.setStyleSheet("color: rgb(255, 255, 255);")
        self.node4_mem_num.setObjectName("node4_mem_num")
        self.node4_res_gridLayout.addWidget(self.node4_mem_num, 1, 4, 1, 1)

        # Disk
        self.node4_net_label = QtWidgets.QLabel(self.node4_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node4_net_label.sizePolicy().hasHeightForWidth())
        self.node4_net_label.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(18)
        self.node4_net_label.setFont(font)
        self.node4_net_label.setStyleSheet("color: rgb(255, 255, 255);")
        self.node4_net_label.setObjectName("node4_net_label")
        self.node4_res_gridLayout.addWidget(self.node4_net_label, 2, 0, 1, 1)

        # disk_read
        self.node4_net_read_label = QtWidgets.QLabel(self.node4_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node4_net_read_label.sizePolicy().hasHeightForWidth())
        self.node4_net_read_label.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node4_net_read_label.setFont(font)
        self.node4_net_read_label.setStyleSheet("color: rgb(255, 255, 255);")
        self.node4_net_read_label.setObjectName("node4_net_read_label")
        self.node4_res_gridLayout.addWidget(self.node4_net_read_label, 2, 2, 1, 1)

        # disk_write
        self.node4_net_read_v = QtWidgets.QLabel(self.node4_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node4_net_read_v.sizePolicy().hasHeightForWidth())
        self.node4_net_read_v.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node4_net_read_v.setFont(font)
        self.node4_net_read_v.setStyleSheet("color: rgb(255, 255, 255);")
        self.node4_net_read_v.setObjectName("node4_net_read_v")
        self.node4_res_gridLayout.addWidget(self.node4_net_read_v, 2, 4, 1, 1)

        self.node4_net_name = QtWidgets.QLabel(self.node4_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node4_net_name.sizePolicy().hasHeightForWidth())
        self.node4_net_name.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node4_net_name.setFont(font)
        self.node4_net_name.setStyleSheet("color: rgb(0, 17, 53);")
        self.node4_net_name.setObjectName("node4_net_name")
        self.node4_res_gridLayout.addWidget(self.node4_net_name, 3, 0, 1, 1)

        # disk_read
        self.node4_net_write_label = QtWidgets.QLabel(self.node4_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node4_net_write_label.sizePolicy().hasHeightForWidth())
        self.node4_net_write_label.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node4_net_write_label.setFont(font)
        self.node4_net_write_label.setStyleSheet("color: rgb(255, 255, 255);")
        self.node4_net_write_label.setObjectName("node4_net_write_label")
        self.node4_res_gridLayout.addWidget(self.node4_net_write_label, 3, 2, 1, 1)

        # disk_write
        self.node4_net_write_v = QtWidgets.QLabel(self.node4_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node4_net_write_v.sizePolicy().hasHeightForWidth())
        self.node4_net_write_v.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node4_net_write_v.setFont(font)
        self.node4_net_write_v.setStyleSheet("color: rgb(255, 255, 255);")
        self.node4_net_write_v.setObjectName("node4_net_write_v")
        self.node4_res_gridLayout.addWidget(self.node4_net_write_v, 3, 4, 1, 1)
        #################################
        # Disk
        self.node4_disk_label = QtWidgets.QLabel(self.node4_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node4_disk_label.sizePolicy().hasHeightForWidth())
        self.node4_disk_label.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(18)
        self.node4_disk_label.setFont(font)
        self.node4_disk_label.setStyleSheet("color: rgb(255, 255, 255);")
        self.node4_disk_label.setObjectName("node4_disk_label")
        self.node4_res_gridLayout.addWidget(self.node4_disk_label, 4, 0, 1, 1)

        # disk_read
        self.node4_disk_read_label = QtWidgets.QLabel(self.node4_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node4_disk_read_label.sizePolicy().hasHeightForWidth())
        self.node4_disk_read_label.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node4_disk_read_label.setFont(font)
        self.node4_disk_read_label.setStyleSheet("color: rgb(255, 255, 255);")
        self.node4_disk_read_label.setObjectName("node4_disk_read_label")
        self.node4_res_gridLayout.addWidget(self.node4_disk_read_label, 4, 2, 1, 1)

        # disk_write
        self.node4_disk_read_v = QtWidgets.QLabel(self.node4_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node4_disk_read_v.sizePolicy().hasHeightForWidth())
        self.node4_disk_read_v.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node4_disk_read_v.setFont(font)
        self.node4_disk_read_v.setStyleSheet("color: rgb(255, 255, 255);")
        self.node4_disk_read_v.setObjectName("node4_disk_read_v")
        self.node4_res_gridLayout.addWidget(self.node4_disk_read_v, 4, 4, 1, 1)

        self.node4_disk_name = QtWidgets.QLabel(self.node4_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node4_disk_name.sizePolicy().hasHeightForWidth())
        self.node4_disk_name.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node4_disk_name.setFont(font)
        self.node4_disk_name.setStyleSheet("color: rgb(255, 255, 255);")
        self.node4_disk_name.setObjectName("node4_disk_name")
        self.node4_res_gridLayout.addWidget(self.node4_disk_name, 5, 0, 1, 2)

        # disk_read
        self.node4_disk_write_label = QtWidgets.QLabel(self.node4_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node4_disk_write_label.sizePolicy().hasHeightForWidth())
        self.node4_disk_write_label.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node4_disk_write_label.setFont(font)
        self.node4_disk_write_label.setStyleSheet("color: rgb(255, 255, 255);")
        self.node4_disk_write_label.setObjectName("node4_disk_write_label")
        self.node4_res_gridLayout.addWidget(self.node4_disk_write_label, 5, 2, 1, 1)

        # disk_write
        self.node4_disk_write_v = QtWidgets.QLabel(self.node4_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node4_disk_write_v.sizePolicy().hasHeightForWidth())
        self.node4_disk_write_v.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node4_disk_write_v.setFont(font)
        self.node4_disk_write_v.setStyleSheet("color: rgb(255, 255, 255);")
        self.node4_disk_write_v.setObjectName("node4_disk_write_v")
        self.node4_res_gridLayout.addWidget(self.node4_disk_write_v, 5, 4, 1, 1)

        self.node4_res_gridLayout.setColumnStretch(0, 2)
        self.node4_res_gridLayout.setColumnStretch(1, 1)
        self.node4_res_gridLayout.setColumnStretch(2, 0)
        self.node4_res_gridLayout.setColumnStretch(3, 1)

        self.node4_verticalLayout.addWidget(self.node4_resource)
        self.node4_verticalLayout.setStretch(0, 1)
        self.node4_verticalLayout.setStretch(1, 1)
        self.node4_verticalLayout.setStretch(2, 4)
        self.node4_verticalLayout.setStretch(3, 4)
        self.status_monitor_layout.addWidget(self.node4)

        self.horizontalLayout.addLayout(self.status_monitor_layout)

        # 在底部添加logo
        self.nokia_logo = QtWidgets.QLabel()
        self.nokia_logo.setPixmap(QtGui.QPixmap("./images/bell_logo.png"))
        self.nokia_logo.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.nokia_logo_layout = QtWidgets.QHBoxLayout()
        self.nokia_logo_layout.addStretch(19)
        self.nokia_logo_layout.addWidget(self.nokia_logo)
        self.nokia_logo_layout.addStretch(1)
        self.nokia_logo.setStyleSheet("border: none;")
        self.horizontalLayout.addLayout(self.nokia_logo_layout)

        self._initSpeedMeter()
        self.setText()
        self.layout.addWidget(self.groupBox)

        self.history_cpu_1 = Queue(-1)
        self.history_cpu_2 = Queue(-1)
        self.history_cpu_3 = Queue(-1)
        self.history_cpu_4 = Queue(-1)

        # self.history_delay_1 = Queue(15000)
        # self.history_delay_2 = Queue(15000)
        # self.history_delay_3 = Queue(15000)
        # self.history_delay_4 = Queue(15000)

        self.history_delay_1 = None
        self.history_delay_2 = None
        self.history_delay_3 = None
        self.history_delay_4 = None

        self.history1 = DataVisualizationWindow(self.history_cpu_1, self.history_delay_1, "Node1")
        self.history1.setVisible(False)

        self.history2 = DataVisualizationWindow(self.history_cpu_2, self.history_delay_2, "Node2")
        self.history2.setVisible(False)

        self.history3 = DataVisualizationWindow(self.history_cpu_3, self.history_delay_3, "Node3")
        self.history3.setVisible(False)

        self.history4 = DataVisualizationWindow(self.history_cpu_4, self.history_delay_4, "Node4")
        self.history4.setVisible(False)

    def _initSpeedMeter(self):
        font = QtGui.QFont()
        font.setPointSize(15)
        font.setFamily("微软雅黑")

        self.speed_meter_1 = SpeedMeter('', '', 0, 100)
        self.layout_1 = QVBoxLayout()
        self.layout_1.addWidget(self.speed_meter_1)

        self.hlayout_1 = QHBoxLayout()

        self.plot_button1 = QPushButton("History", self)
        self.plot_button1.setFont(font)
        self.plot_button1.setFixedWidth(200)
        # self.plot_button1.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignCenter)
        self.plot_button1.clicked.connect(self.show_history1)
        self.plot_button1.setStyleSheet("border: 1px solid;\n"
                                        "background-color: white;\n"
                                        "color: black")
        self.hlayout_1.addWidget(self.plot_button1)
        self.layout_1.addLayout(self.hlayout_1)

        self.layout_1.setStretch(0, 3)
        self.layout_1.setStretch(1, 1)
        # self.layout_1.setStretch(2,1)

        self.node1_net.setLayout(self.layout_1)
        self.speed_meter_1.setGeometry(200, 200, 200, 200)
        #########################################################################################
        self.speed_meter_2 = SpeedMeter('', '', 0, 100)
        self.layout_2 = QVBoxLayout()
        self.layout_2.addWidget(self.speed_meter_2)

        self.hlayout_2 = QHBoxLayout()

        self.plot_button2 = QPushButton("History", self)
        self.plot_button2.setFont(font)
        self.plot_button2.setFixedWidth(200)
        self.plot_button2.clicked.connect(self.show_history2)
        self.plot_button2.setStyleSheet("border: 1px solid;\n"
                                        "background-color: white;\n"
                                        "color: black")
        self.hlayout_2.addWidget(self.plot_button2)
        self.layout_2.addLayout(self.hlayout_2)

        self.layout_2.setStretch(0, 3)
        self.layout_2.setStretch(1, 1)
        # self.layout_2.setStretch(2, 1)

        self.node2_net.setLayout(self.layout_2)
        self.speed_meter_2.setGeometry(200, 200, 200, 200)
        ##################################################################################################################
        self.speed_meter_3 = SpeedMeter('', '', 0, 100)
        self.layout_3 = QVBoxLayout()
        self.layout_3.addWidget(self.speed_meter_3)

        self.hlayout_3 = QHBoxLayout()

        self.plot_button3 = QPushButton("History", self)
        self.plot_button3.setFont(font)
        self.plot_button3.setFixedWidth(200)
        self.plot_button3.clicked.connect(self.show_history3)
        self.plot_button3.setStyleSheet("border: 1px solid;\n"
                                        "background-color: white;\n"
                                        "color: black")
        self.hlayout_3.addWidget(self.plot_button3)
        self.layout_3.addLayout(self.hlayout_3)

        self.layout_3.setStretch(0, 3)
        self.layout_3.setStretch(1, 1)
        # self.layout_3.setStretch(2, 1)

        self.node3_net.setLayout(self.layout_3)
        self.speed_meter_3.setGeometry(200, 200, 200, 200)

        ##################################################################################################################
        self.speed_meter_4 = SpeedMeter('', '', 0, 100)
        self.layout_4 = QVBoxLayout()
        self.layout_4.addWidget(self.speed_meter_4)

        self.hlayout_4 = QHBoxLayout()

        self.plot_button4 = QPushButton("History", self)
        self.plot_button4.setFont(font)
        self.plot_button4.setFixedWidth(200)
        self.plot_button4.clicked.connect(self.show_history4)
        self.plot_button4.setStyleSheet("border: 1px solid;\n"
                                        "background-color: white;\n"
                                        "color: black")
        self.hlayout_4.addWidget(self.plot_button4)
        self.layout_4.addLayout(self.hlayout_4)

        self.layout_4.setStretch(0, 3)
        self.layout_4.setStretch(1, 1)
        # self.layout_4.setStretch(2, 1)

        self.node4_net.setLayout(self.layout_4)
        self.speed_meter_4.setGeometry(200, 200, 200, 200)

    def show_history1(self):
        # self.history1 = DataVisualizationWindow(self.history_cpu_1, self.history_delay_1, "Node1")
        self.history1.setVisible(True)

    def show_history2(self):
        # self.history2 = DataVisualizationWindow(self.history_cpu_2, self.history_delay_2, "Node2")
        self.history2.setVisible(True)

    def show_history3(self):
        # self.history3 = DataVisualizationWindow(self.history_cpu_3, self.history_delay_3, "Node3")
        self.history3.setVisible(True)

    def show_history4(self):
        # self.history4 = DataVisualizationWindow(self.history_cpu_4, self.history_delay_4, "Node4")
        self.history4.setVisible(True)

    def setText(self):
        self.node1_label.setText("C-Node1")
        self.node1_wl_label.setText("Workload")
        self.node1_cpu_label.setText("CPU")
        self.node1_cpu_num.setText("0.0%")
        self.node1_mem_label.setText("MEM")
        self.node1_mem_num.setText("0.0%")
        self.node1_net_label.setText("NET I/O")
        self.node1_net_read_label.setText("Tx/s")
        self.node1_net_read_v.setText("Rx/s")
        self.node1_net_name.setText("Total")
        self.node1_net_write_label.setText("345kb")
        self.node1_net_write_v.setText("333kb")
        self.node1_disk_label.setText("DISK")
        self.node1_disk_read_label.setText("R/s")
        self.node1_disk_read_v.setText("W/s")
        self.node1_disk_name.setText("Total")
        self.node1_disk_write_label.setText("10M")
        self.node1_disk_write_v.setText("2M")

        self.node2_label.setText("C-Node2")
        self.node2_wl_label.setText("Workload")
        self.node2_cpu_label.setText("CPU")
        self.node2_cpu_num.setText("0.0%")
        self.node2_mem_label.setText("MEM")
        self.node2_mem_num.setText("0.0%")
        self.node2_net_label.setText("NET I/O")
        self.node2_net_read_label.setText("Tx/s")
        self.node2_net_read_v.setText("Rx/s")
        self.node2_net_name.setText("Total")
        self.node2_net_write_label.setText("345kb")
        self.node2_net_write_v.setText("333kb")
        self.node2_disk_label.setText("DISK")
        self.node2_disk_read_label.setText("R/s")
        self.node2_disk_read_v.setText("W/s")
        self.node2_disk_name.setText("Total")
        self.node2_disk_write_label.setText("10M")
        self.node2_disk_write_v.setText("2M")

        self.node3_label.setText("C-Node3")
        self.node3_wl_label.setText("Workload")
        self.node3_cpu_label.setText("CPU")
        self.node3_cpu_num.setText("0.0%")
        self.node3_mem_label.setText("MEM")
        self.node3_mem_num.setText("0.0%")
        self.node3_net_label.setText("NET I/O")
        self.node3_net_read_label.setText("Tx/s")
        self.node3_net_read_v.setText("Rx/s")
        self.node3_net_name.setText("Total")
        self.node3_net_write_label.setText("345kb")
        self.node3_net_write_v.setText("333kb")
        self.node3_disk_label.setText("DISK")
        self.node3_disk_read_label.setText("R/s")
        self.node3_disk_read_v.setText("W/s")
        self.node3_disk_name.setText("Total")
        self.node3_disk_write_label.setText("10M")
        self.node3_disk_write_v.setText("2M")

        self.node4_label.setText("Average")
        self.node4_wl_label.setText("Workload")
        self.node4_cpu_label.setText("CPU")
        self.node4_cpu_num.setText("0.0%")
        self.node4_mem_label.setText("MEM")
        self.node4_mem_num.setText("0.0%")
        self.node4_net_label.setText("NET I/O")
        self.node4_net_read_label.setText("Tx/s")
        self.node4_net_read_v.setText("Rx/s")
        self.node4_net_name.setText("Total")
        self.node4_net_write_label.setText("345kb")
        self.node4_net_write_v.setText("333kb")
        self.node4_disk_label.setText("DISK")
        self.node4_disk_read_label.setText("R/s")
        self.node4_disk_read_v.setText("W/s")
        self.node4_disk_name.setText("Total")
        self.node4_disk_write_label.setText("10M")
        self.node4_disk_write_v.setText("2M")

    def _initResourceUri(self):
        self.node1_resource_uri = f"http://{self.cfn_manager.demo_config.get_node('c_node1')['node_ip']}:8000/synthetic"
        self.node2_resource_uri = f"http://{self.cfn_manager.demo_config.get_node('c_node2')['node_ip']}:8000/synthetic"
        self.node3_resource_uri = f"http://{self.cfn_manager.demo_config.get_node('c_node3')['node_ip']}:8000/synthetic"
        node1_client = requests.get(url=self.node1_resource_uri, timeout=3)
        node2_client = requests.get(url=self.node2_resource_uri, timeout=3)
        node3_client = requests.get(url=self.node3_resource_uri, timeout=3)
        if node1_client:
            self.node1_info = node1_client.json()

        if node2_client:
            self.node2_info = node2_client.json()

        if node3_client:
            self.node3_info = node3_client.json()

        nodes_info = [self.node1_info, self.node2_info, self.node3_info]

        self.node4_info = {
            "cpu": round(sum(ni['cpu'] for ni in nodes_info) / len(nodes_info), 2),
            "mem": round(sum(ni['mem'] for ni in nodes_info) / len(nodes_info), 2),
            "disk": [
                round(sum(ni['disk'][0] for ni in nodes_info) / len(nodes_info), 2),
                round(sum(ni['disk'][1] for ni in nodes_info) / len(nodes_info), 2)
            ],
            "net": [
                round(sum(ni['net'][0] for ni in nodes_info) / len(nodes_info), 2),
                round(sum(ni['net'][1] for ni in nodes_info) / len(nodes_info), 2)
            ]
        }
        self.node1_globe_info = [[self.node1_info['net'][0], self.node1_info['net'][1]], [self.node1_info['disk'][0], self.node1_info['disk'][1]]]
        self.node2_globe_info = [[self.node2_info['net'][0], self.node2_info['net'][1]], [self.node2_info['disk'][0], self.node2_info['disk'][1]]]
        self.node3_globe_info = [[self.node3_info['net'][0], self.node3_info['net'][1]], [self.node3_info['disk'][0], self.node3_info['disk'][1]]]
        self.node4_globe_info = [[self.node4_info['net'][0], self.node4_info['net'][1]], [self.node4_info['disk'][0], self.node4_info['disk'][1]]]

    def requestResourceInfo(self):
        # print("get resource!")
        try:
            node1_client = requests.get(url=self.node1_resource_uri, timeout=3)
            node2_client = requests.get(url=self.node2_resource_uri, timeout=3)
            node3_client = requests.get(url=self.node3_resource_uri, timeout=3)
            if node1_client:
                self.node1_info = node1_client.json()

            if node2_client:
                self.node2_info = node2_client.json()

            if node3_client:
                self.node3_info = node3_client.json()

            nodes_info = [self.node1_info, self.node2_info, self.node3_info]
            self.node4_info = {
                "cpu": round(sum(ni['cpu'] for ni in nodes_info) / len(nodes_info), 2),
                "mem": round(sum(ni['mem'] for ni in nodes_info) / len(nodes_info), 2),
                "disk": [
                    round(sum(ni['disk'][0] for ni in nodes_info) / len(nodes_info), 2),
                    round(sum(ni['disk'][1] for ni in nodes_info) / len(nodes_info), 2)
                ],
                "net": [
                    round(sum(ni['net'][0] for ni in nodes_info) / len(nodes_info), 2),
                    round(sum(ni['net'][1] for ni in nodes_info) / len(nodes_info), 2)
                ]
            }
            nodes_info.append(self.node4_info)
            self.updateHeatMap.emit([self.node1_info['cpu'], self.node2_info['cpu'], self.node3_info['cpu']])
        except Exception as exp:
            print(f"Get Info exp: {exp}")
        finally:
            pass

    def updateNodesInfo(self):
        # print("update resource!")
        self.updateNode1Info()
        self.updateNode2Info()
        self.updateNode3Info()
        self.updateNode4Info()
        self.node1_globe_info = [[self.node1_info['net'][0], self.node1_info['net'][1]],
                                 [self.node1_info['disk'][0], self.node1_info['disk'][1]]]
        self.node2_globe_info = [[self.node2_info['net'][0], self.node2_info['net'][1]],
                                 [self.node2_info['disk'][0], self.node2_info['disk'][1]]]
        self.node3_globe_info = [[self.node3_info['net'][0], self.node3_info['net'][1]],
                                 [self.node3_info['disk'][0], self.node3_info['disk'][1]]]
        self.node4_globe_info = [[self.node4_info['net'][0], self.node4_info['net'][1]],
                                 [self.node4_info['disk'][0], self.node4_info['disk'][1]]]

    def updateNode1Info(self):
        cu = self.node1_info['cpu']
        mu = self.node1_info['mem']
        tx, dx = self.node1_info['net'][0] - self.node1_globe_info[0][0], self.node1_info['net'][1] - self.node1_globe_info[0][1]
        rb, wb = self.node1_info['disk'][0] - self.node1_globe_info[1][0], self.node1_info['disk'][1] - self.node1_globe_info[1][1]
        self.history_cpu_1.put(cu)
        self.history1.update_plot()
        # self.history1.cpu_history.update_data_home()
        eval("self.node1_cpu_num.setText('" + str(cu) + "%'" + ")")
        eval("self.node1_mem_num.setText('" + str(mu) + "%'" + ")")
        self.speed_meter_1.setSpeed(cu)
        self.speed_meter_1.sharedPainter()
        self.node1_cpu_bar.setProperty("value", cu)
        if cu <= 50.0:
            self.node1_cpu_bar.setStyleSheet(
                "QProgressBar::chunk {background-color:rgb("f'{int(2.55 * cu * 2)}'",'255','0')}")
        else:
            self.node1_cpu_bar.setStyleSheet(
                "QProgressBar::chunk {background-color:rgb("f'{int(2.55 * (100 - (cu - 50) * 2))}'",'255','0')}")
        self.node1_cpu_bar.sharedPainter()
        self.node1_mem_bar.setProperty("value", mu)
        if mu <= 50.0:
            self.node1_mem_bar.setStyleSheet(
                "QProgressBar::chunk {background-color:rgb("f'{int(2.55 * mu * 2)}'",'255','0')}")
        else:
            self.node1_mem_bar.setStyleSheet(
                "QProgressBar::chunk {background-color:rgb("f'{int(2.55 * (100 - (mu - 50) * 2))}'",'255','0')}")
        self.node1_mem_bar.sharedPainter()
        tx_tag, dx_tag = net_formatter(tx, dx)

        self.node1_net_read_label.setText(f"Tx({tx_tag.split(' ')[1]})")
        self.node1_net_read_v.setText(f"{tx_tag.split(' ')[0]}")
        self.node1_net_write_label.setText(f"Rx({dx_tag.split(' ')[1]})")
        self.node1_net_write_v.setText(f"{dx_tag.split(' ')[0]}")

        r_tag, w_tag = disk_formatter(rb, wb)

        self.node1_disk_read_label.setText(f"Read({r_tag.split(' ')[1]})")
        self.node1_disk_read_v.setText(f"{r_tag.split(' ')[0]}")
        self.node1_disk_write_label.setText(f"Write({w_tag.split(' ')[1]})")
        self.node1_disk_write_v.setText(f"{w_tag.split(' ')[0]}")

    def updateNode2Info(self):
        cu = self.node2_info['cpu']
        mu = self.node2_info['mem']
        tx, dx = self.node2_info['net'][0] - self.node2_globe_info[0][0], self.node2_info['net'][1] - self.node2_globe_info[0][1]
        rb, wb = self.node2_info['disk'][0] - self.node2_globe_info[1][0], self.node2_info['disk'][1] - self.node2_globe_info[1][1]
        self.history_cpu_2.put(cu)
        self.history2.update_plot()
        # self.history2.cpu_history.update_data_home()
        eval("self.node2_cpu_num.setText('" + str(cu) + "%'" + ")")
        eval("self.node2_mem_num.setText('" + str(mu) + "%'" + ")")
        self.speed_meter_2.setSpeed(cu)
        self.speed_meter_2.sharedPainter()
        self.node2_cpu_bar.setProperty("value", cu)
        if cu <= 50.0:
            self.node2_cpu_bar.setStyleSheet(
                "QProgressBar::chunk {background-color:rgb("f'{int(2.55 * cu * 2)}'",'255','0')}")
        else:
            self.node2_cpu_bar.setStyleSheet(
                "QProgressBar::chunk {background-color:rgb("f'{int(2.55 * (100 - (cu - 50) * 2))}'",'255','0')}")
        self.node2_cpu_bar.sharedPainter()
        self.node2_mem_bar.setProperty("value", mu)
        if mu <= 50.0:
            self.node2_mem_bar.setStyleSheet(
                "QProgressBar::chunk {background-color:rgb("f'{int(2.55 * mu * 2)}'",'255','0')}")
        else:
            self.node2_mem_bar.setStyleSheet(
                "QProgressBar::chunk {background-color:rgb("f'{int(2.55 * (100 - (mu - 50) * 2))}'",'255','0')}")
            self.node2_mem_bar.sharedPainter()
        tx_tag, dx_tag = net_formatter(tx, dx)

        self.node2_net_read_label.setText(f"Tx({tx_tag.split(' ')[1]})")
        self.node2_net_read_v.setText(f"{tx_tag.split(' ')[0]}")
        self.node2_net_write_label.setText(f"Rx({dx_tag.split(' ')[1]})")
        self.node2_net_write_v.setText(f"{dx_tag.split(' ')[0]}")

        r_tag, w_tag = disk_formatter(rb, wb)

        self.node2_disk_read_label.setText(f"Read({r_tag.split(' ')[1]})")
        self.node2_disk_read_v.setText(f"{r_tag.split(' ')[0]}")
        self.node2_disk_write_label.setText(f"Write({w_tag.split(' ')[1]})")
        self.node2_disk_write_v.setText(f"{w_tag.split(' ')[0]}")

    def updateNode3Info(self):
        cu = self.node3_info['cpu']
        mu = self.node3_info['mem']
        tx, dx = self.node3_info['net'][0] - self.node3_globe_info[0][0], self.node3_info['net'][1] - self.node3_globe_info[0][1]
        rb, wb = self.node3_info['disk'][0] - self.node3_globe_info[1][0], self.node3_info['disk'][1] - self.node3_globe_info[1][1]
        self.history_cpu_3.put(cu)
        self.history3.update_plot()
        # self.history3.cpu_history.update_data_home()
        eval("self.node3_cpu_num.setText('" + str(cu) + "%'" + ")")
        eval("self.node3_mem_num.setText('" + str(mu) + "%'" + ")")
        self.speed_meter_3.setSpeed(cu)
        self.speed_meter_3.sharedPainter()
        self.node3_cpu_bar.setProperty("value", cu)
        if cu <= 50.0:
            self.node3_cpu_bar.setStyleSheet(
                "QProgressBar::chunk {background-color:rgb("f'{int(2.55 * cu * 2)}'",'255','0')}")
        else:
            self.node3_cpu_bar.setStyleSheet(
                "QProgressBar::chunk {background-color:rgb("f'{int(2.55 * (100 - (cu - 50) * 2))}'",'255','0')}")
        self.node3_cpu_bar.sharedPainter()
        self.node3_mem_bar.setProperty("value", mu)
        if mu <= 50.0:
            self.node3_mem_bar.setStyleSheet(
                "QProgressBar::chunk {background-color:rgb("f'{int(2.55 * mu * 2)}'",'255','0')}")
        else:
            self.node3_mem_bar.setStyleSheet(
                "QProgressBar::chunk {background-color:rgb("f'{int(2.55 * (100 - (mu - 50) * 2))}'",'255','0')}")
        self.node3_mem_bar.sharedPainter()
        tx_tag, dx_tag = net_formatter(tx, dx)

        self.node3_net_read_label.setText(f"Tx({tx_tag.split(' ')[1]})")
        self.node3_net_read_v.setText(f"{tx_tag.split(' ')[0]}")
        self.node3_net_write_label.setText(f"Rx({dx_tag.split(' ')[1]})")
        self.node3_net_write_v.setText(f"{dx_tag.split(' ')[0]}")

        r_tag, w_tag = disk_formatter(rb, wb)

        self.node3_disk_read_label.setText(f"Read({r_tag.split(' ')[1]})")
        self.node3_disk_read_v.setText(f"{r_tag.split(' ')[0]}")
        self.node3_disk_write_label.setText(f"Write({w_tag.split(' ')[1]})")
        self.node3_disk_write_v.setText(f"{w_tag.split(' ')[0]}")

    def updateNode4Info(self):
        cu = self.node4_info['cpu']
        mu = self.node4_info['mem']
        tx, dx = self.node4_info['net'][0] - self.node4_globe_info[0][0], self.node4_info['net'][1] - self.node4_globe_info[0][1]
        rb, wb = self.node4_info['disk'][0] - self.node4_globe_info[1][0], self.node4_info['disk'][1] - self.node4_globe_info[1][1]
        self.history_cpu_4.put(cu)
        self.history4.update_plot()
        # self.history4.cpu_history.update_data_home()
        eval("self.node4_cpu_num.setText('" + str(cu) + "%'" + ")")
        eval("self.node4_mem_num.setText('" + str(mu) + "%'" + ")")
        self.speed_meter_4.setSpeed(cu)
        self.speed_meter_4.sharedPainter()
        self.node4_cpu_bar.setProperty("value", cu)
        if cu <= 50.0:
            self.node4_cpu_bar.setStyleSheet(
                "QProgressBar::chunk {background-color:rgb("f'{int(2.55 * cu * 2)}'",'255','0')}")
        else:
            self.node4_cpu_bar.setStyleSheet(
                "QProgressBar::chunk {background-color:rgb("f'{int(2.55 * (100 - (cu - 50) * 2))}'",'255','0')}")
        self.node4_cpu_bar.sharedPainter()
        self.node4_mem_bar.setProperty("value", mu)
        if mu <= 50.0:
            self.node4_mem_bar.setStyleSheet(
                "QProgressBar::chunk {background-color:rgb("f'{int(2.55 * mu * 2)}'",'255','0')}")
        else:
            self.node4_mem_bar.setStyleSheet(
                "QProgressBar::chunk {background-color:rgb("f'{int(2.55 * (100 - (mu - 50) * 2))}'",'255','0')}")
        self.node4_mem_bar.sharedPainter()
        tx_tag, dx_tag = net_formatter(tx, dx)
        self.node4_net_read_label.setText(f"Tx({tx_tag.split(' ')[1]})")
        self.node4_net_read_v.setText(f"{tx_tag.split(' ')[0]}")
        self.node4_net_write_label.setText(f"Rx({dx_tag.split(' ')[1]})")
        self.node4_net_write_v.setText(f"{dx_tag.split(' ')[0]}")

        r_tag, w_tag = disk_formatter(rb, wb)

        self.node4_disk_read_label.setText(f"Read({r_tag.split(' ')[1]})")
        self.node4_disk_read_v.setText(f"{r_tag.split(' ')[0]}")
        self.node4_disk_write_label.setText(f"Write({w_tag.split(' ')[1]})")
        self.node4_disk_write_v.setText(f"{w_tag.split(' ')[0]}")


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    data_visual = data_visualize()
    data_visual.show()
    computingNetResMonTimer = QtCore.QTimer()
    computingNetResMonTimer.setInterval(100)
    computingNetResMonTimer.timeout.connect(data_visual.updateNodesInfo)
    computingNetResMonTimer.start()
    # data_mon = repeatTimer(3, data_visual.updateNodesInfo, autostart=True)
    # data_mon.start()
    sys.exit(app.exec_())
