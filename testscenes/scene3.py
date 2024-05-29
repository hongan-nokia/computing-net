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

from testscenes.scene31 import Scene31
from testscenes.scene32 import Scene32
from testscenes.scene33 import Scene33


class Scene3(QWidget):
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

        self._initView()
        self._initTestScene()

    def _initView(self):
        self.setWindowTitle(" ")
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.view = QtWidgets.QGraphicsView(parent=self)
        self.view.setBackgroundBrush(QtGui.QBrush(QtGui.QImage('./images_test3/test_scenario3_bg_all.png')))
        self.view.setCacheMode(QtWidgets.QGraphicsView.CacheBackground)
        self.view.setScene(QtWidgets.QGraphicsScene())
        self.view.setSceneRect(0, 0, 1920, 1080)
        self.view.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        self.view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setRenderHint(QtGui.QPainter.Antialiasing)
        self.view.setGeometry(0, 0, 1920, 1080)

        self.add_butten()

    def add_butten(self):
        self.initBtn()
        # self.initScene()

    def initBtn(self):
        self.btnStyleSheet = """
                                    QPushButton {
                                        background-color: #031133;
                                        border: 15px solid #2980b9;
                                        border-style:outset;
                                        color: #fff;
                                        border-radius: 50px;
                                        padding: 10px 20px;
                                    }
                                    QPushButton:hover {
                                        color:red;
                                        border: 15px inset #2980b9;
                                    }
                                """

        self.topBtnFont = QtGui.QFont("Arial", 30, QtGui.QFont.Bold)

        btnToTop = 400
        btnWidth = 300
        btnHeight = 300

        self.btn1 = QPushButton("服务寻址测试")
        self.btn1.setGeometry(240, btnToTop, btnWidth, btnHeight)
        self.btn1.setFont(self.topBtnFont)
        self.btn2 = QPushButton("算力寻址测试")
        self.btn2.setGeometry(810, btnToTop, btnWidth, btnHeight)
        self.btn2.setFont(self.topBtnFont)
        self.btn3 = QPushButton("内容寻址测试")
        self.btn3.setGeometry(1380, btnToTop, btnWidth, btnHeight)
        self.btn3.setFont(self.topBtnFont)

        self.btn1.clicked.connect(self.btn1_click)
        self.btn2.clicked.connect(self.btn2_click)
        self.btn3.clicked.connect(self.btn3_click)

        self.view.scene().addWidget(self.btn1)
        self.view.scene().addWidget(self.btn2)
        self.view.scene().addWidget(self.btn3)

    def btn1_click(self):
        self.setVisible(False)
        self.scene31.reset()
        # self.scene31.service_step1.label.setVisible(True)
        self.scene31.setVisible(True)
        self.scene32.setVisible(False)
        self.scene33.setVisible(False)

    def btn2_click(self):
        self.setVisible(False)
        self.scene31.setVisible(False)
        self.scene32.reset()
        # self.scene32.service_step1.label.setVisible(True)
        self.scene32.setVisible(True)
        self.scene33.setVisible(False)

    def btn3_click(self):
        self.setVisible(False)
        self.scene31.setVisible(False)
        self.scene32.setVisible(False)
        self.scene33.reset()
        # self.scene33.service_step1.label.setVisible(True)
        self.scene33.setVisible(True)

    def reset(self):
        self.btn1.setStyleSheet(self.btnStyleSheet)
        self.btn2.setStyleSheet(self.btnStyleSheet)
        self.btn3.setStyleSheet(self.btnStyleSheet)

    def _initTestScene(self):
        self.scene31 = Scene31(self.parent(), self.cfn_manager)
        self.scene31.setVisible(False)
        self.scene32 = Scene32(self.parent(), self.cfn_manager)
        self.scene32.setVisible(False)
        self.scene33 = Scene33(self.parent(), self.cfn_manager)
        self.scene33.setVisible(False)
        # pass