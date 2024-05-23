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
    QHeaderView, QTableWidget

from guiwidgets.exitdialog import ExitDialog
from guiwidgets.fadingpic import BlinkingPic
from guiwidgets.heatmap import HeatMap
from nodemodels.cfndemomanager import CfnDemoManager
from resourcevisiualize.resvisualize import data_visualize
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
        self._initView()
        self._initMainTitle()
        # self._initDataVisualize()
        self._initScenarioButtons()
        self.mouse = PyWinMouse.Mouse()
        self.mouse_pos_mon = repeatTimer(1, self.get_mouse_position, autostart=True)
        self.mouse_pos_mon.start()

    def _initDataVisualize(self):
        self.data_visual = data_visualize(parent=self, bw_list=self.monitor_q_net_list)
        self.data_visual.setVisible(False)

    def _resourceAwarenessShow(self):
        if self.data_visual.isVisible():
            self.data_visual.setVisible(False)
            self.data_visual.history1.setVisible(False)
            self.data_visual.history2.setVisible(False)
            self.data_visual.history3.setVisible(False)
        else:
            self.data_visual.show()

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
        self.net_compute_aware_btn.setGeometry(40, 1000, 378, 60)
        self.net_compute_aware_btn.setStyleSheet(
            "border-radius:8px;border-style:outset;border:none;background-color: {}".format(QColor(0, 45, 127).name()))
        palette = self.net_compute_aware_btn.palette()
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))  # 设置按钮上字体的颜色为红色
        self.net_compute_aware_btn.setPalette(palette)

        self.service_deploy_btn = QPushButton(parent=self)
        self.service_deploy_btn.setText("服务部署")
        self.service_deploy_btn.setFont(btn_font)
        self.service_deploy_btn.setGeometry(538, 990, 378, 60)
        self.service_deploy_btn.setStyleSheet(
            "border-radius:8px;border-style:outset;border:none;background-color: {}".format(QColor(0, 45, 127).name()))
        palette = self.service_deploy_btn.palette()
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))  # 设置按钮上字体的颜色为红色
        self.service_deploy_btn.setPalette(palette)

        self.dynamic_scheduling_btn = QPushButton(parent=self)
        self.dynamic_scheduling_btn.setText("动态调度")
        self.dynamic_scheduling_btn.setFont(btn_font)
        self.dynamic_scheduling_btn.setGeometry(1036, 990, 378, 60)
        self.dynamic_scheduling_btn.setStyleSheet(
            "border-radius:8px;border-style:outset;border:none;background-color: {}".format(QColor(0, 45, 127).name()))
        palette = self.dynamic_scheduling_btn.palette()
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))  # 设置按钮上字体的颜色为红色
        self.dynamic_scheduling_btn.setPalette(palette)

        self.net_compute_aware_btn.clicked.connect(self._resourceAwarenessShow)
        # self.service_deploy_btn.clicked.connect(self._serviceDeploymentShow)
        # self.dynamic_scheduling_btn.clicked.connect(self._switchScenario3)

        self.net_compute_aware_btn.show()
        self.service_deploy_btn.show()
        self.dynamic_scheduling_btn.show()

    def keyPressEvent(self, KEvent):
        k = KEvent.key()
        if k == QtCore.Qt.Key_R:
            self.reset()
        else:
            pass

    def get_mouse_position(self):
        x, y = self.mouse.get_mouse_pos()
        if y < 990:
            self.net_compute_aware_btn.setVisible(False)
            self.service_deploy_btn.setVisible(False)
            self.dynamic_scheduling_btn.setVisible(False)
        else:
            self.net_compute_aware_btn.setVisible(True)
            self.service_deploy_btn.setVisible(True)
            self.dynamic_scheduling_btn.setVisible(True)

    def reset(self):
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)

    configuration = DemoConfigParser("cpn_config-test.json")
    inter_process_resource_NodeMan = [(i['node_name'], Pipe()) for i in configuration.nodes]
    inter_process_resource_StatMon = [(i['monitoring_source_name'], Queue(15)) for i in configuration.monitoring_sources]  # for state_monitor_process. new Queue()

    # cfn_manager = CfnDemoManager(configuration, inter_process_resource_NodeMan, inter_process_resource_StatMon)
    # print(cfn_manager.n_nodes)
    cfn_manager = None
    mainWidget = CpnAppWindow(cfn_manager)

    mainWidget.show()
    sys.exit(app.exec())
