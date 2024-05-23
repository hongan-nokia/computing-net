# -*- coding: utf-8 -*-
"""
@Time: 5/17/2024 11:26 AM
@Author: Honggang Yuan
@Email: honggang.yuan@nokia-sbell.com
Description:
"""
import socket
import sys
from multiprocessing import Pipe, Queue
from time import sleep

import PyWinMouse
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import pyqtSlot, Qt, QTimer
from PyQt5.QtGui import QPalette, QColor, QBrush, QPixmap, QIcon
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QPushButton, QLabel, QGroupBox, QVBoxLayout, QTableWidgetItem, \
    QHeaderView, QTableWidget, QWidget

from guiwidgets.exitdialog import ExitDialog
from guiwidgets.fadingpic import BlinkingPic
from guiwidgets.heatmap import HeatMap
from nodemodels.cfndemomanager import CfnDemoManager
from resourcevisiualize.resvisualize import data_visualize
from testscenes.computingpowerawareaddressroute import ComputingPowerAwareAddressRouteWindow
from utils.configparser import DemoConfigParser
from utils.repeatimer import repeatTimer


class CpnAppWindow(QtWidgets.QMainWindow):
    def __init__(self, demo_manager: CfnDemoManager):
        super().__init__()
        geo = {
            'top': 0,
            'left': 0,
            'width': 1920,
            'height': 1080}
        self.setGeometry(geo['left'], geo['top'], geo['width'], geo['height'])
        self.nokia_blue = QtGui.QColor(18, 65, 145)
        self.cfn_manager = demo_manager
        # self.node_names = demo_manager.node_names
        self.mainTitle = QtWidgets.QLabel(parent=self)
        self._initResMonitorQueue()
        self._initView()
        self._initMainTitle()
        self._initTestScenes()
        # self._initDataVisualize()
        self._initScenarioButtons()
        self.mouse = PyWinMouse.Mouse()
        self.mouse_pos_mon = repeatTimer(1, self.get_mouse_position, autostart=True)
        self.mouse_pos_mon.start()

    def _initResMonitorQueue(self):
        self.c_node1_cpu_queue = self.cfn_manager.resource_StatMon['c_node1_cpu']
        self.c_node2_cpu_queue = self.cfn_manager.resource_StatMon['c_node2_cpu']
        self.c_node2_cpu_queue = self.cfn_manager.resource_StatMon['c_node2_cpu']
        self.data_visual_queue_dict = {
            "c_node1_cpu_q": self.cfn_manager.resource_StatMon['c_node1_cpu'],
            "c_node2_cpu_q": self.cfn_manager.resource_StatMon['c_node2_cpu'],
            "c_node3_cpu_q": self.cfn_manager.resource_StatMon['c_node3_cpu'],
            "c_node1_mem_q": self.cfn_manager.resource_StatMon['c_node1_mem'],
            "c_node2_mem_q": self.cfn_manager.resource_StatMon['c_node2_mem'],
            "c_node3_mem_q": self.cfn_manager.resource_StatMon['c_node3_mem'],
            "c_node1_net_q": self.cfn_manager.resource_StatMon['c_node1_net'],
            "c_node2_net_q": self.cfn_manager.resource_StatMon['c_node2_net'],
            "c_node3_net_q": self.cfn_manager.resource_StatMon['c_node3_net'],
            "c_node1_disk_q": self.cfn_manager.resource_StatMon['c_node1_disk'],
            "c_node2_disk_q": self.cfn_manager.resource_StatMon['c_node2_disk'],
            "c_node3_disk_q": self.cfn_manager.resource_StatMon['c_node3_disk'],
        }

    def _initTestScenes(self):
        self.CPAARWidget = ComputingPowerAwareAddressRouteWindow(self, cfn_manager)
        self.CPAARWidget.setVisible(False)

    def _initDataVisualize(self):
        self.data_visual = data_visualize(parent=self, res_queue_dict=self.data_visual_queue_dict)
        self.data_visual.setVisible(False)
        print("_initDataVisualize Done ")
        # self.computing_res_mon = repeatTimer(15, self.data_visual.update_datav, autostart=True)
        # self.computing_res_mon.start()

    def _initView(self):
        self.setWindowTitle(" ")
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.view = QtWidgets.QGraphicsView(parent=self)
        self.view.setBackgroundBrush(QtGui.QBrush(QtGui.QImage('./images/main_bg_cn.png')))
        self.view.setCacheMode(QtWidgets.QGraphicsView.CacheBackground)
        self.view.setScene(QtWidgets.QGraphicsScene())
        self.view.setSceneRect(0, 0, 1920, 1080)
        self.view.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        self.view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setRenderHint(QtGui.QPainter.Antialiasing)
        self.view.setGeometry(0, 0, 1920, 1080)

    def _initMainTitle(self):
        self.mainTitle.setText("")
        font = QtGui.QFont("Arial", 30, QtGui.QFont.Bold)
        self.mainTitle.setFont(font)
        self.mainTitle.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignCenter)  # Qt.AlignRight
        palette = self.palette()
        palette.setColor(self.foregroundRole(), self.nokia_blue)
        self.mainTitle.setPalette(palette)
        self.mainTitle.setGeometry(465, 30, 965, 69)
        self.mainTitle.raise_()

    def _initScenarioButtons(self):
        btn_font = QtGui.QFont("微软雅黑", 18, QtGui.QFont.Bold)
        self.net_compute_aware_btn = QPushButton(parent=self)
        self.net_compute_aware_btn.setText("实时算网资源")
        self.net_compute_aware_btn.setFont(btn_font)
        self.net_compute_aware_btn.setGeometry(30, 1000, 378, 60)
        self.net_compute_aware_btn.setStyleSheet(
            "border-radius:8px;border-style:outset;border:none;background-color: {}".format(QColor(0, 45, 127).name()))
        palette = self.net_compute_aware_btn.palette()
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))  # 设置按钮上字体的颜色为红色
        self.net_compute_aware_btn.setPalette(palette)

        self.main_page_btn = QPushButton(parent=self)
        self.main_page_btn.setText("主页")
        self.main_page_btn.setFont(btn_font)
        self.main_page_btn.setGeometry(20, 40, 100, 60)
        self.main_page_btn.setStyleSheet(
            "border-radius:8px;border-style:outset;border:none;background-color: {}".format(QColor(0, 45, 127).name()))
        palette = self.main_page_btn.palette()
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))  # 设置按钮上字体的颜色为红色
        self.main_page_btn.setPalette(palette)

        self.test1_btn = QPushButton(parent=self)
        self.test1_btn.setText("测试一")
        self.test1_btn.setFont(btn_font)
        self.test1_btn.setGeometry(20, 110, 100, 60)
        self.test1_btn.setStyleSheet(
            "border-radius:8px;border-style:outset;border:none;background-color: {}".format(QColor(0, 45, 127).name()))
        palette = self.test1_btn.palette()
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))  # 设置按钮上字体的颜色为红色
        self.test1_btn.setPalette(palette)

        self.test2_btn = QPushButton(parent=self)
        self.test2_btn.setText("测试二")
        self.test2_btn.setFont(btn_font)
        self.test2_btn.setGeometry(20, 180, 100, 60)
        self.test2_btn.setStyleSheet(
            "border-radius:8px;border-style:outset;border:none;background-color: {}".format(QColor(0, 45, 127).name()))
        palette = self.test2_btn.palette()
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))  # 设置按钮上字体的颜色为红色
        self.test2_btn.setPalette(palette)

        self.test3_btn = QPushButton(parent=self)
        self.test3_btn.setText("测试三")
        self.test3_btn.setFont(btn_font)
        self.test3_btn.setGeometry(20, 250, 100, 60)
        self.test3_btn.setStyleSheet(
            "border-radius:8px;border-style:outset;border:none;background-color: {}".format(QColor(0, 45, 127).name()))
        palette = self.test3_btn.palette()
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))  # 设置按钮上字体的颜色为红色
        self.test3_btn.setPalette(palette)

        self.net_compute_aware_btn.show()
        self.main_page_btn.show()
        self.test1_btn.show()
        self.test2_btn.show()
        self.test3_btn.show()

        self.net_compute_aware_btn.clicked.connect(self._resourceAwarenessShow)
        self.main_page_btn.clicked.connect(self._showMainPage)
        self.test1_btn.clicked.connect(self._showTestScene1)

    def _resourceAwarenessShow(self):
        print("_resourceAwarenessShow")
        if self.data_visual.isVisible():
            print("self.data_visual.isVisible() -> True")
            self.data_visual.setVisible(False)
            self.data_visual.history1.setVisible(False)
            self.data_visual.history2.setVisible(False)
            self.data_visual.history3.setVisible(False)
        else:
            print("self.data_visual.isVisible() -> False")
            self.data_visual.setVisible(True)

    def _showMainPage(self):
        self.CPAARWidget.setVisible(False)
        print("Show Main Page")

    def _showTestScene1(self):
        self.CPAARWidget.setVisible(True)
        print("This is TestScene1")

    def keyPressEvent(self, KEvent):
        k = KEvent.key()
        if k == QtCore.Qt.Key_R:
            self.reset()
        else:
            pass

    def get_mouse_position(self):
        x, y = self.mouse.get_mouse_pos()
        if y < 900:
            self.net_compute_aware_btn.setVisible(False)
        else:
            self.net_compute_aware_btn.setVisible(True)
        if x < 100:
            self.test1_btn.setVisible(True)
            self.test2_btn.setVisible(True)
            self.test3_btn.setVisible(True)
            self.main_page_btn.setVisible(True)
        else:
            self.test1_btn.setVisible(False)
            self.test2_btn.setVisible(False)
            self.test3_btn.setVisible(False)
            self.main_page_btn.setVisible(False)

    def reset(self):
        print("This is Reset")


if __name__ == '__main__':
    app = QApplication(sys.argv)

    configuration = DemoConfigParser("cpn_config-test.json")
    inter_process_resource_NodeMan = [(i['node_name'], Pipe()) for i in configuration.nodes]
    inter_process_resource_StatMon = [(i['monitoring_source_name'], Queue(15)) for i in configuration.monitoring_sources]  # for state_monitor_process. new Queue()

    cfn_manager = CfnDemoManager(configuration, inter_process_resource_NodeMan, inter_process_resource_StatMon)
    print(cfn_manager.n_nodes)
    mainWidget = CpnAppWindow(cfn_manager)

    mainWidget.show()
    sys.exit(app.exec())
