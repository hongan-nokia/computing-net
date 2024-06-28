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
from PyQt5.QtCore import pyqtSlot, Qt, QTimer, QSize
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


class Scene31(QWidget):
    """
    服务寻址
    """
    def __init__(self, parent, demo_manager: CfnDemoManager):
        super().__init__()
        self.path = 1
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

    def _initView(self):
        self.setWindowTitle(" ")
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.view = QtWidgets.QGraphicsView(parent=self)
        self.view.setBackgroundBrush(QtGui.QBrush(QtGui.QImage('./images_test3/test_scenario31_bg.png')))
        self.view.setCacheMode(QtWidgets.QGraphicsView.CacheBackground)
        self.view.setScene(QtWidgets.QGraphicsScene())
        self.view.setSceneRect(0, 0, 1920, 1080)
        self.view.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        self.view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setRenderHint(QtGui.QPainter.Antialiasing)
        self.view.setGeometry(0, 0, 1920, 1080)

    def _initScene(self):

        c_node1_video_img = QtGui.QPixmap("./images/video_conversion.png").scaled(QSize(80, 60))
        c_node2_video_img = QtGui.QPixmap("./images/video_conversion.png").scaled(QSize(80, 60))
        c_node3_video_img = QtGui.QPixmap("./images/video_conversion.png").scaled(QSize(80, 60))
        self.c_node1_video = BlinkingPic(parent=self, pixmap=c_node1_video_img, auto_dim=True, dim_opacity=0.1,
                                         blink_period=1200).pixmap_item
        self.c_node2_video = BlinkingPic(parent=self, pixmap=c_node2_video_img, auto_dim=True, dim_opacity=0.1,
                                         blink_period=1200).pixmap_item
        self.c_node3_video = BlinkingPic(parent=self, pixmap=c_node3_video_img, auto_dim=True, dim_opacity=0.1,
                                         blink_period=1200).pixmap_item

        self.view.scene().addItem(self.c_node1_video)
        self.view.scene().addItem(self.c_node2_video)
        self.view.scene().addItem(self.c_node3_video)

        self.c_node1_video.setPos(886, 428)
        self.c_node2_video.setPos(1140, 535)
        self.c_node3_video.setPos(1088, 860)

        self.c_node1_video.setVisible(True)
        self.c_node2_video.setVisible(True)
        self.c_node3_video.setVisible(True)

        self.cloud1_hm_l1 = QtWidgets.QLabel(parent=self)
        self.cloud1_hm_l2 = QtWidgets.QLabel(parent=self)
        self.cloud1_hm_l3 = QtWidgets.QLabel(parent=self)
        self.cloud1_hm_l1.setText("0%")
        self.cloud1_hm_l2.setText("100%")
        self.cloud1_hm_l3.setText("CPU")
        self.cloud1_hm_l1.setGeometry(772, 467, 20, 10)
        self.cloud1_hm_l2.setGeometry(763, 399, 30, 10)
        self.cloud1_hm_l3.setGeometry(792, 476, 20, 20)
        self.cloud2_hm_l1 = QtWidgets.QLabel(parent=self)
        self.cloud2_hm_l2 = QtWidgets.QLabel(parent=self)
        self.cloud2_hm_l3 = QtWidgets.QLabel(parent=self)
        self.cloud2_hm_l1.setText("0%")
        self.cloud2_hm_l2.setText("100%")
        self.cloud2_hm_l3.setText("CPU")
        self.cloud2_hm_l1.setGeometry(1037, 582, 20, 10)
        self.cloud2_hm_l2.setGeometry(1027, 514, 30, 10)
        self.cloud2_hm_l3.setGeometry(1055, 592, 20, 20)
        self.cloud3_hm_l1 = QtWidgets.QLabel(parent=self)
        self.cloud3_hm_l2 = QtWidgets.QLabel(parent=self)
        self.cloud3_hm_l3 = QtWidgets.QLabel(parent=self)
        self.cloud3_hm_l1.setText("0%")
        self.cloud3_hm_l2.setText("100%")
        self.cloud3_hm_l3.setText("CPU")
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

        self.backBtn = QPushButton(self)
        self.backBtn.setStyleSheet("background-color: rgba(240, 240, 240, 0);")
        self.backBtn.setGeometry(460, 60, 1000, 150)
        self.backBtn.clicked.connect(self.backTest3)
        self.view.scene().addWidget(self.backBtn)

    def _initMonitorQueue(self):
        self.monitor_q_cpu_hm_node1 = self.cfn_manager.resource_StatMon['c_node1_cpu']  # 算力节点1 CPU
        self.monitor_q_cpu_hm_node2 = self.cfn_manager.resource_StatMon['c_node2_cpu']  # 算力节点2 CPU
        self.monitor_q_cpu_hm_node3 = self.cfn_manager.resource_StatMon['c_node3_cpu']  # 算力节点3 CPU

    def _initHeapMap(self):
        self.cloud1_hm = HeatMap(parent=self, geo=[793, 405, 40, 80], interval=1500, data_q=self.monitor_q_cpu_hm_node1)
        self.cloud2_hm = HeatMap(parent=self, geo=[1058, 520, 40, 80], interval=1500, data_q=self.monitor_q_cpu_hm_node2)
        self.cloud3_hm = HeatMap(parent=self, geo=[986, 857, 40, 80], interval=1500, data_q=self.monitor_q_cpu_hm_node3)
        self.cloud1_hm.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.cloud2_hm.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.cloud3_hm.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.cloud1_hm.setVisible(True)
        self.cloud2_hm.setVisible(True)
        self.cloud3_hm.setVisible(True)

    def _initImageLoad(self):
        # -------------------------------------- Scenario_0 --------------------------------------
        self.service_step1 = ImageLoader(parent=self, geo=[320, 450, 530, 100],
                                         image_url='./images_test3/server_addressing_step1.png',
                                         img_scale_w=530,
                                         img_scale_h=75,
                                         direction="l2r",
                                         interval=3, title='1.服务寻址请求', tag_geo=[180, 32, 300, 20])
        self.service_step1.tag_label.setStyleSheet("color: red;")
        self.service_step2 = ImageLoader(parent=self, geo=[896, 449, 443, 100],
                                         image_url='./images_test3/server_addressing_step2.png',
                                         img_scale_w=443,
                                         img_scale_h=75,
                                         direction="l2r",
                                         interval=3, title='2.寻址请求', tag_geo=[170, 32, 150, 20])
        self.service_step3 = ImageLoader(parent=self, geo=[1360, 440, 443, 100],
                                         image_url='./images_test3/server_addressing_step3.png',
                                         img_scale_w=200,
                                         img_scale_h=3,
                                         direction="l2r",
                                         interval=3, title='3.算网融合调度编排', tag_geo=[90, 0, 200, 20])
        self.service_step41 = ImageLoader(parent=self, geo=[880, 550, 476, 170],
                                          image_url='./images_test3/server_addressing_step41.png',
                                          img_scale_w=475,
                                          img_scale_h=75,
                                          direction="r2l",
                                          interval=3, title='4.网络路径控制', tag_geo=[280, 20, 200, 30])
        self.service_step42 = ImageLoader(parent=self, geo=[1050, 615, 340, 180],
                                          image_url='./images_test3/server_addressing_step42.png',
                                          img_scale_w=340,
                                          img_scale_h=180,
                                          direction="r2l",
                                          interval=3, title='4.网络路径控制', tag_geo=[160, 120, 200, 30])
        self.service_step43 = ImageLoader(parent=self, geo=[1050, 615, 340, 180],
                                          image_url='./images_test3/server_addressing_step43.png',
                                          img_scale_w=340,
                                          img_scale_h=180,
                                          direction="r2l",
                                          interval=3, title='4.网络路径控制', tag_geo=[160, 120, 200, 30])
        self.service_step51 = ImageLoader(parent=self, geo=[320, 460, 550, 120],
                                          image_url='./images_test3/server_addressing_step51.png',
                                          img_scale_w=550,
                                          img_scale_h=120,
                                          direction="r2l",
                                          interval=3, title='5.视频传输数据', tag_geo=[20, 80, 200, 30])
        # self.service_step51.tag_label.setStyleSheet("color: rgb(224,61,205);")
        self.service_step52 = ImageLoader(parent=self, geo=[340, 525, 800, 275],
                                          image_url='./images_test3/server_addressing_step52.png',
                                          img_scale_w=800,
                                          img_scale_h=275,
                                          direction="r2l",
                                          interval=3, title='5.视频传输数据', tag_geo=[20, 10, 200, 30])
        # self.service_step52.tag_label.setStyleSheet("color: rgb(224,61,205);")
        self.service_step53 = ImageLoader(parent=self, geo=[340, 525, 750, 350],
                                          image_url='./images_test3/server_addressing_step53.png',
                                          img_scale_w=750,
                                          img_scale_h=350,
                                          direction="r2l",
                                          interval=3, title='5.视频传输数据', tag_geo=[20, 10, 200, 30])
        # self.service_step53.tag_label.setStyleSheet("color: rgb(224,61,205);")

    def initConnections(self):
        self.cfn_manager.signal_emitter.QtSignals.serviceAddr_test.connect(self.serviceAddressWorkFlow)
        self.service_step1.QtSignals.anim_over.connect(self.service_provision_anim)
        self.service_step2.QtSignals.anim_over.connect(self.service_provision_anim)
        self.service_step3.QtSignals.anim_over.connect(self.service_provision_anim)
        self.service_step41.QtSignals.anim_over.connect(self.service_provision_anim)
        self.service_step42.QtSignals.anim_over.connect(self.service_provision_anim)
        self.service_step43.QtSignals.anim_over.connect(self.service_provision_anim)
        self.service_step51.QtSignals.anim_over.connect(self.service_provision_anim)
        self.service_step52.QtSignals.anim_over.connect(self.service_provision_anim)
        self.service_step53.QtSignals.anim_over.connect(self.service_provision_anim)

    @pyqtSlot(str)
    def service_provision_anim(self, destination: str):
        # self.queueFlag = 1
        if destination == "sp1":
            # self.service_step2.label.setVisible(True)
            self.service_step2.start("sp2")
        elif destination == "sp2":
            self.service_step3.tag_label.setVisible(True)
            # self.service_step3.label.setVisible(True)
            self.service_step3.start("sp3")
        elif destination == "sp3":
            temp1 = self.cloud1_hm.index
            temp2 = self.cloud2_hm.index
            temp3 = self.cloud3_hm.index

            temps = [temp1, temp2, temp3]
            self.path = temps.index(min(temps)) + 1
            # self.path = 3
            if self.path == 1:
                # self.service_step41.label.setVisible(True)
                self.service_step41.start("sp4")
            elif self.path == 2:
                # self.service_step42.label.setVisible(True)
                self.service_step42.start("sp4")
            elif self.path == 3:
                # self.service_step43.label.setVisible(True)
                self.service_step43.start("sp4")

        elif destination == "sp4":
            if self.path == 1:
                # self.service_step51.label.setVisible(True)
                self.service_step51.start("sp5")
                self.cfn_manager.send_command('c_node1', 'task', 'vlcc worldCup.mp4_0')
                self.c_node1_video.start_blink()
            elif self.path == 2:
                # self.service_step52.label.setVisible(True)
                self.service_step52.start("sp5")
                self.cfn_manager.send_command('c_node2', 'task', 'vlcc worldCup.mp4_0')
                self.c_node2_video.start_blink()
            elif self.path == 3:
                # self.service_step53.label.setVisible(True)
                self.service_step53.start("sp5")
                self.cfn_manager.send_command('c_node3', 'task', 'vlcc worldCup.mp4_0')
                self.c_node3_video.start_blink()
        else:
            pass

    @pyqtSlot(int, str)
    def serviceAddressWorkFlow(self):
        self.reset()
        self.start_timer()
        self.service_step1.start("sp1")

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
        self.cfn_manager.send_command('c_node1', 'stop_task', 'vlcc worldCup.mp4_0')
        self.cfn_manager.send_command('c_node2', 'stop_task', 'vlcc worldCup.mp4_0')
        self.cfn_manager.send_command('c_node3', 'stop_task', 'vlcc worldCup.mp4_0')
        self.service_step1.tag_label.setVisible(False)
        self.service_step2.tag_label.setVisible(False)
        self.service_step3.tag_label.setVisible(False)
        self.service_step53.tag_label.setVisible(False)
        self.service_step41.tag_label.setVisible(False)
        self.service_step42.tag_label.setVisible(False)
        self.service_step43.tag_label.setVisible(False)
        self.service_step51.tag_label.setVisible(False)
        self.service_step52.tag_label.setVisible(False)
        self.service_step1.label.setVisible(False)
        self.service_step2.label.setVisible(False)
        self.service_step3.label.setVisible(False)
        self.service_step41.label.setVisible(False)
        self.service_step42.label.setVisible(False)
        self.service_step43.label.setVisible(False)
        self.service_step51.label.setVisible(False)
        self.service_step52.label.setVisible(False)
        self.service_step53.label.setVisible(False)

        self.stop_timer()
