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


class data_visualize(QWidget):
    def __init__(self, parent=None, res_queue_dict=None):
        super().__init__()
        self._initResourceUri()
        self.updateFlag = False
        self.layout = QtWidgets.QHBoxLayout(self)
        self.setParent(parent)
        self.groupBox = QGroupBox("")
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
        self.node1_res_gridLayout.addWidget(self.node1_disk_name, 5, 0, 1, 2)

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
        self.node2_res_gridLayout.addWidget(self.node2_disk_name, 5, 0, 1, 2)

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

        self.node2_res_gridLayout.setColumnStretch(0, 3)
        self.node2_res_gridLayout.setColumnStretch(1, 8)
        self.node2_res_gridLayout.setColumnStretch(2, 2)

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
        self.node3_res_gridLayout.addWidget(self.node3_cpu_bar, 0, 1, 1, 1)

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
        self.node3_res_gridLayout.addWidget(self.node3_cpu_num, 0, 3, 1, 1)

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
        self.node3_res_gridLayout.addWidget(self.node3_mem_bar, 1, 1, 1, 1)

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
        self.node3_res_gridLayout.addWidget(self.node3_mem_num, 1, 3, 1, 1)

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
        self.node3_res_gridLayout.addWidget(self.node3_net_write_label, 2, 4, 1, 1)

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
        self.node3_net_name.setStyleSheet("color: rgb(255, 255, 255);")
        self.node3_net_name.setObjectName("node3_net_name")
        self.node3_res_gridLayout.addWidget(self.node3_net_name, 3, 0, 1, 1)

        # disk_read
        self.node3_net_read_value = QtWidgets.QLabel(self.node3_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node3_net_read_value.sizePolicy().hasHeightForWidth())
        self.node3_net_read_value.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node3_net_read_value.setFont(font)
        self.node3_net_read_value.setStyleSheet("color: rgb(255, 255, 255);")
        self.node3_net_read_value.setObjectName("node3_net_read_value")
        self.node3_res_gridLayout.addWidget(self.node3_net_read_value, 3, 2, 1, 1)

        # disk_write
        self.node3_net_write_value = QtWidgets.QLabel(self.node3_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node3_net_write_value.sizePolicy().hasHeightForWidth())
        self.node3_net_write_value.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node3_net_write_value.setFont(font)
        self.node3_net_write_value.setStyleSheet("color: rgb(255, 255, 255);")
        self.node3_net_write_value.setObjectName("node3_net_write_value")
        self.node3_res_gridLayout.addWidget(self.node3_net_write_value, 3, 4, 1, 1)
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
        self.node3_res_gridLayout.addWidget(self.node3_disk_write_label, 4, 4, 1, 1)

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
        self.node3_disk_read_value = QtWidgets.QLabel(self.node3_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node3_disk_read_value.sizePolicy().hasHeightForWidth())
        self.node3_disk_read_value.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node3_disk_read_value.setFont(font)
        self.node3_disk_read_value.setStyleSheet("color: rgb(255, 255, 255);")
        self.node3_disk_read_value.setObjectName("node3_disk_read_value")
        self.node3_res_gridLayout.addWidget(self.node3_disk_read_value, 5, 2, 1, 1)

        # disk_write
        self.node3_disk_write_value = QtWidgets.QLabel(self.node3_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node3_disk_write_value.sizePolicy().hasHeightForWidth())
        self.node3_disk_write_value.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node3_disk_write_value.setFont(font)
        self.node3_disk_write_value.setStyleSheet("color: rgb(255, 255, 255);")
        self.node3_disk_write_value.setObjectName("node3_disk_write_value")
        self.node3_res_gridLayout.addWidget(self.node3_disk_write_value, 5, 4, 1, 1)

        self.node3_res_gridLayout.setColumnStretch(0, 3)
        self.node3_res_gridLayout.setColumnStretch(1, 8)
        self.node3_res_gridLayout.setColumnStretch(2, 2)

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
        self.node4_res_gridLayout.addWidget(self.node4_cpu_bar, 0, 1, 1, 1)

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
        self.node4_res_gridLayout.addWidget(self.node4_cpu_num, 0, 3, 1, 1)

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
        self.node4_res_gridLayout.addWidget(self.node4_mem_bar, 1, 1, 1, 1)

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
        self.node4_res_gridLayout.addWidget(self.node4_mem_num, 1, 3, 1, 1)

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
        self.node4_res_gridLayout.addWidget(self.node4_net_write_label, 2, 4, 1, 1)

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
        self.node4_net_name.setStyleSheet("color: rgb(255, 255, 255);")
        self.node4_net_name.setObjectName("node4_net_name")
        self.node4_res_gridLayout.addWidget(self.node4_net_name, 3, 0, 1, 1)

        # disk_read
        self.node4_net_read_value = QtWidgets.QLabel(self.node4_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node4_net_read_value.sizePolicy().hasHeightForWidth())
        self.node4_net_read_value.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node4_net_read_value.setFont(font)
        self.node4_net_read_value.setStyleSheet("color: rgb(255, 255, 255);")
        self.node4_net_read_value.setObjectName("node4_net_read_value")
        self.node4_res_gridLayout.addWidget(self.node4_net_read_value, 3, 2, 1, 1)

        # disk_write
        self.node4_net_write_value = QtWidgets.QLabel(self.node4_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node4_net_write_value.sizePolicy().hasHeightForWidth())
        self.node4_net_write_value.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node4_net_write_value.setFont(font)
        self.node4_net_write_value.setStyleSheet("color: rgb(255, 255, 255);")
        self.node4_net_write_value.setObjectName("node4_net_write_value")
        self.node4_res_gridLayout.addWidget(self.node4_net_write_value, 3, 4, 1, 1)
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
        self.node4_res_gridLayout.addWidget(self.node4_disk_write_label, 4, 4, 1, 1)

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
        self.node4_disk_read_value = QtWidgets.QLabel(self.node4_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node4_disk_read_value.sizePolicy().hasHeightForWidth())
        self.node4_disk_read_value.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node4_disk_read_value.setFont(font)
        self.node4_disk_read_value.setStyleSheet("color: rgb(255, 255, 255);")
        self.node4_disk_read_value.setObjectName("node4_disk_read_value")
        self.node4_res_gridLayout.addWidget(self.node4_disk_read_value, 5, 2, 1, 1)

        # disk_write
        self.node4_disk_write_value = QtWidgets.QLabel(self.node4_resource)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node4_disk_write_value.sizePolicy().hasHeightForWidth())
        self.node4_disk_write_value.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.node4_disk_write_value.setFont(font)
        self.node4_disk_write_value.setStyleSheet("color: rgb(255, 255, 255);")
        self.node4_disk_write_value.setObjectName("node4_disk_write_value")
        self.node4_res_gridLayout.addWidget(self.node4_disk_write_value, 5, 4, 1, 1)

        self.node4_res_gridLayout.setColumnStretch(0, 3)
        self.node4_res_gridLayout.setColumnStretch(1, 8)
        self.node4_res_gridLayout.setColumnStretch(2, 2)

        self.node4_verticalLayout.addWidget(self.node4_resource)
        self.node4_verticalLayout.setStretch(0, 1)
        self.node4_verticalLayout.setStretch(1, 1)
        self.node4_verticalLayout.setStretch(2, 4)
        self.node4_verticalLayout.setStretch(3, 4)
        self.status_monitor_layout.addWidget(self.node4)

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
        self.history_cpu_4 = Queue(15000)

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

        self._initVariableGroup()

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

        self.node2_label.setText("C-Node2")
        self.node2_wl_label.setText("Workload")
        self.node2_cpu_label.setText("CPU")
        self.node2_cpu_num.setText("0.0%")
        self.node2_mem_label.setText("MEM")
        self.node2_mem_num.setText("0.0%")
        self.node2_net_label.setText("NET I/O")
        self.node2_net_read_label.setText("Tx/s")
        self.node2_net_write_label.setText("Rx/s")
        self.node2_net_name.setText("Ethernet 6")
        self.node2_net_read_value.setText("345kb")
        self.node2_net_write_value.setText("333kb")
        self.node2_disk_label.setText("DISK")
        self.node2_disk_read_label.setText("R/s")
        self.node2_disk_write_label.setText("W/s")
        self.node2_disk_name.setText("PhysicalDrive0")
        self.node2_disk_read_value.setText("10M")
        self.node2_disk_write_value.setText("2M")

        self.node3_label.setText("C-Node3")
        self.node3_wl_label.setText("Workload")
        self.node3_cpu_label.setText("CPU")
        self.node3_cpu_num.setText("0.0%")
        self.node3_mem_label.setText("MEM")
        self.node3_mem_num.setText("0.0%")
        self.node3_net_label.setText("NET I/O")
        self.node3_net_read_label.setText("Tx/s")
        self.node3_net_write_label.setText("Rx/s")
        self.node3_net_name.setText("Ethernet 6")
        self.node3_net_read_value.setText("345kb")
        self.node3_net_write_value.setText("333kb")
        self.node3_disk_label.setText("DISK")
        self.node3_disk_read_label.setText("R/s")
        self.node3_disk_write_label.setText("W/s")
        self.node3_disk_name.setText("PhysicalDrive0")
        self.node3_disk_read_value.setText("10M")
        self.node3_disk_write_value.setText("2M")

        self.node4_label.setText("C-Node4")
        self.node4_wl_label.setText("Workload")
        self.node4_cpu_label.setText("CPU")
        self.node4_cpu_num.setText("0.0%")
        self.node4_mem_label.setText("MEM")
        self.node4_mem_num.setText("0.0%")
        self.node4_net_label.setText("NET I/O")
        self.node4_net_read_label.setText("Tx/s")
        self.node4_net_write_label.setText("Rx/s")
        self.node4_net_name.setText("Ethernet 6")
        self.node4_net_read_value.setText("345kb")
        self.node4_net_write_value.setText("333kb")
        self.node4_disk_label.setText("DISK")
        self.node4_disk_read_label.setText("R/s")
        self.node4_disk_write_label.setText("W/s")
        self.node4_disk_name.setText("PhysicalDrive0")
        self.node4_disk_read_value.setText("10M")
        self.node4_disk_write_value.setText("2M")

    def _initResourceUri(self):
        self.node1_resource_uri = "http://127.0.0.1:8000/synthetic"
        self.node2_resource_uri = "http://127.0.0.1:8000/synthetic"
        self.node3_resource_uri = "http://127.0.0.1:8000/synthetic"

    def _initVariableGroup(self):
        self.CPU_Nums = [
            self.node1_cpu_num,
            self.node2_cpu_num,
            self.node3_cpu_num,
            self.node4_cpu_num,
        ]
        self.CPU_Bars = [
            self.node1_cpu_bar,
            self.node2_cpu_bar,
            self.node3_cpu_bar,
            self.node4_cpu_bar,
        ]
        self.CPU_SpeedMeters = [
            self.speed_meter_1,
            self.speed_meter_2,
            self.speed_meter_3,
            self.speed_meter_4,
        ]
        self.Mem_Nums = [
            self.node1_mem_num,
            self.node2_mem_num,
            self.node3_mem_num,
            self.node4_mem_num,
        ]
        self.Mem_Bars = [
            self.node1_mem_bar,
            self.node2_mem_bar,
            self.node3_mem_bar,
            self.node4_mem_bar,
        ]
        self.Net_Info = [
            [self.node1_net_read_value, self.node1_net_write_value],
            [self.node2_net_read_value, self.node2_net_write_value],
            [self.node3_net_read_value, self.node3_net_write_value],
            [self.node4_net_read_value, self.node4_net_write_value],
        ]
        self.Disk_Info = [
            [self.node1_disk_read_value, self.node1_disk_write_value],
            [self.node2_disk_read_value, self.node2_disk_write_value],
            [self.node3_disk_read_value, self.node3_disk_write_value],
            [self.node4_disk_read_value, self.node4_disk_write_value],
        ]
        self.CPU_HistoryList = [self.history_cpu_1, self.history_cpu_2, self.history_cpu_3, self.history_cpu_4]

    def update_datav(self):
        self._updateCPUInfo()
        self._updateMemInfo()
        self._updateNetInfo()
        self._updateDiskInfo()

    def _updateCPUInfo(self):
        print("_updateCPUInfo")
        CPU_Nums = [
            self.node1_cpu_num,
            self.node2_cpu_num,
            self.node3_cpu_num,
            self.node4_cpu_num,
        ]
        CPU_Bars = [
            self.node1_cpu_bar,
            self.node2_cpu_bar,
            self.node3_cpu_bar,
            self.node4_cpu_bar,
        ]
        CPU_SpeedMeters = [
            self.speed_meter_1,
            self.speed_meter_2,
            self.speed_meter_3,
            self.speed_meter_4,
        ]
        CPU_Qs = [
            self.node_res_monitor_queue_dict['c_node1_cpu_q'],
            self.node_res_monitor_queue_dict['c_node2_cpu_q'],
            self.node_res_monitor_queue_dict['c_node3_cpu_q'],
        ]
        CPU_Utilize = [0, 0, 0, 0]

        for i, cpu_q in enumerate(CPU_Qs):
            if not cpu_q.empty():
                cpu_q = reverseQueue(cpu_q)
                cpu_v = cpu_q.get()
                CPU_Utilize[i] = cpu_v[0]
        CPU_Utilize[-1] = sum(CPU_Utilize[:-1]) / len(CPU_Utilize[:-1])

        for i, cu in enumerate(CPU_Utilize):
            print(f"{i} ...cpu... {cu}")
            CPU_Nums[i].setText((str(cu) + "%"))
            CPU_SpeedMeters[i].setSpeed(cu)
            CPU_Bars[i].setProperty("value", cu)
            if cu <= 50.0:
                CPU_Bars[i].setStyleSheet(
                    "QProgressBar::chunk {background-color:rgb("f'{int(2.55 * cu * 2)}'",'255','0')}")
            else:
                CPU_Bars[i].setStyleSheet(
                    "QProgressBar::chunk {background-color:rgb("f'{int(2.55 * (100 - (cu - 50) * 2))}'",'255','0')}")
        print("_updateCPUInfo")

    def _updateMemInfo(self):
        print("_updateMemInfo")
        Mem_Nums = [
            self.node1_mem_num,
            self.node2_mem_num,
            self.node3_mem_num,
            self.node4_mem_num,
        ]
        Mem_Bars = [
            self.node1_mem_bar,
            self.node2_mem_bar,
            self.node3_mem_bar,
            self.node4_mem_bar,
        ]

        Mem_Qs = [
            self.node_res_monitor_queue_dict['c_node1_mem_q'],
            self.node_res_monitor_queue_dict['c_node2_mem_q'],
            self.node_res_monitor_queue_dict['c_node3_mem_q'],
        ]
        Mem_Utilize = [0, 0, 0, 0]

        for i, mem_q in enumerate(Mem_Qs):
            if not mem_q.empty():
                mem_q = reverseQueue(mem_q)
                mem_v = mem_q.get()
                Mem_Utilize[i] = mem_v[0]
        Mem_Utilize[-1] = sum(Mem_Utilize[:-1]) / len(Mem_Utilize[:-1])

        for i, mu in enumerate(Mem_Utilize):
            print(f"{i} ...mem... {mu}")
            Mem_Nums[i].setText((str(mu) + "%"))
            Mem_Bars[i].setProperty("value", mu)
            if mu <= 50.0:
                Mem_Bars[i].setStyleSheet(
                    "QProgressBar::chunk {background-color:rgb("f'{int(2.55 * mu * 2)}'",'255','0')}")
            else:
                Mem_Bars[i].setStyleSheet(
                    "QProgressBar::chunk {background-color:rgb("f'{int(2.55 * (100 - (mu - 50) * 2))}'",'255','0')}")
        print("_updateMemInfo")

    def _updateNetInfo(self):
        Net_Info = [
            [self.node1_net_read_value, self.node1_net_write_value],
            [self.node2_net_read_value, self.node2_net_write_value],
            [self.node3_net_read_value, self.node3_net_write_value],
            [self.node4_net_read_value, self.node4_net_write_value],
        ]
        Net_Qs = [
            self.node_res_monitor_queue_dict['c_node1_net_q'],
            self.node_res_monitor_queue_dict['c_node2_net_q'],
            self.node_res_monitor_queue_dict['c_node3_net_q'],
        ]
        Net_TxDx = [[0, 0], [0, 0], [0, 0], [0, 0]]

        for i, net_q in enumerate(Net_Qs):
            if not net_q.empty():
                net_q = reverseQueue(net_q)
                Net_TxDx[i] = net_q.get()
        tx_sum, dx_sum = sum(Net_TxDx[i][0] for i in range(3)), sum(Net_TxDx[i][1] for i in range(3))
        Net_TxDx[-1][0], Net_TxDx[-1][1] = tx_sum / 3, dx_sum / 3

        for i, net_txdx in enumerate(Net_TxDx):
            tx_tag, dx_tag = "", ""
            if (net_txdx[0] / 1000) < 1:
                tx_tag = f"{net_txdx[0]} b"
            if 1 < (net_txdx[0] / 1000) < 1000:
                tx_tag = f"{net_txdx[0] / 1000} kb"
            if 1 < (net_txdx[0] / 1000000) < 1000:
                tx_tag = f"{net_txdx[0] / 1000000} Mb"

            if (net_txdx[1] / 1000) < 1:
                dx_tag = f"{net_txdx[1]} b"
            if 1 < (net_txdx[1] / 1000) < 1000:
                dx_tag = f"{net_txdx[1] / 1000} kb"
            if 1 < (net_txdx[1] / 1000000) < 1000:
                dx_tag = f"{net_txdx[1] / 1000000} Mb"

            Net_Info[i][0].setText(tx_tag)
            Net_Info[i][1].setText(dx_tag)
        print("_updateNetInfo")

    def _updateDiskInfo(self):
        Disk_Info = [
            [self.node1_disk_read_value, self.node1_disk_write_value],
            [self.node2_disk_read_value, self.node2_disk_write_value],
            [self.node3_disk_read_value, self.node3_disk_write_value],
            [self.node4_disk_read_value, self.node4_disk_write_value],
        ]
        Disk_Qs = [
            self.node_res_monitor_queue_dict['c_node1_disk_q'],
            self.node_res_monitor_queue_dict['c_node2_disk_q'],
            self.node_res_monitor_queue_dict['c_node3_disk_q'],
        ]
        Disk_RW = [[0, 0], [0, 0], [0, 0], [0, 0]]

        for i, disk_q in enumerate(Disk_Qs):
            if not disk_q.empty():
                disk_q = reverseQueue(disk_q)
                Disk_RW[i] = disk_q.get()
        r_sum, w_sum = sum(Disk_RW[i][0] for i in range(3)), sum(Disk_RW[i][1] for i in range(3))
        Disk_RW[-1][0], Disk_RW[-1][1] = r_sum / 3, w_sum / 3

        for i, disk_rw in enumerate(Disk_RW):
            r_tag, w_tag = "", ""
            if (disk_rw[0] / 1000) < 1:
                r_tag = f"{disk_rw[0]} b"
            if 1 < (disk_rw[0] / 1000) < 1000:
                r_tag = f"{disk_rw[0] / 1000} kb"
            if 1 < (disk_rw[0] / 1000000) < 1000:
                r_tag = f"{disk_rw[0] / 1000000} Mb"

            if (disk_rw[1] / 1000) < 1:
                w_tag = f"{disk_rw[1]} b"
            if 1 < (disk_rw[1] / 1000) < 1000:
                w_tag = f"{disk_rw[1] / 1000} kb"
            if 1 < (disk_rw[1] / 1000000) < 1000:
                w_tag = f"{disk_rw[1] / 1000000} Mb"
            Disk_Info[i][0].setText(r_tag)
            Disk_Info[i][1].setText(w_tag)
        print("_updateDiskInfo")

    def requestResourceInfo(self):
        nodes_info = []
        try:
            node1_client = requests.get(url=self.node1_resource_uri)
            node2_client = requests.get(url=self.node2_resource_uri)
            node3_client = requests.get(url=self.node3_resource_uri)
            node1_info = node1_client.json()
            node2_info = node2_client.json()
            node3_info = node3_client.json()
            nodes_info = [node1_info, node2_info, node3_info]
            node4_info = {
                "cpu": sum(ni['cpu'] for ni in nodes_info) / len(nodes_info),
                "mem": sum(ni['mem'] for ni in nodes_info) / len(nodes_info),
                "disk": [
                    sum(ni['disk'][0] for ni in nodes_info) / len(nodes_info),
                    sum(ni['disk'][1] for ni in nodes_info) / len(nodes_info)
                ],
                "net": [
                    sum(ni['net'][0] for ni in nodes_info) / len(nodes_info),
                    sum(ni['net'][1] for ni in nodes_info) / len(nodes_info)
                ]
            }
            nodes_info.append(node4_info)
        except Exception as exp:
            print(f"Get Info exp: {exp}")
        finally:
            pass
        return nodes_info

    def updateSyntheticResource(self):
        syntheticResInfo = self.requestResourceInfo()
        while not (len(syntheticResInfo) == 4):
            syntheticResInfo = self.requestResourceInfo()
            sleep(2)
        for i, SRI in enumerate(syntheticResInfo):
            sleep(0.5)
            cu = SRI["cpu"]
            mu = SRI["mem"]
            tx, dx = SRI['net'][0], SRI['net'][1]
            rb, wb = SRI['disk'][0], SRI['disk'][1]
            try:
                self.CPU_HistoryList[i].put(cu)
                print("History CPU Info Stored")
                self.CPU_Nums[i].setText((str(cu) + "%"))
                self.CPU_SpeedMeters[i].setSpeed(cu)
                self.CPU_Bars[i].setProperty("value", cu)
                if cu <= 50.0:
                    self.CPU_Bars[i].setStyleSheet(
                        "QProgressBar::chunk {background-color:rgb("f'{int(2.55 * cu * 2)}'",'255','0')}")
                else:
                    self.CPU_Bars[i].setStyleSheet(
                        "QProgressBar::chunk {background-color:rgb("f'{int(2.55 * (100 - (cu - 50) * 2))}'",'255','0')}")
            except Exception as exp:
                print(f"CPU Info Updated: {exp}")
            finally:
                pass
            try:
                self.Mem_Nums[i].setText((str(mu) + "%"))
                self.Mem_Bars[i].setProperty("value", mu)
                if mu <= 50.0:
                    self.Mem_Bars[i].setStyleSheet(
                        "QProgressBar::chunk {background-color:rgb("f'{int(2.55 * mu * 2)}'",'255','0')}")
                else:
                    self.Mem_Bars[i].setStyleSheet(
                        "QProgressBar::chunk {background-color:rgb("f'{int(2.55 * (100 - (mu - 50) * 2))}'",'255','0')}")
            except Exception as exp:
                print(f"Mem Info Updated: {exp}")
            finally:
                pass

            try:
                tx_tag, dx_tag = "", ""
                if (tx / 1000) < 1:
                    tx_tag = f"{tx} b"
                elif 1 < (tx / 1000) < 1000:
                    tx_tag = f"{round(tx / 1000, 2)} kb"
                elif 1 < (tx / 1000000):
                    tx_tag = f"{round(tx / 1000000, 2)} Mb"
                if (dx / 1000) < 1:
                    dx_tag = f"{dx} b"
                elif 1 < (dx / 1000) < 1000:
                    dx_tag = f"{round(dx / 1000, 2)} kb"
                elif 1 < (dx / 1000000):
                    dx_tag = f"{round(dx / 1000000, 2)} Mb"

                self.Net_Info[i][0].setText(tx_tag)
                self.Net_Info[i][1].setText(dx_tag)
            except Exception as exp:
                print(f"Net Info Updated: {exp}")
            finally:
                pass

            try:
                r_tag, w_tag = "", ""
                if (rb / 1000) < 1:
                    r_tag = f"{rb} b"
                elif 1 < (rb / 1000) < 1000:
                    r_tag = f"{round(rb / 1000, 2)} kb"
                elif 1 < (rb / 1000000) < 1000:
                    r_tag = f"{round(rb / 1000000, 2)} Mb"
                elif 1 < (rb / 1000000000):
                    r_tag = f"{round(rb / 1000000000, 2)} Gb"

                if (wb / 1000) < 1:
                    w_tag = f"{wb} b"
                elif 1 < (wb / 1000) < 1000:
                    w_tag = f"{round(wb / 1000, 2)} kb"
                elif 1 < (wb / 1000000) < 1000:
                    w_tag = f"{round(wb / 1000000, 2)} Mb"
                elif 1 < (wb / 1000000000):
                    w_tag = f"{round(wb / 1000000000, 2)} Gb"
                self.Disk_Info[i][0].setText(r_tag)
                self.Disk_Info[i][1].setText(w_tag)
            except Exception as exp:
                print(f"Disk Info Updated: {exp}")
            finally:
                pass

    def updateNodesInfo(self):
        syntheticResInfo = self.requestResourceInfo()
        while not (len(syntheticResInfo) == 4):
            syntheticResInfo = self.requestResourceInfo()
            sleep(2)
        print(syntheticResInfo)
        self.updateNode1Info(syntheticResInfo[0])
        self.updateNode2Info(syntheticResInfo[1])
        self.updateNode3Info(syntheticResInfo[2])
        self.updateNode4Info(syntheticResInfo[3])

    def updateNode1Info(self, node1_info):
        cu = node1_info['cpu']
        mu = node1_info['mem']
        tx, dx = node1_info['net'][0], node1_info['net'][1]
        rb, wb = node1_info['disk'][0], node1_info['disk'][1]
        self.history_cpu_1.put(cu)
        self.node1_cpu_num.setText((str(cu) + "%"))
        self.speed_meter_1.setSpeed(cu)
        self.node1_cpu_bar.setProperty("value", cu)
        if cu <= 50.0:
            self.node1_cpu_bar.setStyleSheet(
                "QProgressBar::chunk {background-color:rgb("f'{int(2.55 * cu * 2)}'",'255','0')}")
        else:
            self.node1_cpu_bar.setStyleSheet(
                "QProgressBar::chunk {background-color:rgb("f'{int(2.55 * (100 - (cu - 50) * 2))}'",'255','0')}")
        self.node1_mem_num.setText((str(mu) + "%"))
        self.node1_mem_bar.setProperty("value", mu)
        if mu <= 50.0:
            self.node1_mem_bar.setStyleSheet(
                "QProgressBar::chunk {background-color:rgb("f'{int(2.55 * mu * 2)}'",'255','0')}")
        else:
            self.node1_mem_bar.setStyleSheet(
                "QProgressBar::chunk {background-color:rgb("f'{int(2.55 * (100 - (mu - 50) * 2))}'",'255','0')}")
        tx_tag, dx_tag = "", ""
        if (tx / 1000) < 1:
            tx_tag = f"{tx} b"
        elif 1 < (tx / 1000) < 1000:
            tx_tag = f"{round(tx / 1000, 2)} kb"
        elif 1 < (tx / 1000000):
            tx_tag = f"{round(tx / 1000000, 2)} Mb"
        if (dx / 1000) < 1:
            dx_tag = f"{dx} b"
        elif 1 < (dx / 1000) < 1000:
            dx_tag = f"{round(dx / 1000, 2)} kb"
        elif 1 < (dx / 1000000):
            dx_tag = f"{round(dx / 1000000, 2)} Mb"

        self.node1_net_read_value.setText(tx_tag)
        self.node1_net_write_value.setText(dx_tag)

        r_tag, w_tag = "", ""
        if (rb / 1000) < 1:
            r_tag = f"{rb} b"
        elif 1 < (rb / 1000) < 1000:
            r_tag = f"{round(rb / 1000, 2)} kb"
        elif 1 < (rb / 1000000) < 1000:
            r_tag = f"{round(rb / 1000000, 2)} Mb"
        elif 1 < (rb / 1000000000):
            r_tag = f"{round(rb / 1000000000, 2)} Gb"

        if (wb / 1000) < 1:
            w_tag = f"{wb} b"
        elif 1 < (wb / 1000) < 1000:
            w_tag = f"{round(wb / 1000, 2)} kb"
        elif 1 < (wb / 1000000) < 1000:
            w_tag = f"{round(wb / 1000000, 2)} Mb"
        elif 1 < (wb / 1000000000):
            w_tag = f"{round(wb / 1000000000, 2)} Gb"
        self.node1_disk_read_value.setText(r_tag)
        self.node1_disk_write_value.setText(w_tag)

    def updateNode2Info(self, node2_info):
        cu = node2_info['cpu']
        mu = node2_info['mem']
        tx, dx = node2_info['net'][0], node2_info['net'][1]
        rb, wb = node2_info['disk'][0], node2_info['disk'][1]
        self.history_cpu_2.put(cu)
        self.node2_cpu_num.setText((str(cu) + "%"))
        self.speed_meter_2.setSpeed(cu)
        self.node2_cpu_bar.setProperty("value", cu)
        if cu <= 50.0:
            self.node2_cpu_bar.setStyleSheet(
                "QProgressBar::chunk {background-color:rgb("f'{int(2.55 * cu * 2)}'",'255','0')}")
        else:
            self.node2_cpu_bar.setStyleSheet(
                "QProgressBar::chunk {background-color:rgb("f'{int(2.55 * (100 - (cu - 50) * 2))}'",'255','0')}")
        self.node2_mem_num.setText((str(mu) + "%"))
        self.node2_mem_bar.setProperty("value", mu)
        if mu <= 50.0:
            self.node2_mem_bar.setStyleSheet(
                "QProgressBar::chunk {background-color:rgb("f'{int(2.55 * mu * 2)}'",'255','0')}")
        else:
            self.node2_mem_bar.setStyleSheet(
                "QProgressBar::chunk {background-color:rgb("f'{int(2.55 * (100 - (mu - 50) * 2))}'",'255','0')}")
        tx_tag, dx_tag = "", ""
        if (tx / 1000) < 1:
            tx_tag = f"{tx} b"
        elif 1 < (tx / 1000) < 1000:
            tx_tag = f"{round(tx / 1000, 2)} kb"
        elif 1 < (tx / 1000000):
            tx_tag = f"{round(tx / 1000000, 2)} Mb"
        if (dx / 1000) < 1:
            dx_tag = f"{dx} b"
        elif 1 < (dx / 1000) < 1000:
            dx_tag = f"{round(dx / 1000, 2)} kb"
        elif 1 < (dx / 1000000):
            dx_tag = f"{round(dx / 1000000, 2)} Mb"

        self.node2_net_read_value.setText(tx_tag)
        self.node2_net_write_value.setText(dx_tag)

        r_tag, w_tag = "", ""
        if (rb / 1000) < 1:
            r_tag = f"{rb} b"
        elif 1 < (rb / 1000) < 1000:
            r_tag = f"{round(rb / 1000, 2)} kb"
        elif 1 < (rb / 1000000) < 1000:
            r_tag = f"{round(rb / 1000000, 2)} Mb"
        elif 1 < (rb / 1000000000):
            r_tag = f"{round(rb / 1000000000, 2)} Gb"

        if (wb / 1000) < 1:
            w_tag = f"{wb} b"
        elif 1 < (wb / 1000) < 1000:
            w_tag = f"{round(wb / 1000, 2)} kb"
        elif 1 < (wb / 1000000) < 1000:
            w_tag = f"{round(wb / 1000000, 2)} Mb"
        elif 1 < (wb / 1000000000):
            w_tag = f"{round(wb / 1000000000, 2)} Gb"
        self.node2_disk_read_value.setText(r_tag)
        self.node2_disk_write_value.setText(w_tag)

    def updateNode3Info(self, node3_info):
        cu = node3_info['cpu']
        mu = node3_info['mem']
        tx, dx = node3_info['net'][0], node3_info['net'][1]
        rb, wb = node3_info['disk'][0], node3_info['disk'][1]
        self.history_cpu_3.put(cu)
        self.node3_cpu_num.setText((str(cu) + "%"))
        self.speed_meter_3.setSpeed(cu)
        self.node3_cpu_bar.setProperty("value", cu)
        if cu <= 50.0:
            self.node3_cpu_bar.setStyleSheet(
                "QProgressBar::chunk {background-color:rgb("f'{int(2.55 * cu * 2)}'",'255','0')}")
        else:
            self.node3_cpu_bar.setStyleSheet(
                "QProgressBar::chunk {background-color:rgb("f'{int(2.55 * (100 - (cu - 50) * 2))}'",'255','0')}")
        self.node3_mem_num.setText((str(mu) + "%"))
        self.node3_mem_bar.setProperty("value", mu)
        if mu <= 50.0:
            self.node3_mem_bar.setStyleSheet(
                "QProgressBar::chunk {background-color:rgb("f'{int(2.55 * mu * 2)}'",'255','0')}")
        else:
            self.node3_mem_bar.setStyleSheet(
                "QProgressBar::chunk {background-color:rgb("f'{int(2.55 * (100 - (mu - 50) * 2))}'",'255','0')}")
        tx_tag, dx_tag = "", ""
        if (tx / 1000) < 1:
            tx_tag = f"{tx} b"
        elif 1 < (tx / 1000) < 1000:
            tx_tag = f"{round(tx / 1000, 2)} kb"
        elif 1 < (tx / 1000000):
            tx_tag = f"{round(tx / 1000000, 2)} Mb"
        if (dx / 1000) < 1:
            dx_tag = f"{dx} b"
        elif 1 < (dx / 1000) < 1000:
            dx_tag = f"{round(dx / 1000, 2)} kb"
        elif 1 < (dx / 1000000):
            dx_tag = f"{round(dx / 1000000, 2)} Mb"

        self.node3_net_read_value.setText(tx_tag)
        self.node3_net_write_value.setText(dx_tag)

        r_tag, w_tag = "", ""
        if (rb / 1000) < 1:
            r_tag = f"{rb} b"
        elif 1 < (rb / 1000) < 1000:
            r_tag = f"{round(rb / 1000, 2)} kb"
        elif 1 < (rb / 1000000) < 1000:
            r_tag = f"{round(rb / 1000000, 2)} Mb"
        elif 1 < (rb / 1000000000):
            r_tag = f"{round(rb / 1000000000, 2)} Gb"

        if (wb / 1000) < 1:
            w_tag = f"{wb} b"
        elif 1 < (wb / 1000) < 1000:
            w_tag = f"{round(wb / 1000, 2)} kb"
        elif 1 < (wb / 1000000) < 1000:
            w_tag = f"{round(wb / 1000000, 2)} Mb"
        elif 1 < (wb / 1000000000):
            w_tag = f"{round(wb / 1000000000, 2)} Gb"
        self.node3_disk_read_value.setText(r_tag)
        self.node3_disk_write_value.setText(w_tag)

    def updateNode4Info(self, node4_info):
        cu = node4_info['cpu']
        mu = node4_info['mem']
        tx, dx = node4_info['net'][0], node4_info['net'][1]
        rb, wb = node4_info['disk'][0], node4_info['disk'][1]
        self.history_cpu_4.put(cu)
        self.node4_cpu_num.setText((str(cu) + "%"))
        self.speed_meter_4.setSpeed(cu)
        self.node4_cpu_bar.setProperty("value", cu)
        if cu <= 50.0:
            self.node4_cpu_bar.setStyleSheet(
                "QProgressBar::chunk {background-color:rgb("f'{int(2.55 * cu * 2)}'",'255','0')}")
        else:
            self.node4_cpu_bar.setStyleSheet(
                "QProgressBar::chunk {background-color:rgb("f'{int(2.55 * (100 - (cu - 50) * 2))}'",'255','0')}")
        self.node4_mem_num.setText((str(mu) + "%"))
        self.node4_mem_bar.setProperty("value", mu)
        if mu <= 50.0:
            self.node4_mem_bar.setStyleSheet(
                "QProgressBar::chunk {background-color:rgb("f'{int(2.55 * mu * 2)}'",'255','0')}")
        else:
            self.node4_mem_bar.setStyleSheet(
                "QProgressBar::chunk {background-color:rgb("f'{int(2.55 * (100 - (mu - 50) * 2))}'",'255','0')}")
        tx_tag, dx_tag = "", ""
        if (tx / 1000) < 1:
            tx_tag = f"{tx} b"
        elif 1 < (tx / 1000) < 1000:
            tx_tag = f"{round(tx / 1000, 2)} kb"
        elif 1 < (tx / 1000000):
            tx_tag = f"{round(tx / 1000000, 2)} Mb"
        if (dx / 1000) < 1:
            dx_tag = f"{dx} b"
        elif 1 < (dx / 1000) < 1000:
            dx_tag = f"{round(dx / 1000, 2)} kb"
        elif 1 < (dx / 1000000):
            dx_tag = f"{round(dx / 1000000, 2)} Mb"

        self.node4_net_read_value.setText(tx_tag)
        self.node4_net_write_value.setText(dx_tag)

        r_tag, w_tag = "", ""
        if (rb / 1000) < 1:
            r_tag = f"{rb} b"
        elif 1 < (rb / 1000) < 1000:
            r_tag = f"{round(rb / 1000, 2)} kb"
        elif 1 < (rb / 1000000) < 1000:
            r_tag = f"{round(rb / 1000000, 2)} Mb"
        elif 1 < (rb / 1000000000):
            r_tag = f"{round(rb / 1000000000, 2)} Gb"

        if (wb / 1000) < 1:
            w_tag = f"{wb} b"
        elif 1 < (wb / 1000) < 1000:
            w_tag = f"{round(wb / 1000, 2)} kb"
        elif 1 < (wb / 1000000) < 1000:
            w_tag = f"{round(wb / 1000000, 2)} Mb"
        elif 1 < (wb / 1000000000):
            w_tag = f"{round(wb / 1000000000, 2)} Gb"
        self.node4_disk_read_value.setText(r_tag)
        self.node4_disk_write_value.setText(w_tag)


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    window = data_visualize()
    window.show()
    # window.update_start()
    sys.exit(app.exec_())
