# -*- coding: utf-8 -*-
"""
@Time: 5/17/2024 11:47 AM
@Author: Honggang Yuan
@Email: honggang.yuan@nokia-sbell.com
Description: 
"""

import random
from multiprocessing import Queue

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtChart import QChartView
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QGroupBox, QPushButton

from resourcevisiualize.resourcehistory import HistoryWindow
from resourcevisiualize.speedmeter import SpeedMeter
from utils.reversequeue import reverseQueue


class DataVisualizationWindow(QWidget):
    def __init__(self, cpu_q, delay_q, windowTitle="History"):
        super().__init__()
        self.cpu_queue = cpu_q
        self.delay_queue = delay_q
        self.setWindowTitle(windowTitle)
        self.setGeometry(100, 100, 800, 600)
        layout = QVBoxLayout()

        self.cpu_history = HistoryWindow(parent=self, cpu_q=self.cpu_queue, delay_q=self.delay_queue)
        self.cpuHistoryView = QChartView(self.cpu_history)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        layout.addWidget(self.cpuHistoryView)
        self.setLayout(layout)

    def closeEvent(self, event):
        self.hide()
        event.ignore()


class data_v(QWidget):
    def __init__(self, parent=None, bw_list=[]):

        super().__init__()
        self.layout = QtWidgets.QHBoxLayout(self)
        self.setParent(parent)
        self.groupBox = QGroupBox("")
        self.groupBox.setStyleSheet("color: rgb(255, 255, 255);\n"
                                    "border: none;\n"
                                    "border-radius: 3px;\n"
                                    "background-color: #001135;")
        self.nodesBandWidthList = bw_list
        geo = {
            'top': 0,
            'left': 0,
            'width': 1920,
            'height': 1060}
        self.setGeometry(geo['left'], geo['top'], geo['width'], geo['height'])

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

        self.status_monitor_layout = QtWidgets.QHBoxLayout()
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
        self.node1_res_gridLayout.addWidget(self.node1_cpu_bar, 0, 1, 1, 1)

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
        self.node1_res_gridLayout.addWidget(self.node1_cpu_num, 0, 3, 1, 1)

        """
        # gpu
        self.node1_gpu_label = QtWidgets.QLabel(self.node1_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node1_gpu_label.sizePolicy().hasHeightForWidth())
        self.node1_gpu_label.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node1_gpu_label.setFont(font)
        self.node1_gpu_label.setStyleSheet("color: rgb(255, 255, 255);")
        self.node1_gpu_label.setObjectName("node1_gpu")
        self.node1_res_gridLayout.addWidget(self.node1_gpu_label, 1, 0, 1, 1)

        # gpu bar
        self.node1_gpu_bar = QtWidgets.QProgressBar(self.node1_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node1_gpu_bar.sizePolicy().hasHeightForWidth())
        self.node1_gpu_bar.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        self.node1_gpu_bar.setFont(font)
        self.node1_gpu_bar.setStyleSheet("color: rgb(255, 255, 255);")
        self.node1_gpu_bar.setProperty("value", 0)
        self.node1_gpu_bar.setTextVisible(False)
        self.node1_gpu_bar.setFixedHeight(28)
        self.node1_gpu_bar.setObjectName("node1_gpu_bar")
        self.node1_res_gridLayout.addWidget(self.node1_gpu_bar, 1, 1, 1, 1)

        # gpu num
        self.node1_gpu_num = QtWidgets.QLabel(self.node1_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node1_gpu_num.sizePolicy().hasHeightForWidth())
        self.node1_gpu_num.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node1_gpu_num.setFont(font)
        self.node1_gpu_num.setStyleSheet("color: rgb(255, 255, 255);")
        self.node1_gpu_num.setObjectName("node1_gpu_num")
        self.node1_res_gridLayout.addWidget(self.node1_gpu_num, 1, 2, 1, 1)
        """

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
        self.node1_res_gridLayout.addWidget(self.node1_mem_bar, 1, 1, 1, 1)

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
        self.node1_res_gridLayout.addWidget(self.node1_mem_num, 1, 3, 1, 1)

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
        self.node1_res_gridLayout.addWidget(self.node1_net_write_label, 2, 4, 1, 1)

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
        self.node1_net_name.setStyleSheet("color: rgb(255, 255, 255);")
        self.node1_net_name.setObjectName("node1_net_name")
        self.node1_res_gridLayout.addWidget(self.node1_net_name, 3, 0, 1, 1)

        # disk_read
        self.node1_net_read_value = QtWidgets.QLabel(self.node1_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node1_net_read_value.sizePolicy().hasHeightForWidth())
        self.node1_net_read_value.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node1_net_read_value.setFont(font)
        self.node1_net_read_value.setStyleSheet("color: rgb(255, 255, 255);")
        self.node1_net_read_value.setObjectName("node1_net_read_value")
        self.node1_res_gridLayout.addWidget(self.node1_net_read_value, 3, 2, 1, 1)

        # disk_write
        self.node1_net_write_value = QtWidgets.QLabel(self.node1_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node1_net_write_value.sizePolicy().hasHeightForWidth())
        self.node1_net_write_value.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node1_net_write_value.setFont(font)
        self.node1_net_write_value.setStyleSheet("color: rgb(255, 255, 255);")
        self.node1_net_write_value.setObjectName("node1_net_write_value")
        self.node1_res_gridLayout.addWidget(self.node1_net_write_value, 3, 4, 1, 1)
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
        self.node1_res_gridLayout.addWidget(self.node1_disk_write_label, 4, 4, 1, 1)

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
        self.node1_res_gridLayout.addWidget(self.node1_disk_name, 5, 0, 1, 1)

        # disk_read
        self.node1_disk_read_value = QtWidgets.QLabel(self.node1_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node1_disk_read_value.sizePolicy().hasHeightForWidth())
        self.node1_disk_read_value.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node1_disk_read_value.setFont(font)
        self.node1_disk_read_value.setStyleSheet("color: rgb(255, 255, 255);")
        self.node1_disk_read_value.setObjectName("node1_disk_read_value")
        self.node1_res_gridLayout.addWidget(self.node1_disk_read_value, 5, 2, 1, 1)

        # disk_write
        self.node1_disk_write_value = QtWidgets.QLabel(self.node1_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node1_disk_write_value.sizePolicy().hasHeightForWidth())
        self.node1_disk_write_value.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node1_disk_write_value.setFont(font)
        self.node1_disk_write_value.setStyleSheet("color: rgb(255, 255, 255);")
        self.node1_disk_write_value.setObjectName("node1_disk_write_value")
        self.node1_res_gridLayout.addWidget(self.node1_disk_write_value, 5, 4, 1, 1)

        """
        # bw
        self.bw_1 = QtWidgets.QLabel(self.node1_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.bw_1.sizePolicy().hasHeightForWidth())
        self.bw_1.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.bw_1.setFont(font)
        self.bw_1.setStyleSheet("color: rgb(255, 255, 255);")
        self.bw_1.setObjectName("bw_1")
        self.node1_res_gridLayout.addWidget(self.bw_1, 4, 0, 1, 1)

        # bw bar
        # self.bw_bar_1 = QtWidgets.QProgressBar(self.resource_1)
        # sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # sizePolicy.setHorizontalStretch(0)
        # sizePolicy.setVerticalStretch(0)
        # sizePolicy.setHeightForWidth(self.bw_bar_1.sizePolicy().hasHeightForWidth())
        # self.bw_bar_1.setSizePolicy(sizePolicy)
        # font = QtGui.QFont()
        # font.setFamily("Arial")
        # font.setPointSize(10)
        # self.bw_bar_1.setFont(font)
        # self.bw_bar_1.setStyleSheet("color: rgb(255, 255, 255);")
        # self.bw_bar_1.setProperty("value", 24)
        # self.bw_bar_1.setTextVisible(False)
        # self.bw_bar_1.setFixedHeight(28)
        # self.bw_bar_1.setObjectName("bw_bar_1")
        # self.gridLayout_1.addWidget(self.bw_bar_1, 4, 1, 1, 1)

        # bw num
        self.bw_num_1 = QtWidgets.QLabel(self.node1_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.bw_num_1.sizePolicy().hasHeightForWidth())
        self.bw_num_1.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.bw_num_1.setFont(font)
        self.bw_num_1.setStyleSheet("color: rgb(255, 255, 255);")
        self.bw_num_1.setObjectName("bw_num_1")
        self.node1_res_gridLayout.addWidget(self.bw_num_1, 4, 2, 1, 1)
        """

        self.node1_res_gridLayout.setColumnStretch(0, 3)
        self.node1_res_gridLayout.setColumnStretch(1, 8)
        self.node1_res_gridLayout.setColumnStretch(2, 2)

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
        self.node2_res_gridLayout.addWidget(self.node2_cpu_bar, 0, 1, 1, 1)

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
        self.node2_res_gridLayout.addWidget(self.node2_cpu_num, 0, 3, 1, 1)

        """
        # gpu
        self.node2_gpu_label = QtWidgets.QLabel(self.node2_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node2_gpu_label.sizePolicy().hasHeightForWidth())
        self.node2_gpu_label.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node2_gpu_label.setFont(font)
        self.node2_gpu_label.setStyleSheet("color: rgb(255, 255, 255);")
        self.node2_gpu_label.setObjectName("node2_gpu_label")
        self.node2_res_gridLayout.addWidget(self.node2_gpu_label, 1, 0, 1, 1)

        # gpu bar
        self.node2_gpu_bar = QtWidgets.QProgressBar(self.node2_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node2_gpu_bar.sizePolicy().hasHeightForWidth())
        self.node2_gpu_bar.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        self.node2_gpu_bar.setFont(font)
        self.node2_gpu_bar.setStyleSheet("color: rgb(255, 255, 255);")
        self.node2_gpu_bar.setProperty("value", 0)
        self.node2_gpu_bar.setTextVisible(False)
        self.node2_gpu_bar.setFixedHeight(28)
        self.node2_gpu_bar.setObjectName("node2_gpu_bar")
        self.node2_res_gridLayout.addWidget(self.node2_gpu_bar, 1, 1, 1, 1)

        # gpu num
        self.node2_gpu_num = QtWidgets.QLabel(self.node2_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node2_gpu_num.sizePolicy().hasHeightForWidth())
        self.node2_gpu_num.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node2_gpu_num.setFont(font)
        self.node2_gpu_num.setStyleSheet("color: rgb(255, 255, 255);")
        self.node2_gpu_num.setObjectName("node2_gpu_num")
        self.node2_res_gridLayout.addWidget(self.node2_gpu_num, 1, 2, 1, 1)
        """

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
        self.node2_res_gridLayout.addWidget(self.node2_mem_bar, 1, 1, 1, 1)

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
        self.node2_res_gridLayout.addWidget(self.node2_mem_num, 1, 3, 1, 1)

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
        self.node2_net_write_label.setObjectName("node1_net_write_label")
        self.node2_res_gridLayout.addWidget(self.node2_net_write_label, 2, 4, 1, 1)

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
        self.node2_net_name.setStyleSheet("color: rgb(255, 255, 255);")
        self.node2_net_name.setObjectName("node2_net_name")
        self.node2_res_gridLayout.addWidget(self.node2_net_name, 3, 0, 1, 1)

        # disk_read
        self.node2_net_read_value = QtWidgets.QLabel(self.node2_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node2_net_read_value.sizePolicy().hasHeightForWidth())
        self.node2_net_read_value.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node2_net_read_value.setFont(font)
        self.node2_net_read_value.setStyleSheet("color: rgb(255, 255, 255);")
        self.node2_net_read_value.setObjectName("node2_net_read_value")
        self.node2_res_gridLayout.addWidget(self.node2_net_read_value, 3, 2, 1, 1)

        # disk_write
        self.node2_net_write_value = QtWidgets.QLabel(self.node2_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node2_net_write_value.sizePolicy().hasHeightForWidth())
        self.node2_net_write_value.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node2_net_write_value.setFont(font)
        self.node2_net_write_value.setStyleSheet("color: rgb(255, 255, 255);")
        self.node2_net_write_value.setObjectName("node1_net_write_value")
        self.node2_res_gridLayout.addWidget(self.node2_net_write_value, 3, 4, 1, 1)
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
        self.node2_disk_write_label.setObjectName("node1_disk_write_label")
        self.node2_res_gridLayout.addWidget(self.node2_disk_write_label, 4, 4, 1, 1)

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
        self.node2_res_gridLayout.addWidget(self.node2_disk_name, 5, 0, 1, 1)

        # disk_read
        self.node2_disk_read_value = QtWidgets.QLabel(self.node2_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node2_disk_read_value.sizePolicy().hasHeightForWidth())
        self.node2_disk_read_value.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node2_disk_read_value.setFont(font)
        self.node2_disk_read_value.setStyleSheet("color: rgb(255, 255, 255);")
        self.node2_disk_read_value.setObjectName("node2_disk_read_value")
        self.node2_res_gridLayout.addWidget(self.node2_disk_read_value, 5, 2, 1, 1)

        # disk_write
        self.node2_disk_write_value = QtWidgets.QLabel(self.node2_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node2_disk_write_value.sizePolicy().hasHeightForWidth())
        self.node2_disk_write_value.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node2_disk_write_value.setFont(font)
        self.node2_disk_write_value.setStyleSheet("color: rgb(255, 255, 255);")
        self.node2_disk_write_value.setObjectName("node2_disk_write_value")
        self.node2_res_gridLayout.addWidget(self.node2_disk_write_value, 5, 4, 1, 1)

        """
        # bw
        self.bw_2 = QtWidgets.QLabel(self.node2_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.bw_2.sizePolicy().hasHeightForWidth())
        self.bw_2.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.bw_2.setFont(font)
        self.bw_2.setStyleSheet("color: rgb(255, 255, 255);")
        self.bw_2.setObjectName("bw_1")
        self.node2_res_gridLayout.addWidget(self.bw_2, 4, 0, 1, 1)

        # bw bar
        # self.bw_bar_2 = QtWidgets.QProgressBar(self.resource_2)
        # sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # sizePolicy.setHorizontalStretch(0)
        # sizePolicy.setVerticalStretch(0)
        # sizePolicy.setHeightForWidth(self.bw_bar_2.sizePolicy().hasHeightForWidth())
        # self.bw_bar_2.setSizePolicy(sizePolicy)
        # font = QtGui.QFont()
        # font.setFamily("Arial")
        # font.setPointSize(10)
        # self.bw_bar_2.setFont(font)
        # self.bw_bar_2.setStyleSheet("color: rgb(255, 255, 255);")
        # self.bw_bar_2.setProperty("value", 24)
        # self.bw_bar_2.setTextVisible(False)
        # self.bw_bar_2.setFixedHeight(28)
        # self.bw_bar_2.setObjectName("bw_bar_2")
        # self.gridLayout_2.addWidget(self.bw_bar_2, 4, 1, 1, 1)

        # bw num
        self.bw_num_2 = QtWidgets.QLabel(self.node2_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.bw_num_2.sizePolicy().hasHeightForWidth())
        self.bw_num_2.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.bw_num_2.setFont(font)
        self.bw_num_2.setStyleSheet("color: rgb(255, 255, 255);")
        self.bw_num_2.setObjectName("bw_num_2")
        self.node2_res_gridLayout.addWidget(self.bw_num_2, 4, 2, 1, 1)
        """

        self.node2_res_gridLayout.setColumnStretch(0, 3)
        self.node2_res_gridLayout.setColumnStretch(1, 8)
        self.node2_res_gridLayout.setColumnStretch(2, 2)

        self.node2_verticalLayout.addWidget(self.node2_resource)
        self.node2_verticalLayout.setStretch(0, 1)
        self.node2_verticalLayout.setStretch(1, 1)
        self.node2_verticalLayout.setStretch(2, 4)
        self.node2_verticalLayout.setStretch(3, 4)
        self.status_monitor_layout.addWidget(self.node2)

        self.horizontalLayout.addLayout(self.status_monitor_layout)

        # 在底部添加logo
        self.nokia_logo = QtWidgets.QLabel()
        self.nokia_logo.setPixmap(QtGui.QPixmap("../images/bell_logo.png"))
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

        self.history_cpu_1 = Queue(15000)
        self.history_cpu_2 = Queue(15000)
        self.history_cpu_3 = Queue(15000)

        self.history_delay_1 = Queue(15000)
        self.history_delay_2 = Queue(15000)
        self.history_delay_3 = Queue(15000)

        self.history1 = DataVisualizationWindow(self.history_cpu_1, self.history_delay_1, "Node1")
        self.history1.setVisible(False)

        self.history2 = DataVisualizationWindow(self.history_cpu_2, self.history_delay_2, "Node2")
        self.history2.setVisible(False)

        self.history3 = DataVisualizationWindow(self.history_cpu_3, self.history_delay_3, "Node3")
        self.history3.setVisible(False)

    def _initSpeedMeter(self):
        font = QtGui.QFont()
        font.setPointSize(15)
        font.setFamily("微软雅黑")

        self.speed_meter_1 = SpeedMeter('', '', 0, 100)
        self.layout_1 = QVBoxLayout()
        self.layout_1.addWidget(self.speed_meter_1)

        # self.workload1 = QLabel("0")
        # self.setFont(font)
        # self.workload1.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignCenter)
        # self.layout_1.addWidget(self.workload1)

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

        # self.workload2 = QLabel("0")
        # self.setFont(font)
        # self.workload2.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignCenter)
        # self.layout_2.addWidget(self.workload2)

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

        # self.workload3 = QLabel("0")
        # self.setFont(font)
        # self.workload3.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignCenter)
        # self.layout_3.addWidget(self.workload3)

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

        self.net_3.setLayout(self.layout_3)
        self.speed_meter_3.setGeometry(200, 200, 200, 200)

    def show_history1(self):
        # self.history1 = DataVisualizationWindow(self.history_cpu_1, self.history_delay_1, "Node1")
        self.history1.setVisible(True)

    def show_history2(self):
        # self.history2 = DataVisualizationWindow(self.history_cpu_2, self.history_delay_2, "Node2")
        self.history2.setVisible(True)

    def show_history3(self):
        # self.history3 = DataVisualizationWindow(self.history_cpu_3, self.history_delay_3, "Node3")
        self.history3.setVisible(True)

    def setText(self):
        self.node1_label.setText("C-Node1")
        self.node1_wl_label.setText("Workload")
        self.node1_cpu_label.setText("CPU")
        self.node1_cpu_num.setText("0.0%")
        # self.node1_gpu_label.setText("GPU")
        # self.node1_gpu_num.setText("NA")
        self.node1_mem_label.setText("MEM")
        self.node1_mem_num.setText("0.0%")
        self.node1_net_label.setText("NET I/O")
        self.node1_net_read_label.setText("Tx/s")
        self.node1_net_write_label.setText("Rx/s")
        self.node1_net_name.setText("Ethernet 6")
        self.node1_net_read_value.setText("345kb")
        self.node1_net_write_value.setText("333kb")
        self.node1_disk_label.setText("DISK")
        self.node1_disk_read_label.setText("R/s")
        self.node1_disk_write_label.setText("W/s")
        self.node1_disk_name.setText("PhysicalDrive0")
        self.node1_disk_read_value.setText("10M")
        self.node1_disk_write_value.setText("2M")
        # self.bw_1.setText("Occupied BW")
        # self.bw_num_1.setText("1000Mbps")

        self.label_2.setText("CFN-Node2")
        self.net_label_2.setText("Workload")
        self.cpu_2.setText("CPU")
        self.cpu_num_2.setText("0.0%")
        self.gpu_2.setText("GPU")
        self.gpu_num_2.setText("NA")
        self.mem_2.setText("MEM")
        self.mem_num_2.setText("0.0%")
        self.delay_2.setText("DELAY")
        self.delay_num_2.setText("0ms")
        self.bw_2.setText("Occupied BW")
        self.bw_num_2.setText("1000Mbps")
        self.label_3.setText("CFN-Node3")
        self.net_label_3.setText("Workload")

        self.cpu_3.setText("CPU")
        self.cpu_num_3.setText("0%")
        self.gpu_3.setText("GPU")
        self.gpu_num_3.setText("NA")
        self.mem_3.setText("MEM")
        self.mem_num_3.setText("0.0%")
        self.delay_3.setText("DELAY")
        self.delay_num_3.setText("0ms")
        self.bw_3.setText("Occupied BW")
        self.bw_num_3.setText("1000Mbps")

    def set_data(self, display_node_num, data):

        cpu, gpu, mem, delay, bw = data
        _translate = QtCore.QCoreApplication.translate

        eval("self.cpu_num_" + str(display_node_num) + ".setText(_translate(\"window\", str(cpu) + \"%\"))")
        eval("self.cpu_bar_" + str(display_node_num) + ".setProperty(\"value\", cpu)")
        if cpu <= 50.0:
            eval("self.cpu_bar_" + str(
                display_node_num) + ".setStyleSheet(\"QProgressBar::chunk {background-color: rgb(\" + str(int(2.55 * "
                                    "cpu * 2)) + \",\" + \"255\" + \",0);}\")")
        else:
            eval("self.cpu_bar_" + str(
                display_node_num) + ".setStyleSheet(\"QProgressBar::chunk {background-color: rgb(\" + \"255\" + \","
                                    "\" + str(int(2.55 * (100 - ((cpu - 50) * 2)))) + \",0);}\")")

        # eval("self.gpu_num_" + str(display_node_num) + ".setText(_translate(\"window\", str(gpu) + \"%\"))")
        # eval("self.gpu_bar_" + str(display_node_num) + ".setProperty(\"value\", gpu)")
        #
        # if gpu <= 50.0:
        #     eval("self.gpu_bar_" + str(
        #         display_node_num) + ".setStyleSheet(\"QProgressBar::chunk {background-color: rgb(\" + str(int(2.55 * "
        #                             "gpu * 2)) + \",\" + \"255\" + \",0);}\")")
        # else:
        #     eval("self.gpu_bar_" + str(
        #         display_node_num) + ".setStyleSheet(\"QProgressBar::chunk {background-color: rgb(\" + \"255\" + \","
        #                             "\" + str(int(2.55 * (100 - ((gpu - 50) * 2)))) + \",0);}\")")

        if mem < 1:
            mem = round(mem * 10, 1)
            eval("self.mem_num_" + str(display_node_num) + ".setText(_translate(\"window\", str(mem) + \"‰\"))")
            eval("self.mem_bar_" + str(display_node_num) + ".setProperty(\"value\", mem)")
        else:
            mem = round(mem, 1)
            eval("self.mem_num_" + str(display_node_num) + ".setText(_translate(\"window\", str(mem) + \"%\"))")
            eval("self.mem_bar_" + str(display_node_num) + ".setProperty(\"value\", mem)")

        if mem <= 50.0:
            eval("self.mem_bar_" + str(
                display_node_num) + ".setStyleSheet(\"QProgressBar::chunk {background-color: rgb(\" + str(int(2.55 * "
                                    "mem * 2)) + \",\" + \"255\" + \",0);}\")")

        else:
            eval("self.mem_bar_" + str(
                display_node_num) + ".setStyleSheet(\"QProgressBar::chunk {background-color: rgb(\" + \"255\" + \","
                                    "\" + str(int(2.55 * (100 - ((mem - 50) * 2)))) + \",0);}\")")

        eval("self.delay_num_" + str(display_node_num) + ".setText(_translate(\"window\", str(delay) + \"ms\"))")
        delay_percent = (delay / 50.0) * 100
        if delay <= 50:
            eval("self.delay_bar_" + str(display_node_num) + ".setProperty(\"value\", delay_percent)")
        else:
            eval("self.delay_bar_" + str(display_node_num) + ".setProperty(\"value\", 100)")

        # if delay <= 50:
        #     eval("self.delay_bar_" + str(
        #         display_node_num) + ".setStyleSheet(\"QProgressBar::chunk {background-color: rgb(\" + str(int(2.55 * "
        #                             "delay * 2)) + \",\" + \"255\" + \",0);}\")")
        # else:
        #     eval("self.delay_bar_" + str(
        #         display_node_num) + ".setStyleSheet(\"QProgressBar::chunk {background-color: rgb(\" + \"255\" + \","
        #                             "\" + str(int(2.55 * (100 - ((delay - 50) * 2)))) + \",0);}\")")

        if delay < 18:

            eval("self.delay_bar_" + str(
                display_node_num) + ".setStyleSheet(\"QProgressBar::chunk {background-color: rgb(\" + str(int(0*"
                                    "0)) + \",\" + \"255\" + \",0);}\")")
        elif delay < 30:
            eval("self.delay_bar_" + str(
                display_node_num) + ".setStyleSheet(\"QProgressBar::chunk {background-color: rgb(\" + str(int(255"
                                    ")) + \",\" + \"165\" + \",0);}\")")
        else:
            eval("self.delay_bar_" + str(
                display_node_num) + ".setStyleSheet(\"QProgressBar::chunk {background-color: rgb(\" + str(int(255"
                                    ")) + \",\" + \"0\" + \",0);}\")")

        # eval("self.bw_num_" + str(display_node_num) + ".setText(_translate(\"window\", str(bw) + \"Mbps\"))")
        # eval("self.bw_bar_" + str(display_node_num) + ".setProperty(\"value\", bw)")

        # if bw <= 50:
        #     eval("self.bw_bar_" + str(
        #         display_node_num) + ".setStyleSheet(\"QProgressBar::chunk {background-color: rgb(\" + str(int(2.55 * "
        #                             "bw * 2)) + \",\" + \"255\" + \",0);}\")")
        # else:
        #     eval("self.bw_bar_" + str(
        #         display_node_num) + ".setStyleSheet(\"QProgressBar::chunk {background-color: rgb(\" + \"255\" + \","
        #                             "\" + str(int(2.55 * (100 - ((bw - 50) * 2)))) + \",0);}\")")

        eval("self.speed_meter_" + str(display_node_num) + ".setSpeed(cpu)")

    def update_start(self, cfndata):
        worker1, worker2, ocp = self.read_json(cfndata)
        self.set_data(1, ocp)
        self.set_data(2, worker1)
        self.set_data(3, worker2)
        self.set_WN_Bandwidth()

    def read_json(self, cfndata):
        worker1 = []
        worker2 = []
        ocp = []

        data = cfndata['compute']

        worker1_data = data['worker1']
        worker2_data = data['worker2']
        ocp_data = data['ocp']

        cpu_w1 = worker1_data['cpu']
        tmp = (float(cpu_w1['total']) - float(cpu_w1['available'])) / (float(cpu_w1['total']) + 0.0001)
        tmp = round(tmp * 100, 1)
        worker1.append(tmp)

        gpu_w1 = worker1_data['gpu']
        # tmp = (int(gpu_w1['total']) - int(gpu_w1['available'])) / (int(gpu_w1['total']) + 0.0001)
        # tmp = round(tmp, 1) * 100
        tmp = 'NA'
        worker1.append(tmp)

        memory_w1 = worker1_data['memory']
        tmp = (int(memory_w1['total'][:-2]) - int(memory_w1['available'][:-2])) / (
                int(memory_w1['total'][:-2]) + 0.0001)
        memory = round(tmp * 100, 1)
        worker1.append(memory)

        if cfndata['network'][:-2] == "0s":
            worker1.append(16)
        else:
            try:
                worker1.append(int(float(cfndata['network'][:-2])) + random.randint(1, 2))
            except Exception as e:
                worker1.append(16)
                print(e)
        worker1.append(1000)

        cpu_w2 = worker2_data['cpu']
        tmp = (float(cpu_w2['total']) - float(cpu_w2['available'])) / (float(cpu_w2['total']) + 0.0001)
        tmp = round(tmp * 100, 1)
        worker2.append(tmp)

        gpu_w2 = worker2_data['gpu']
        # tmp = (int(gpu_w2['total']) - int(gpu_w2['available'])) / (int(gpu_w2['total']) + 0.0001)
        # tmp = round(tmp, 1) * 100
        tmp = 'NA'
        worker2.append(tmp)

        memory_w2 = worker2_data['memory']
        tmp = (int(memory_w2['total'][:-2]) - int(memory_w2['available'][:-2])) / (
                int(memory_w2['total'][:-2]) + 0.0001)
        memory = round(tmp * 100, 1)
        worker2.append(memory)

        if cfndata['network'][:-2] == "0s":
            worker2.append(15)
        else:
            try:
                worker2.append(int(float(cfndata['network'][:-2])))
            except Exception as e:
                worker2.append(15)
                print(e)
        worker2.append(1000)

        cpu_o = ocp_data['cpu']
        tmp = (float(cpu_o['total']) - float(cpu_o['available'])) / (float(cpu_o['total']) + 0.0001)
        tmp = round(tmp * 100, 1)
        ocp.append(tmp)

        gpu_o = ocp_data['gpu']
        # tmp = (int(gpu_o['total']) - int(gpu_o['available'])) / (int(gpu_o['total']) + 0.0001)
        # tmp = round(tmp, 1) * 100
        tmp = 'NA'
        ocp.append(tmp)

        memory_o = ocp_data['memory']
        tmp = (int(memory_o['total'][:-2]) - int(memory_o['available'][:-2])) / (int(memory_o['total'][:-2]) + 0.0001)
        memory = round(tmp * 100, 1)
        ocp.append(memory)

        if cfndata['network'][:-2] == "0s":
            ocp.append(10)
        else:
            try:
                # ocp.append(int(float(cfndata['network'][:-2])) - random.randint(4, 6))
                ocp.append(int(float(cfndata['network'][:-2])) - random.randint(1, 2))
            except Exception as e:
                ocp.append(10)
                print(e)
        ocp.append(1000)

        self.history_cpu_1.put(ocp[0])  # cpu1
        self.history_cpu_2.put(worker1[0])  # cpu2
        self.history_cpu_3.put(worker2[0])  # cpu3
        self.history_delay_1.put(ocp[3])  # network
        self.history_delay_2.put(worker1[3])  # network
        self.history_delay_3.put(worker2[3])  # network

        return worker1, worker2, ocp

    def set_WN1_Bandwidth(self):
        self.bw_num_2.setText("1.5Mbps")

    def unset_WN1_Bandwidth(self):
        self.bw_num_2.setText("1000Mbps")

    def set_WN_Bandwidth(self):
        bw_num_list = [self.bw_num_1, self.bw_num_2, self.bw_num_3]
        for i, bw_q in enumerate(self.nodesBandWidthList):
            if not bw_q.empty():
                bw_q = reverseQueue(bw_q)
                net_metrics = bw_q.get()  # ['tx', 'rx']
                net_metrics[0] /= 1000
                rx = net_metrics[1] / 1000
                if 0 <= rx < 0.1:
                    bw_num_list[i].setText(f"{str(round(net_metrics[1], 2))}Kbps")
                else:
                    bw_num_list[i].setText(f"{str(round(rx, 2))}Mbps")


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    window = data_v()
    window.show()
    # window.update_start()
    sys.exit(app.exec_())
