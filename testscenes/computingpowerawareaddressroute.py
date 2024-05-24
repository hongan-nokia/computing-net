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

import PyWinMouse
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import pyqtSlot, Qt, QTimer
from PyQt5.QtGui import QPalette, QColor, QBrush, QPixmap, QIcon
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QPushButton, QLabel, QGroupBox, QVBoxLayout, QTableWidgetItem, \
    QHeaderView, QTableWidget, QWidget

from guiwidgets.exitdialog import ExitDialog
from guiwidgets.fadingpic import BlinkingPic, FadingMovingPixmap
from guiwidgets.heatmap import HeatMap
from nodemodels.cfndemomanager import CfnDemoManager
from resourcevisiualize.resvisualize import data_visualize
from utils.configparser import DemoConfigParser
from utils.imageLoader import ImageLoader
from utils.repeatimer import repeatTimer


class ComputingPowerAwareAddressRouteWindow(QWidget):
    def __init__(self, parent, demo_manager):
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
        self._initView()
        self._initImageLoad()

    def _initView(self):
        self.setWindowTitle(" ")
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.view = QtWidgets.QGraphicsView(parent=self)
        self.view.setBackgroundBrush(QtGui.QBrush(QtGui.QImage('./images/test_scenario1_bg.png')))
        self.view.setCacheMode(QtWidgets.QGraphicsView.CacheBackground)
        self.view.setScene(QtWidgets.QGraphicsScene())
        self.view.setSceneRect(0, 0, 1920, 1080)
        self.view.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        self.view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setRenderHint(QtGui.QPainter.Antialiasing)
        self.view.setGeometry(0, 0, 1920, 1080)

    def _initScene(self):
        """ add all items into scene and set their initial position/visibility"""
        scene = QtWidgets.QGraphicsScene()

        self.c_node1_video = BlinkingPic(parent=self, pixmap=QtGui.QPixmap("./images/video_conv.png"), auto_dim=True, dim_opacity=0.1, blink_period=500).pixmap_item
        self.c_node2_video = BlinkingPic(parent=self, pixmap=QtGui.QPixmap("./images/video_conv.png"), auto_dim=True, dim_opacity=0.1, blink_period=500).pixmap_item
        self.c_node3_video = BlinkingPic(parent=self, pixmap=QtGui.QPixmap("./images/video_conv.png"), auto_dim=True, dim_opacity=0.1, blink_period=500).pixmap_item

        scene.addItem(self.c_node1_video)
        scene.addItem(self.c_node2_video)
        scene.addItem(self.c_node3_video)

        self.c_node1_video.setPos(906, 428)
        self.c_node2_video.setPos(1140, 529)
        self.c_node3_video.setPos(1068, 840)

        self.c_node1_video.setVisible(True)
        self.c_node1_video.setVisible(True)
        self.c_node1_video.setVisible(True)

        self.c_node1_video.start_blink()
        self.c_node1_video.start_blink()
        self.c_node1_video.start_blink()

        self.cloud1_hm_l1 = QtWidgets.QLabel(parent=self)
        self.cloud1_hm_l2 = QtWidgets.QLabel(parent=self)
        self.cloud1_hm_l3 = QtWidgets.QLabel(parent=self)
        self.cloud1_hm_l1.setText("0%")
        self.cloud1_hm_l2.setText("100%")
        self.cloud1_hm_l3.setText("cpu")
        self.cloud1_hm_l1.setGeometry(772, 467, 20, 10)
        self.cloud1_hm_l2.setGeometry(763, 399, 30, 10)
        self.cloud1_hm_l3.setGeometry(792, 472, 20, 20)
        self.cloud2_hm_l1 = QtWidgets.QLabel(parent=self)
        self.cloud2_hm_l2 = QtWidgets.QLabel(parent=self)
        self.cloud2_hm_l3 = QtWidgets.QLabel(parent=self)
        self.cloud2_hm_l1.setText("0%")
        self.cloud2_hm_l2.setText("100%")
        self.cloud2_hm_l3.setText("cpu")
        self.cloud2_hm_l1.setGeometry(1127, 492, 20, 10)
        self.cloud2_hm_l2.setGeometry(1117, 424, 30, 10)
        self.cloud2_hm_l3.setGeometry(1145, 498, 20, 20)
        self.cloud3_hm_l1 = QtWidgets.QLabel(parent=self)
        self.cloud3_hm_l2 = QtWidgets.QLabel(parent=self)
        self.cloud3_hm_l3 = QtWidgets.QLabel(parent=self)
        self.cloud3_hm_l1.setText("0%")
        self.cloud3_hm_l2.setText("100%")
        self.cloud3_hm_l3.setText("cpu")
        self.cloud3_hm_l1.setGeometry(1125, 932, 20, 10)
        self.cloud3_hm_l2.setGeometry(1118, 872, 30, 10)
        self.cloud3_hm_l3.setGeometry(1145, 944, 20, 20)
        scene.addWidget(self.cloud1_hm_l1)
        scene.addWidget(self.cloud1_hm_l2)
        scene.addWidget(self.cloud1_hm_l3)
        scene.addWidget(self.cloud2_hm_l1)
        scene.addWidget(self.cloud2_hm_l2)
        scene.addWidget(self.cloud2_hm_l3)
        scene.addWidget(self.cloud3_hm_l1)
        scene.addWidget(self.cloud3_hm_l2)
        scene.addWidget(self.cloud3_hm_l3)

        self.cloud1_link_1 = QtWidgets.QLabel(self)
        self.cloud1_link_1.setGeometry(958, 540, 35, 15)
        scene.addWidget(self.cloud1_link_1)

        self.cloud1_link_2_tag = QtWidgets.QLabel(self)
        self.cloud1_link_2_tag.setText("BW:")
        self.cloud1_link_2_tag.setGeometry(750, 680, 35, 15)
        scene.addWidget(self.cloud1_link_2_tag)

        self.cloud1_link_2 = QtWidgets.QLabel(self)
        self.cloud1_link_2.setGeometry(750, 700, 35, 15)
        scene.addWidget(self.cloud1_link_2)

        self.cloud2_link = QtWidgets.QLabel(self)
        self.cloud2_link.setGeometry(1070, 580, 35, 15)
        scene.addWidget(self.cloud2_link)

        self.cloud3_link_1 = QtWidgets.QLabel(self)
        self.cloud3_link_1.setGeometry(1160, 720, 35, 15)
        scene.addWidget(self.cloud3_link_1)

        self.cloud3_link_2 = QtWidgets.QLabel(self)
        self.cloud3_link_2.setGeometry(990, 805, 35, 15)
        scene.addWidget(self.cloud3_link_2)

        return scene


    def _initImageLoad(self):
        self.user_first_pkg = ImageLoader(parent=self, geo=[300, 440, 560, 150],
                                              image_url='./images/firs_pkg.png', direction="l2r", img_scale_w=0, img_scale_h=0,
                                              interval=3, title='1. 首包 ', tag_geo=[120, 194, 240, 30])
        self.addr_request = ImageLoader(parent=self, geo=[300, 440, 560, 150],
                                          image_url='./images/addr_req.png', direction="l2r", img_scale_w=0, img_scale_h=0,
                                          interval=3, title='2. 寻址请求 ', tag_geo=[120, 194, 240, 30])
        self.net_route_ctrl = ImageLoader(parent=self, geo=[300, 440, 560, 150],
                                        image_url='./images/net_ctrl.png', direction="l2r", img_scale_w=0, img_scale_h=0,
                                        interval=3, title='4. 网络路径控制 ', tag_geo=[120, 194, 240, 30])
        self.net_route_ctrl = ImageLoader(parent=self, geo=[300, 440, 560, 150],
                                          image_url='./images/choose_new_svc.png', direction="l2r", img_scale_w=0, img_scale_h=0,
                                          interval=3, title='8. 选择新服务实例，完成网络路径控制 ', tag_geo=[120, 194, 240, 30])
        self.video_stream = ImageLoader(parent=self, geo=[300, 440, 560, 150],
                                          image_url='./images/video_stream.png', direction="l2r", img_scale_w=0, img_scale_h=0,
                                          interval=3, title='5. 视频传输数据 ', tag_geo=[120, 194, 240, 30])
