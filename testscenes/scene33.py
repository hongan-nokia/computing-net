# -*- coding: utf-8 -*-
"""
@Time: 5/23/2024 8:48 PM
@Author: Honggang Yuan
@Email: honggang.yuan@nokia-sbell.com
Description:
"""
import socket
import sys
from multiprocessing import Pipe, Queue
from time import sleep

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import pyqtSlot, Qt, QTimer
from PyQt5.QtGui import QPalette, QColor, QBrush, QPixmap, QIcon
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QPushButton, QLabel, QGroupBox, QVBoxLayout, QTableWidgetItem, \
    QHeaderView, QTableWidget, QWidget

from guiwidgets.exitdialog import ExitDialog
from guiwidgets.fadingpic import BlinkingPic
from nodemodels.cfndemomanager import CfnDemoManager
from resourcevisiualize.resvisualize import data_visualize
from utils.configparser import DemoConfigParser
from utils.repeatimer import repeatTimer

from utils.HeatMap import HeatMap
from utils.imageLoader import ImageLoader


class Scene33(QWidget):
    """
    内容寻址
    """

    def __init__(self, parent, demo_manager: CfnDemoManager):
        super().__init__()
        geo = {
            'top': 0,
            'left': 0,
            'width': 1920,
            'height': 1080}
        self.setGeometry(geo['left'], geo['top'], geo['width'], geo['height'])
        self.nokia_blue = QtGui.QColor(18, 65, 145)
        self.cfn_manager = demo_manager
        self.setParent(parent)
        self._initMonitorQueue()
        self._initView()
        self._initScene()
        self._initHeapMap()
        self._initImageLoad()
        self.initConnections()

        self.path = 1
        self.commomd = None

    def _initView(self):
        self.setWindowTitle(" ")
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.view = QtWidgets.QGraphicsView(parent=self)
        self.view.setBackgroundBrush(QtGui.QBrush(QtGui.QImage('./images_test3/test_scenario33_bg.png')))
        self.view.setCacheMode(QtWidgets.QGraphicsView.CacheBackground)
        self.view.setScene(QtWidgets.QGraphicsScene())
        self.view.setSceneRect(0, 0, 1920, 1080)
        self.view.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        self.view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setRenderHint(QtGui.QPainter.Antialiasing)
        self.view.setGeometry(0, 0, 1920, 1080)

    def _initScene(self):
        self.cloud1_hm_l1 = QtWidgets.QLabel(parent=self)
        self.cloud1_hm_l2 = QtWidgets.QLabel(parent=self)
        self.cloud1_hm_l3 = QtWidgets.QLabel(parent=self)
        self.cloud1_hm_l1.setText("0%")
        self.cloud1_hm_l2.setText("100%")
        self.cloud1_hm_l3.setText("cpu")
        self.cloud1_hm_l1.setGeometry(772, 427, 20, 10)
        self.cloud1_hm_l2.setGeometry(763, 359, 30, 10)
        self.cloud1_hm_l3.setGeometry(792, 436, 20, 20)
        self.cloud2_hm_l1 = QtWidgets.QLabel(parent=self)
        self.cloud2_hm_l2 = QtWidgets.QLabel(parent=self)
        self.cloud2_hm_l3 = QtWidgets.QLabel(parent=self)
        self.cloud2_hm_l1.setText("0%")
        self.cloud2_hm_l2.setText("100%")
        self.cloud2_hm_l3.setText("cpu")
        self.cloud2_hm_l1.setGeometry(1037, 582, 20, 10)
        self.cloud2_hm_l2.setGeometry(1027, 514, 30, 10)
        self.cloud2_hm_l3.setGeometry(1055, 592, 20, 20)
        self.cloud3_hm_l1 = QtWidgets.QLabel(parent=self)
        self.cloud3_hm_l2 = QtWidgets.QLabel(parent=self)
        self.cloud3_hm_l3 = QtWidgets.QLabel(parent=self)
        self.cloud3_hm_l1.setText("0%")
        self.cloud3_hm_l2.setText("100%")
        self.cloud3_hm_l3.setText("cpu")
        self.cloud3_hm_l1.setGeometry(965, 912, 20, 10)
        self.cloud3_hm_l2.setGeometry(955, 852, 30, 10)
        self.cloud3_hm_l3.setGeometry(985, 928, 20, 20)
        self.view.scene().addWidget(self.cloud1_hm_l1)
        self.view.scene().addWidget(self.cloud1_hm_l2)
        self.view.scene().addWidget(self.cloud1_hm_l3)
        self.view.scene().addWidget(self.cloud2_hm_l1)
        self.view.scene().addWidget(self.cloud2_hm_l2)
        self.view.scene().addWidget(self.cloud2_hm_l3)
        self.view.scene().addWidget(self.cloud3_hm_l1)
        self.view.scene().addWidget(self.cloud3_hm_l2)
        self.view.scene().addWidget(self.cloud3_hm_l3)

        self.backBtn = QPushButton()
        self.backBtn.setStyleSheet("background-color: rgba(240, 240, 240, 0);")
        self.backBtn.setGeometry(460, 60, 1000, 150)
        self.backBtn.clicked.connect(self.backTest3)
        self.view.scene().addWidget(self.backBtn)

        font1 = QtGui.QFont("微软雅黑", 11)
        self.step1_label1 = QtWidgets.QLabel(parent=self)
        self.step1_label1.setText("房间1的监控")
        self.step1_label1.setWordWrap(True)
        self.step1_label1.setGeometry(587, 446, 110, 50)
        self.step1_label1.setFont(font1)
        self.view.scene().addWidget(self.step1_label1)
        self.step1_label1.setVisible(False)

        # font2 = QtGui.QFont("微软雅黑", 14)
        # self.step1_label2 = QtWidgets.QLabel(parent=self)
        # self.step1_label2.setText("寻址请求")
        # self.step1_label2.setWordWrap(True)
        # self.step1_label2.setGeometry(921, 500, 110, 50)
        # self.step1_label2.setFont(font2)
        # self.view.scene().addWidget(self.step1_label2)
        # self.step1_label2.setVisible(False)

    def _initMonitorQueue(self):
        self.monitor_q_cpu_hm_node1 = self.cfn_manager.resource_StatMon['c_node1_cpu']  # 算力节点1 CPU
        self.monitor_q_cpu_hm_node2 = self.cfn_manager.resource_StatMon['c_node2_cpu']  # 算力节点2 CPU
        self.monitor_q_cpu_hm_node3 = self.cfn_manager.resource_StatMon['c_node3_cpu']  # 算力节点3 CPU

    def _initHeapMap(self):
        self.cloud1_hm = HeatMap(parent=self, geo=[793, 365, 40, 80], interval=1500, data_q=self.monitor_q_cpu_hm_node1)
        self.cloud2_hm = HeatMap(parent=self, geo=[1058, 520, 40, 80], interval=1500,
                                 data_q=self.monitor_q_cpu_hm_node2)
        self.cloud3_hm = HeatMap(parent=self, geo=[986, 857, 40, 80], interval=1500, data_q=self.monitor_q_cpu_hm_node3)
        self.cloud1_hm.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.cloud2_hm.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.cloud3_hm.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.cloud1_hm.setVisible(True)
        self.cloud2_hm.setVisible(True)
        self.cloud3_hm.setVisible(True)

    def _initImageLoad(self):
        # -------------------------------------- Scenario_0 --------------------------------------
        self.service_step1 = ImageLoader(parent=self, geo=[325, 450, 1040, 130],
                                         image_url='./images_test3/content_addressing_step1.png',
                                         img_scale_w=1040,
                                         img_scale_h=130,
                                         direction="l2r",
                                         interval=3, title='1.寻址请求', tag_geo=[130, 30, 150, 20])
        self.service_step2 = ImageLoader(parent=self, geo=[1360, 390, 443, 150],
                                         image_url='./images_test3/content_power_addressing_step2.png',
                                         img_scale_w=200,
                                         img_scale_h=1,
                                         direction="l2r",
                                         interval=3, title='2.寻址内容，最优路径计算', tag_geo=[35, 0, 303, 120])
        self.service_step3 = ImageLoader(parent=self, geo=[720, 530, 650, 240],
                                         image_url='./images_test3/content_addressing_step3.png',
                                         img_scale_w=650,
                                         img_scale_h=240,
                                         direction="r2l",
                                         interval=3, title='3.网络路径控制', tag_geo=[420, 75, 400, 20])
        self.service_step41 = ImageLoader(parent=self, geo=[350, 550, 530, 310],
                                         image_url='./images_test3/content_addressing_step41.png',
                                         img_scale_w=530,
                                         img_scale_h=260,
                                         direction="l2r",
                                         interval=3, title='', tag_geo=[280, 20, 200, 30])
        self.service_step42 = ImageLoader(parent=self, geo=[350, 480, 730, 400],
                                         image_url='./images_test3/content_addressing_step42.png',
                                         img_scale_w=730,
                                         img_scale_h=400,
                                         direction="r2l",
                                         interval=3, title='', tag_geo=[280, 20, 200, 30])
        self.service_step43 = ImageLoader(parent=self, geo=[340, 525, 830, 350],
                                          image_url='./images_test3/content_addressing_step43.png',
                                          img_scale_w=830,
                                          img_scale_h=350,
                                          direction="r2l",
                                          interval=3, title='', tag_geo=[280, 20, 200, 30])
        self.service_step5 = ImageLoader(parent=self, geo=[340, 517, 539, 310],
                                         image_url='./images_test3/content_addressing_step5.png',
                                         img_scale_w=540,
                                         img_scale_h=35,
                                         direction="r2l",
                                         interval=3, title='', tag_geo=[280, 20, 200, 30])

    def initConnections(self):
        self.cfn_manager.signal_emitter.QtSignals.contentAddr_test.connect(self.contentAddressWorkFlow)
        self.cfn_manager.signal_emitter.QtSignals.contentAddr_test_video.connect(self.contentAddressVideoWorkFlow)
        self.service_step1.QtSignals.anim_over.connect(self.service_provision_anim)
        self.service_step2.QtSignals.anim_over.connect(self.service_provision_anim)
        self.service_step3.QtSignals.anim_over.connect(self.service_provision_anim)
        self.service_step41.QtSignals.anim_over.connect(self.service_provision_anim)
        self.service_step42.QtSignals.anim_over.connect(self.service_provision_anim)
        self.service_step5.QtSignals.anim_over.connect(self.service_provision_anim)

    @pyqtSlot(int, str)
    def contentAddressWorkFlow(self):
        self.reset()
        self.start_timer()
        self.path = 1
        self.service_step1.start("sp1")

    @pyqtSlot(int, str, str, str)
    def contentAddressVideoWorkFlow(self, Node_id, commond_arg1, commond_arg2, commond_arg3):
        print("in video workflow")
        print(Node_id)
        print(commond_arg1)
        print(commond_arg2)
        print(commond_arg3)
        self.reset()
        self.start_timer()
        self.path = 2
        self.video_name = commond_arg2
        self.video_startTime = commond_arg3
        self.service_step1.start("sp1")

    @pyqtSlot(str)
    def service_provision_anim(self, destination: str):
        if destination == "sp1":
            if self.path == 1:
                self.step1_label1.setText("房间1的监控")
            elif self.path == 2:
                self.step1_label1.setText("视频流")
            self.step1_label1.setVisible(True)
            # self.service_step2.label.setVisible(True)
            self.service_step2.start("sp2")
        elif destination == "sp2":
            # self.service_step3.label.setVisible(True)
            self.service_step3.start("sp3")
        elif destination == "sp3":
            # self.service_step4.label.setVisible(True)
            if self.path == 1:
                self.service_step41.start("sp4")
            elif self.path == 2:
                video_totaltime = 6776
                ratio = int(self.video_startTime) / video_totaltime
                if self.video_name == "足球":
                    self.commomd = f"vlc fake1-WorldCup.mp4_{ratio}"
                    self.cfn_manager.send_command('c_node3', 'task', self.commomd)
                    self.service_step42.start("")
                elif self.video_name == "游戏":
                    self.commomd = f"vlc fake3-game.mp4_{ratio}"
                    self.cfn_manager.send_command('c_node2', 'task', self.commomd)
                    self.service_step43.start("")
        elif destination == "sp4":
            self.cfn_manager.send_command('monitor_client', 'task', 'surveillance up')
            self.service_step5.start("")
        else:
            pass

    def backTest3(self):
        self.setVisible(False)
        self.parent().scene3.setVisible(True)

    def start_timer(self):
        self.cloud1_hm.timer.start()
        self.cloud2_hm.timer.start()
        self.cloud3_hm.timer.start()

    def stop_timer(self):
        self.cloud1_hm.timer.stop()
        self.cloud2_hm.timer.stop()
        self.cloud3_hm.timer.stop()

    def reset(self):
        self.service_step1.tag_label.setVisible(False)
        self.service_step2.tag_label.setVisible(False)
        self.service_step3.tag_label.setVisible(False)
        self.service_step41.tag_label.setVisible(False)
        self.service_step42.tag_label.setVisible(False)
        self.service_step43.tag_label.setVisible(False)
        self.service_step5.tag_label.setVisible(False)

        self.service_step1.label.setVisible(False)
        self.service_step2.label.setVisible(False)
        self.service_step3.label.setVisible(False)
        self.service_step41.label.setVisible(False)
        self.service_step42.label.setVisible(False)
        self.service_step43.label.setVisible(False)
        self.service_step5.label.setVisible(False)
        self.cfn_manager.send_command('monitor_client', 'stop_task', 'surveillance up')
        self.cfn_manager.send_command('c_node3', 'stop_task', self.commomd)
        self.cfn_manager.send_command('c_node2', 'stop_task', self.commomd)
        self.step1_label1.setVisible(False)

        self.stop_timer()