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

from guiwidgets.fadingpic import BlinkingPic
from nodemodels.cfndemomanager import CfnDemoManager
from utils.HeatMap import HeatMap
from utils.configparser import DemoConfigParser
from utils.imageLoader import ImageLoader
from utils.repeatimer import repeatTimer


class ComputingPowerAwareAddressRouteWindow(QWidget):
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
        self._initHeapMap()
        self._initImageLoad()
        self.initConnections()
        # self.user_first_pkg.start("sc1_sp1")

    def _initMonitorQueue(self):
        self.monitor_q_cpu_hm_node1 = self.cfn_manager.resource_StatMon['c_node1_cpu']  # 算力节点1 CPU
        self.monitor_q_cpu_hm_node2 = self.cfn_manager.resource_StatMon['c_node2_cpu']  # 算力节点2 CPU
        self.monitor_q_cpu_hm_node3 = self.cfn_manager.resource_StatMon['c_node3_cpu']  # 算力节点3 CPU

    def _initHeapMap(self):
        self.cloud1_hm = HeatMap(parent=self, geo=[793, 405, 40, 80], interval=4000, data_q=self.monitor_q_cpu_hm_node1)
        self.cloud2_hm = HeatMap(parent=self, geo=[1058, 520, 40, 80], interval=4000,
                                 data_q=self.monitor_q_cpu_hm_node2)
        self.cloud3_hm = HeatMap(parent=self, geo=[986, 857, 40, 80], interval=4000, data_q=self.monitor_q_cpu_hm_node3)
        self.cloud1_hm.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.cloud2_hm.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.cloud3_hm.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.cloud1_hm.setVisible(True)
        self.cloud2_hm.setVisible(True)
        self.cloud3_hm.setVisible(True)
        self.cloud1_hm.timer.start()
        self.cloud2_hm.timer.start()
        self.cloud3_hm.timer.start()

    def _initView(self):
        self.setWindowTitle(" ")
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.view = QtWidgets.QGraphicsView(parent=self)
        self.view.setBackgroundBrush(QtGui.QBrush(QtGui.QImage('./images/test_scenario1_bg.png')))
        self.view.setCacheMode(QtWidgets.QGraphicsView.CacheBackground)
        self.scene = self._initScene()
        self.view.setScene(self.scene)
        self.view.setSceneRect(0, 0, 1920, 1080)
        self.view.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        self.view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setRenderHint(QtGui.QPainter.Antialiasing)
        self.view.setGeometry(0, 0, 1920, 1080)

    def _initScene(self):
        """ add all items into scene and set their initial position/visibility"""
        scene = QtWidgets.QGraphicsScene()

        c_node1_video_img = QtGui.QPixmap("./images/video_conv.png").scaled(QSize(54, 31))
        c_node2_video_img = QtGui.QPixmap("./images/video_conv.png").scaled(QSize(54, 31))
        c_node3_video_img = QtGui.QPixmap("./images/video_conv.png").scaled(QSize(54, 31))
        self.c_node1_video = BlinkingPic(parent=self, pixmap=c_node1_video_img, auto_dim=True, dim_opacity=0.1,
                                         blink_period=1200).pixmap_item
        self.c_node2_video = BlinkingPic(parent=self, pixmap=c_node2_video_img, auto_dim=True, dim_opacity=0.1,
                                         blink_period=1200).pixmap_item
        self.c_node3_video = BlinkingPic(parent=self, pixmap=c_node3_video_img, auto_dim=True, dim_opacity=0.1,
                                         blink_period=1200).pixmap_item

        scene.addItem(self.c_node1_video)
        scene.addItem(self.c_node2_video)
        scene.addItem(self.c_node3_video)

        self.c_node1_video.setPos(906, 428)
        self.c_node2_video.setPos(1140, 535)
        self.c_node3_video.setPos(1098, 840)

        self.c_node1_video.setVisible(True)
        self.c_node2_video.setVisible(True)
        self.c_node3_video.setVisible(True)

        # self.c_node1_video.start_blink()
        # self.c_node2_video.start_blink()
        # self.c_node3_video.start_blink()

        self.cloud1_hm_l1 = QtWidgets.QLabel(parent=self)
        self.cloud1_hm_l2 = QtWidgets.QLabel(parent=self)
        self.cloud1_hm_l3 = QtWidgets.QLabel(parent=self)
        self.cloud1_hm_l1.setText("0%")
        self.cloud1_hm_l2.setText("100%")
        self.cloud1_hm_l3.setText("cpu")
        self.cloud1_hm_l1.setGeometry(772, 467, 20, 10)
        self.cloud1_hm_l2.setGeometry(763, 399, 30, 10)
        self.cloud1_hm_l3.setGeometry(792, 476, 20, 20)
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
        scene.addWidget(self.cloud1_hm_l1)
        scene.addWidget(self.cloud1_hm_l2)
        scene.addWidget(self.cloud1_hm_l3)
        scene.addWidget(self.cloud2_hm_l1)
        scene.addWidget(self.cloud2_hm_l2)
        scene.addWidget(self.cloud2_hm_l3)
        scene.addWidget(self.cloud3_hm_l1)
        scene.addWidget(self.cloud3_hm_l2)
        scene.addWidget(self.cloud3_hm_l3)

        return scene

    def _initImageLoad(self):
        self.user_first_pkg = ImageLoader(parent=self, geo=[320, 450, 530, 100],
                                          image_url='./images_test3/server_addressing_step1.png',
                                          img_scale_w=530,
                                          img_scale_h=75,
                                          direction="l2r",
                                          interval=3, title='1. 首包', tag_geo=[230, 32, 100, 20])
        self.addr_request = ImageLoader(parent=self, geo=[896, 449, 443, 100],
                                        image_url='./images_test3/server_addressing_step2.png',
                                        img_scale_w=443,
                                        img_scale_h=75,
                                        direction="l2r",
                                        interval=3, title='2.寻址请求', tag_geo=[170, 32, 100, 20])
        self.net_brain_ctrl = ImageLoader(parent=self, geo=[1360, 440, 443, 100],
                                          image_url='./images_test3/server_addressing_step3.png',
                                          img_scale_w=200,
                                          img_scale_h=3,
                                          direction="l2r",
                                          interval=3, title='3.算网融合调度编排', tag_geo=[90, 0, 200, 20])
        self.net_route_ctrl = ImageLoader(parent=self, geo=[880, 550, 476, 170],
                                          image_url='./images_test3/server_addressing_step4.png',
                                          img_scale_w=475,
                                          img_scale_h=75,
                                          direction="r2l",
                                          interval=3, title='4.网络路径控制', tag_geo=[280, 20, 200, 30])
        self.video_stream = ImageLoader(parent=self, geo=[320, 460, 550, 120],
                                        image_url='./images_test3/server_addressing_step5.png',
                                        img_scale_w=550,
                                        img_scale_h=120,
                                        direction="r2l",
                                        interval=3, title='5.视频传输数据', tag_geo=[20, 80, 200, 30])

    def initConnections(self):
        self.cfn_manager.signal_emitter.QtSignals.firstPkgLat_test.connect(self.firstPkgLatWorkFlow)
        self.user_first_pkg.QtSignals.anim_over.connect(self.service_provision_anim)
        self.addr_request.QtSignals.anim_over.connect(self.service_provision_anim)
        self.net_brain_ctrl.QtSignals.anim_over.connect(self.service_provision_anim)
        self.net_route_ctrl.QtSignals.anim_over.connect(self.service_provision_anim)
        self.video_stream.QtSignals.anim_over.connect(self.service_provision_anim)

    @pyqtSlot(str)
    def service_provision_anim(self, destination: str):
        print(f"destination is: {destination}")
        if destination == "sc1_sp1":
            self.user_first_pkg.setVisible(True)
            self.addr_request.setVisible(True)
            self.addr_request.label.setVisible(True)
            self.addr_request.start("sc1_sp2")
        elif destination == "sc1_sp2":
            self.net_brain_ctrl.label.setVisible(True)
            self.net_brain_ctrl.start("sc1_sp3")
        elif destination == "sc1_sp3":
            self.net_route_ctrl.label.setVisible(True)
            self.net_route_ctrl.start("sc1_sp4")
        elif destination == "sc1_sp4":
            self.video_stream.label.setVisible(True)
            self.video_stream.start("")
        else:
            pass

    @pyqtSlot(int, str)
    def firstPkgLatWorkFlow(self, node_id, command_args):
        print("Here is firstPkgLatWorkFlow")
        self.user_first_pkg.start("sc1_sp1")
        self._sendFirstPkg2UE()
        # self.cfn_manager.send_command("c_node1", "task", "send_pkg2ue")

    def _sendFirstPkg2UE(self):
        print("Here is _sendFirstPkg2UE")
        client_host = self.cfn_manager.demo_config.get_node('client')['node_ip']
        client_host = "127.0.0.1"
        client_port = 12354
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        message = "RESPONSE FROM C-NODE1"
        sleep(0.1)
        try:
            client_socket.connect((client_host, client_port))
        except Exception as exp:
            print(f"*&&&&&&&&&&&&&&& {exp}")
            
        try:
            client_socket.sendall(message.encode())
        except Exception as exp:
            print(f"*-------------- {exp}")
        print("FirstPkg Message Sent")
        client_socket.close()
