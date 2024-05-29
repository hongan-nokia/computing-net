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

from utils.HeatMap import HeatMap


class SystemSyntheticResUtilize(QWidget):
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
        self._initMonitorQueue()
        self._initView()
        self._initScene()
        self._initHeapMap()

    def _initView(self):
        self.setWindowTitle(" ")
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.view = QtWidgets.QGraphicsView(parent=self)
        self.view.setBackgroundBrush(QtGui.QBrush(QtGui.QImage('./images/test_scenario2_bg.png')))
        self.view.setCacheMode(QtWidgets.QGraphicsView.CacheBackground)
        self.view.setScene(QtWidgets.QGraphicsScene())
        self.view.setSceneRect(0, 0, 1920, 1080)
        self.view.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        self.view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setRenderHint(QtGui.QPainter.Antialiasing)
        self.view.setGeometry(0, 0, 1920, 1080)
        self.add_butten()
        self.topBtn1.setStyleSheet(self.topBtnStyleSheet)
        self.topBtn2.setStyleSheet(self.topBtnStyleSheet)
        self.topBtn3.setStyleSheet(self.topBtnStyleSheet)
        self.topBtn4.setStyleSheet(self.topBtnStyleSheet)
        self.topBtn5.setStyleSheet(self.topBtnStyleSheet)
        self.topBtn6.setStyleSheet(self.topBtnStyleSheet)

        self.leftBtn1.setStyleSheet(self.leftBtnStyleSheet)
        self.leftBtn2.setStyleSheet(self.leftBtnStyleSheet)

    def add_butten(self):
        self.initBtn()

    def initBtn(self):
        self.topBtnStyleSheet = """
        QPushButton {background-color: #031133;border-radius: 20px;border: 5px solid #2980b9;border-style:outset;
        color: #fff;padding: 10px 20px;}
        QPushButton:hover {color:red;border: 5px inset #2980b9;}"""
        self.topBtnSelectedStyleSheet = """
        QPushButton {background-color: #031133;padding: 10px 20px;color: red;border: 5px inset #2980b9;border-radius: 20px;}"""
        self.leftBtnStyleSheet = """
        QPushButton {background-color: #031133;border: 7px solid #2980b9;border-radius: 30px;border-style:outset;
        color: #fff;padding: 30px 20px;width：150px;font-size: 20px;}
        QPushButton:hover {color:red;border: 7px inset #2980b9;}"""
        self.leftBtnSelectedStyleSheet = """
        QPushButton {background-color: #031133;padding: 30px 20px;width：150px;font-size: 20px;
        color:red;border: 7px inset #2980b9;border-radius: 30px;}"""
        self.topBtnFont = QtGui.QFont("Arial", 14, QtGui.QFont.Bold)
        self.leftBtnFont = QtGui.QFont("Arial", 20, QtGui.QFont.Bold)

        topBtnToTop = 175
        topBtnWidth = 150
        topBtnHeight = 20

        self.topBtn1 = QPushButton("视频点播")
        # self.topBtn1.setStyleSheet(self.topBtnStyleSheet)
        self.topBtn1.setGeometry(400, topBtnToTop, topBtnWidth, topBtnHeight)
        self.topBtn1.setFont(self.topBtnFont)
        self.topBtn2 = QPushButton("AI训练1")
        # self.topBtn2.setStyleSheet(self.topBtnStyleSheet)
        self.topBtn2.setGeometry(600, topBtnToTop, topBtnWidth, topBtnHeight)
        self.topBtn2.setFont(self.topBtnFont)
        self.topBtn3 = QPushButton("心跳检测")
        # self.topBtn3.setStyleSheet(self.topBtnStyleSheet)
        self.topBtn3.setGeometry(800, topBtnToTop, topBtnWidth, topBtnHeight)
        self.topBtn3.setFont(self.topBtnFont)
        self.topBtn4 = QPushButton("AI训练2")
        # self.topBtn4.setStyleSheet(self.topBtnStyleSheet)
        self.topBtn4.setGeometry(1000, topBtnToTop, topBtnWidth, topBtnHeight)
        self.topBtn4.setFont(self.topBtnFont)
        self.topBtn5 = QPushButton("视频转换")
        # self.topBtn5.setStyleSheet(self.topBtnStyleSheet)
        self.topBtn5.setGeometry(1200, topBtnToTop, topBtnWidth, topBtnHeight)
        self.topBtn5.setFont(self.topBtnFont)
        self.topBtn6 = QPushButton("AI训练3")
        # self.topBtn6.setStyleSheet(self.topBtnStyleSheet)
        self.topBtn6.setGeometry(1400, topBtnToTop, topBtnWidth, topBtnHeight)
        self.topBtn6.setFont(self.topBtnFont)

        leftBtnToleft = 20
        letBtnWidth = 180
        leftBtnHeight = 20

        self.leftBtn1 = QPushButton("传统MEC")
        # self.leftBtn1.setStyleSheet(self.leftBtnStyleSheet)
        self.leftBtn1.setGeometry(leftBtnToleft, 480, letBtnWidth, leftBtnHeight)
        self.leftBtn1.setFont(self.topBtnFont)
        self.leftBtn2 = QPushButton("算网融合")
        # self.leftBtn2.setStyleSheet(self.leftBtnStyleSheet)
        self.leftBtn2.setGeometry(leftBtnToleft, 620, letBtnWidth, leftBtnHeight)
        self.leftBtn2.setFont(self.topBtnFont)

        self.topBtn1Tag = 0
        self.topBtn2Tag = 0
        self.topBtn3Tag = 0
        self.topBtn4Tag = 0
        self.topBtn5Tag = 0
        self.topBtn6Tag = 0
        self.leftBtn1Tag = 0
        self.leftBtn2Tag = 0

        # self.topBtn1.clicked.connect(self.topBtn1_click)
        # self.topBtn2.clicked.connect(self.topBtn2_click)
        # self.topBtn3.clicked.connect(self.topBtn3_click)
        # self.topBtn4.clicked.connect(self.topBtn4_click)
        # self.topBtn5.clicked.connect(self.topBtn5_click)
        # self.topBtn6.clicked.connect(self.topBtn6_click)

        self.leftBtn1.clicked.connect(self.traditionalMEC)
        self.leftBtn2.clicked.connect(self.computingNetConverge)

        self.view.scene().addWidget(self.topBtn1)
        self.view.scene().addWidget(self.topBtn2)
        self.view.scene().addWidget(self.topBtn3)
        self.view.scene().addWidget(self.topBtn4)
        self.view.scene().addWidget(self.topBtn5)
        self.view.scene().addWidget(self.topBtn6)

        self.view.scene().addWidget(self.leftBtn1)
        self.view.scene().addWidget(self.leftBtn2)

    def _initScene(self):
        pixmap = QtGui.QPixmap('./images/dianbo.png')
        self.pixmap_dianbo = QtWidgets.QGraphicsPixmapItem(pixmap)
        self.pixmap_dianbo.setPos(925, 350)
        self.view.scene().addItem(self.pixmap_dianbo)
        self.pixmap_dianbo.setVisible(False)

        pixmap = QtGui.QPixmap('./images/xunlian1.png')
        self.pixmap_xunlian1 = QtWidgets.QGraphicsPixmapItem(pixmap)
        self.pixmap_xunlian1.setPos(1120, 780)
        self.view.scene().addItem(self.pixmap_xunlian1)
        self.pixmap_xunlian1.setVisible(False)

        pixmap = QtGui.QPixmap('./images/xintiao.png')
        self.pixmap_xintiao = QtWidgets.QGraphicsPixmapItem(pixmap)
        self.pixmap_xintiao.setPos(925, 390)
        self.view.scene().addItem(self.pixmap_xintiao)
        self.pixmap_xintiao.setVisible(False)

        pixmap = QtGui.QPixmap('./images/xunlian2.png')
        self.pixmap_xunlian2 = QtWidgets.QGraphicsPixmapItem(pixmap)
        self.pixmap_xunlian2.setPos(1175, 460)
        self.view.scene().addItem(self.pixmap_xunlian2)
        self.pixmap_xunlian2.setVisible(False)

        pixmap = QtGui.QPixmap('./images/zhuanhuan.png')
        self.pixmap_zhuanhuan = QtWidgets.QGraphicsPixmapItem(pixmap)
        self.pixmap_zhuanhuan.setPos(1120, 820)
        self.view.scene().addItem(self.pixmap_zhuanhuan)
        self.pixmap_zhuanhuan.setVisible(False)

        pixmap = QtGui.QPixmap('./images/xunlian3.png')
        self.pixmap_xunlian3 = QtWidgets.QGraphicsPixmapItem(pixmap)
        self.pixmap_xunlian3.setPos(1175, 500)
        self.view.scene().addItem(self.pixmap_xunlian3)
        self.pixmap_xunlian3.setVisible(False)

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
        self.view.scene().addWidget(self.cloud1_hm_l1)
        self.view.scene().addWidget(self.cloud1_hm_l2)
        self.view.scene().addWidget(self.cloud1_hm_l3)
        self.view.scene().addWidget(self.cloud2_hm_l1)
        self.view.scene().addWidget(self.cloud2_hm_l2)
        self.view.scene().addWidget(self.cloud2_hm_l3)
        self.view.scene().addWidget(self.cloud3_hm_l1)
        self.view.scene().addWidget(self.cloud3_hm_l2)
        self.view.scene().addWidget(self.cloud3_hm_l3)

    def topBtn1_click(self):
        if self.topBtn1Tag == 0:
            self.topBtn1.setStyleSheet(self.topBtnSelectedStyleSheet)
            self.topBtn1Tag = 1
            self.pixmap_dianbo.setVisible(True)

            if self.topBtn1Tag == 1 and self.topBtn2Tag == 1 and self.topBtn3Tag == 0 and self.topBtn4Tag == 0 and self.topBtn5Tag == 0 and self.topBtn6Tag == 0:
                self.leftBtn1.setStyleSheet((self.leftBtnSelectedStyleSheet))
            if self.topBtn1Tag == 1 and self.topBtn2Tag == 1 and self.topBtn3Tag == 1 and self.topBtn4Tag == 1 and self.topBtn5Tag == 1 and self.topBtn6Tag == 1:
                self.leftBtn1.setStyleSheet((self.leftBtnStyleSheet))
                self.leftBtn2.setStyleSheet((self.leftBtnSelectedStyleSheet))

        else:
            self.topBtn1.setStyleSheet(self.topBtnStyleSheet)
            self.leftBtn1.setStyleSheet(self.leftBtnStyleSheet)
            self.leftBtn2.setStyleSheet(self.leftBtnStyleSheet)
            self.topBtn1Tag = 0
            self.leftBtn1Tag = 0
            self.leftBtn2Tag = 0

            self.pixmap_dianbo.setVisible(False)

    def topBtn2_click(self):
        if self.topBtn2Tag == 0:
            self.topBtn2.setStyleSheet(self.topBtnSelectedStyleSheet)
            self.topBtn2Tag = 1
            self.pixmap_xunlian1.setVisible(True)

            if self.topBtn1Tag == 1 and self.topBtn2Tag == 1 and self.topBtn3Tag == 0 and self.topBtn4Tag == 0 and self.topBtn5Tag == 0 and self.topBtn6Tag == 0:
                self.leftBtn1.setStyleSheet((self.leftBtnSelectedStyleSheet))
            if self.topBtn1Tag == 1 and self.topBtn2Tag == 1 and self.topBtn3Tag == 1 and self.topBtn4Tag == 1 and self.topBtn5Tag == 1 and self.topBtn6Tag == 1:
                self.leftBtn1.setStyleSheet((self.leftBtnStyleSheet))
                self.leftBtn2.setStyleSheet((self.leftBtnSelectedStyleSheet))

        else:
            self.topBtn2.setStyleSheet(self.topBtnStyleSheet)
            self.leftBtn1.setStyleSheet(self.leftBtnStyleSheet)
            self.leftBtn2.setStyleSheet(self.leftBtnStyleSheet)
            self.topBtn2Tag = 0
            self.leftBtn1Tag = 0
            self.leftBtn2Tag = 0

            self.pixmap_xunlian1.setVisible(False)

    def topBtn3_click(self):
        if self.topBtn3Tag == 0:
            self.topBtn3.setStyleSheet(self.topBtnSelectedStyleSheet)
            self.leftBtn1.setStyleSheet(self.leftBtnStyleSheet)
            self.topBtn3Tag = 1
            self.leftBtn1Tag = 0
            self.pixmap_xintiao.setVisible(True)

            if self.topBtn1Tag == 1 and self.topBtn2Tag == 1 and self.topBtn3Tag == 1 and self.topBtn4Tag == 1 and self.topBtn5Tag == 1 and self.topBtn6Tag == 1:
                self.leftBtn1.setStyleSheet(self.leftBtnStyleSheet)
                self.leftBtn2.setStyleSheet(self.leftBtnSelectedStyleSheet)
        else:
            self.topBtn3.setStyleSheet(self.topBtnStyleSheet)
            self.leftBtn1.setStyleSheet(self.leftBtnStyleSheet)
            self.leftBtn2.setStyleSheet(self.leftBtnStyleSheet)
            self.topBtn3Tag = 0
            self.leftBtn1Tag = 0
            self.leftBtn2Tag = 0

            if self.topBtn1Tag == 1 and self.topBtn2Tag == 1 and self.topBtn3Tag == 0 and self.topBtn4Tag == 0 and self.topBtn5Tag == 0 and self.topBtn6Tag == 0:
                self.leftBtn1.setStyleSheet(self.leftBtnSelectedStyleSheet)

            self.pixmap_xintiao.setVisible(False)

    def topBtn4_click(self):
        if self.topBtn4Tag == 0:
            self.topBtn4.setStyleSheet(self.topBtnSelectedStyleSheet)
            self.leftBtn1.setStyleSheet(self.leftBtnStyleSheet)
            self.topBtn4Tag = 1
            self.leftBtn1Tag = 0
            self.pixmap_xunlian2.setVisible(True)

            if self.topBtn1Tag == 1 and self.topBtn2Tag == 1 and self.topBtn3Tag == 1 and self.topBtn4Tag == 1 and self.topBtn5Tag == 1 and self.topBtn6Tag == 1:
                self.leftBtn1.setStyleSheet(self.leftBtnStyleSheet)
                self.leftBtn2.setStyleSheet(self.leftBtnSelectedStyleSheet)

        else:
            self.topBtn4.setStyleSheet(self.topBtnStyleSheet)
            self.leftBtn1.setStyleSheet(self.leftBtnStyleSheet)
            self.leftBtn2.setStyleSheet(self.leftBtnStyleSheet)
            self.topBtn4Tag = 0
            self.leftBtn1Tag = 0
            self.leftBtn2Tag = 0

            if self.topBtn1Tag == 1 and self.topBtn2Tag == 1 and self.topBtn3Tag == 0 and self.topBtn4Tag == 0 and self.topBtn5Tag == 0 and self.topBtn6Tag == 0:
                self.leftBtn1.setStyleSheet(self.leftBtnSelectedStyleSheet)

            self.pixmap_xunlian2.setVisible(False)

    def topBtn5_click(self):
        if self.topBtn5Tag == 0:
            self.topBtn5.setStyleSheet(self.topBtnSelectedStyleSheet)
            self.leftBtn1.setStyleSheet(self.leftBtnStyleSheet)
            self.topBtn5Tag = 1
            self.leftBtn1Tag = 0
            self.pixmap_zhuanhuan.setVisible(True)

            if self.topBtn1Tag == 1 and self.topBtn2Tag == 1 and self.topBtn3Tag == 1 and self.topBtn4Tag == 1 and self.topBtn5Tag == 1 and self.topBtn6Tag == 1:
                self.leftBtn1.setStyleSheet((self.leftBtnStyleSheet))
                self.leftBtn2.setStyleSheet((self.leftBtnSelectedStyleSheet))

        else:
            self.topBtn5.setStyleSheet(self.topBtnStyleSheet)
            self.leftBtn1.setStyleSheet(self.leftBtnStyleSheet)
            self.leftBtn2.setStyleSheet(self.leftBtnStyleSheet)
            self.topBtn5Tag = 0
            self.leftBtn1Tag = 0
            self.leftBtn2Tag = 0

            if self.topBtn1Tag == 1 and self.topBtn2Tag == 1 and self.topBtn3Tag == 0 and self.topBtn4Tag == 0 and self.topBtn5Tag == 0 and self.topBtn6Tag == 0:
                self.leftBtn1.setStyleSheet((self.leftBtnSelectedStyleSheet))

            self.pixmap_zhuanhuan.setVisible(False)

    def topBtn6_click(self):
        if self.topBtn6Tag == 0:
            self.topBtn6.setStyleSheet(self.topBtnSelectedStyleSheet)
            self.leftBtn1.setStyleSheet(self.leftBtnStyleSheet)
            self.topBtn6Tag = 1
            self.leftBtn1Tag = 0
            self.pixmap_xunlian3.setVisible(True)

            if self.topBtn1Tag == 1 and self.topBtn2Tag == 1 and self.topBtn3Tag == 1 and self.topBtn4Tag == 1 and self.topBtn5Tag == 1 and self.topBtn6Tag == 1:
                self.leftBtn1.setStyleSheet((self.leftBtnStyleSheet))
                self.leftBtn2.setStyleSheet((self.leftBtnSelectedStyleSheet))

        else:
            self.topBtn6.setStyleSheet(self.topBtnStyleSheet)
            self.leftBtn1.setStyleSheet(self.leftBtnStyleSheet)
            self.leftBtn2.setStyleSheet(self.leftBtnStyleSheet)
            self.topBtn6Tag = 0
            self.leftBtn1Tag = 0
            self.leftBtn2Tag = 0

            if self.topBtn1Tag == 1 and self.topBtn2Tag == 1 and self.topBtn3Tag == 0 and self.topBtn4Tag == 0 and self.topBtn5Tag == 0 and self.topBtn6Tag == 0:
                self.leftBtn1.setStyleSheet(self.leftBtnSelectedStyleSheet)

            self.pixmap_xunlian3.setVisible(False)

    def traditionalMEC(self):
        if self.leftBtn1Tag == 0:
            self.reset()
            self.leftBtn1Tag = 1
            self.leftBtn2Tag = 0
            self.topBtn1Tag = 1
            self.topBtn2Tag = 1

            self.pixmap_xunlian1.setPos(925, 390)

            self.pixmap_dianbo.setVisible(True)
            self.pixmap_xunlian1.setVisible(True)
            self.pixmap_xunlian2.setVisible(False)
            self.pixmap_xunlian3.setVisible(False)
            self.pixmap_xintiao.setVisible(False)
            self.pixmap_zhuanhuan.setVisible(False)

            self.topBtn1.setStyleSheet(self.topBtnSelectedStyleSheet)
            self.topBtn2.setStyleSheet(self.topBtnSelectedStyleSheet)
            self.topBtn3.setStyleSheet(self.topBtnStyleSheet)
            self.topBtn4.setStyleSheet(self.topBtnStyleSheet)
            self.topBtn5.setStyleSheet(self.topBtnStyleSheet)
            self.topBtn6.setStyleSheet(self.topBtnStyleSheet)

            self.leftBtn1.setStyleSheet(self.leftBtnSelectedStyleSheet)
            self.leftBtn2.setStyleSheet(self.leftBtnStyleSheet)
            self.setTraditionalMEC()
        else:
            self.reset()

    def computingNetConverge(self):
        if self.leftBtn2Tag == 0:
            self.leftBtn1Tag = 0
            self.leftBtn2Tag = 1
            self.topBtn1Tag = 1
            self.topBtn2Tag = 1
            self.topBtn3Tag = 1
            self.topBtn4Tag = 1
            self.topBtn5Tag = 1
            self.topBtn6Tag = 1

            self.pixmap_xunlian1.setPos(1120, 780)

            self.pixmap_dianbo.setVisible(True)
            self.pixmap_xunlian1.setVisible(True)
            self.pixmap_xunlian2.setVisible(True)
            self.pixmap_xunlian3.setVisible(True)
            self.pixmap_xintiao.setVisible(True)
            self.pixmap_zhuanhuan.setVisible(True)

            self.topBtn1.setStyleSheet(self.topBtnSelectedStyleSheet)
            self.topBtn2.setStyleSheet(self.topBtnSelectedStyleSheet)
            self.topBtn3.setStyleSheet(self.topBtnSelectedStyleSheet)
            self.topBtn4.setStyleSheet(self.topBtnSelectedStyleSheet)
            self.topBtn5.setStyleSheet(self.topBtnSelectedStyleSheet)
            self.topBtn6.setStyleSheet(self.topBtnSelectedStyleSheet)

            self.leftBtn1.setStyleSheet(self.leftBtnStyleSheet)
            self.leftBtn2.setStyleSheet(self.leftBtnSelectedStyleSheet)
            self.setComputingNetConverge()
        else:
            self.reset()

    def _initMonitorQueue(self):
        self.monitor_q_cpu_hm_node1 = self.cfn_manager.resource_StatMon['c_node1_cpu']  # 算力节点1 CPU
        self.monitor_q_cpu_hm_node2 = self.cfn_manager.resource_StatMon['c_node2_cpu']  # 算力节点2 CPU
        self.monitor_q_cpu_hm_node3 = self.cfn_manager.resource_StatMon['c_node3_cpu']  # 算力节点3 CPU

    def _initHeapMap(self):
        self.s2cloud1_hm = HeatMap(parent=self, geo=[793, 405, 40, 80], interval=4000,
                                   data_q=self.monitor_q_cpu_hm_node1)
        self.s2cloud2_hm = HeatMap(parent=self, geo=[1058, 520, 40, 80], interval=4000,
                                   data_q=self.monitor_q_cpu_hm_node2)
        self.s2cloud3_hm = HeatMap(parent=self, geo=[986, 857, 40, 80], interval=4000,
                                   data_q=self.monitor_q_cpu_hm_node3)
        self.s2cloud1_hm.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.s2cloud2_hm.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.s2cloud3_hm.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.s2cloud1_hm.setVisible(True)
        self.s2cloud2_hm.setVisible(True)
        self.s2cloud3_hm.setVisible(True)
        self.s2cloud1_hm.timer.start()
        self.s2cloud2_hm.timer.start()
        self.s2cloud3_hm.timer.start()

    def setTraditionalMEC(self):
        self.cfn_manager.send_command('c_node1', 'task', 'AI_trainer1 up')              # AI 训练
        self.cfn_manager.send_command('c_node1', 'task', 'vlcc fake1-WorldCup.mp4_0')     # 视频点播
        # self.cfn_manager.send_command('c_node1', 'task', 'cam_health camera_1')

    def setComputingNetConverge(self):
        self.cfn_manager.send_command('c_node1', 'task', 'vlcc fake1-WorldCup.mp4_0')
        self.cfn_manager.send_command('c_node1', 'task', 'cam_health camera_1')

        self.cfn_manager.send_command('c_node2', 'task', 'AI_trainer1 up')
        self.cfn_manager.send_command('c_node2', 'task', 'AI_trainer2 up')

        self.cfn_manager.send_command('c_node3', 'task', 'AI_trainer3 up')
        self.cfn_manager.send_command('c_node3', 'task', 'vlcc fake2-WorldCup.mp4_0')

    def unsetTraditionalMEC(self):
        self.cfn_manager.send_command('c_node1', 'stop_task', 'AI_trainer1 up')  # AI 训练
        self.cfn_manager.send_command('c_node1', 'stop_task', 'vlcc fake1-WorldCup.mp4_0')  # 视频点播
        # self.cfn_manager.send_command('c_node1', 'task', 'cam_health camera_1')

    def unsetComputingNetConverge(self):
        self.cfn_manager.send_command('c_node1', 'stop_task', 'vlcc fake1-WorldCup.mp4_0')
        self.cfn_manager.send_command('c_node1', 'stop_task', 'cam_health camera_1')

        self.cfn_manager.send_command('c_node2', 'stop_task', 'AI_trainer1 up')
        self.cfn_manager.send_command('c_node2', 'stop_task', 'AI_trainer2 up')

        self.cfn_manager.send_command('c_node3', 'stop_task', 'AI_trainer3 up')
        self.cfn_manager.send_command('c_node3', 'stop_task', 'vlcc fake2-WorldCup.mp4_0')

    def reset(self):
        self.topBtn1Tag = 0
        self.topBtn2Tag = 0
        self.topBtn3Tag = 0
        self.topBtn4Tag = 0
        self.topBtn5Tag = 0
        self.topBtn6Tag = 0
        self.leftBtn1Tag = 0
        self.leftBtn2Tag = 0

        self.pixmap_dianbo.setVisible(False)
        self.pixmap_xunlian1.setVisible(False)
        self.pixmap_xunlian2.setVisible(False)
        self.pixmap_xunlian3.setVisible(False)
        self.pixmap_xintiao.setVisible(False)
        self.pixmap_zhuanhuan.setVisible(False)

        self.topBtn1.setStyleSheet(self.topBtnStyleSheet)
        self.topBtn2.setStyleSheet(self.topBtnStyleSheet)
        self.topBtn3.setStyleSheet(self.topBtnStyleSheet)
        self.topBtn4.setStyleSheet(self.topBtnStyleSheet)
        self.topBtn5.setStyleSheet(self.topBtnStyleSheet)
        self.topBtn6.setStyleSheet(self.topBtnStyleSheet)

        self.leftBtn1.setStyleSheet(self.leftBtnStyleSheet)
        self.leftBtn2.setStyleSheet(self.leftBtnStyleSheet)

        self.unsetTraditionalMEC()
        self.unsetComputingNetConverge()

