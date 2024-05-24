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
        self._initView()

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

    def add_butten(self):
        self.initBtn()
        self.initScene()

    def initBtn(self):
        self.topBtnStyleSheet = """
                                    QPushButton {
                                        background-color: #ccc;
                                        border: 6px solid #2980b9;
                                        color: blue;
                                        padding: 10px 20px;
                                        border-radius: 25px;
                                        width：150px;
                                        font-size: 20px;
                                    }
                                    QPushButton:hover {
                                        color:red;
                                        border: 6px inset #2980b9;
                                    }
                                """

        self.topBtnSelectedStyleSheet = """
                                            QPushButton {
                                                background-color: #ccc;
                                                padding: 10px 20px;
                                                border-radius: 25px;
                                                width：150px;
                                                font-size: 20px;
                                                color:red;
                                                border: 6px inset #2980b9;
                                            }
                                        """

        self.leftBtnStyleSheet = """
                                            QPushButton {
                                                background-color: #ccc;
                                                border: 10px solid #2980b9;
                                                color: blue;
                                                padding: 20px;
                                                border-radius: 30px;
                                                width：150px;
                                                font-size: 20px;
                                            }
                                            QPushButton:hover {
                                                color:red;
                                                border: 10px inset #2980b9;
                                            }
                                        """

        self.leftBtnSelectedStyleSheet = """
                                                    QPushButton {
                                                        background-color: #ccc;
                                                        padding: 20px;
                                                        border-radius: 30px;
                                                        width：150px;
                                                        font-size: 20px;
                                                        color:red;
                                                        border: 10px inset #2980b9;
                                                    }
                                                """

        self.topBtn1 = QPushButton("视频点播")
        self.topBtn1.setStyleSheet(self.topBtnStyleSheet)
        self.topBtn2 = QPushButton("AI训练1")
        self.topBtn2.setStyleSheet(self.topBtnStyleSheet)
        self.topBtn3 = QPushButton("心跳检测")
        self.topBtn3.setStyleSheet(self.topBtnStyleSheet)
        self.topBtn4 = QPushButton("AI训练2")
        self.topBtn4.setStyleSheet(self.topBtnStyleSheet)
        self.topBtn5 = QPushButton("视频转换")
        self.topBtn5.setStyleSheet(self.topBtnStyleSheet)
        self.topBtn6 = QPushButton("AI训练3")
        self.topBtn6.setStyleSheet(self.topBtnStyleSheet)

        self.leftBtn1 = QPushButton("传统MEC")
        self.leftBtn1.setStyleSheet(self.leftBtnStyleSheet)
        self.leftBtn2 = QPushButton("算网融合")
        self.leftBtn2.setStyleSheet(self.leftBtnStyleSheet)

        self.topBtn1Tag = 0
        self.topBtn2Tag = 0
        self.topBtn3Tag = 0
        self.topBtn4Tag = 0
        self.topBtn5Tag = 0
        self.topBtn6Tag = 0
        self.leftBtn1Tag = 0
        self.leftBtn2Tag = 0

        self.topBtn1.clicked.connect(self.topBtn1_click)
        self.topBtn2.clicked.connect(self.topBtn2_click)
        self.topBtn3.clicked.connect(self.topBtn3_click)
        self.topBtn4.clicked.connect(self.topBtn4_click)
        self.topBtn5.clicked.connect(self.topBtn5_click)
        self.topBtn6.clicked.connect(self.topBtn6_click)

        self.leftBtn1.clicked.connect(self.leftBtn1_click)
        self.leftBtn2.clicked.connect(self.leftBtn2_click)

        self.proxy_widget_height = 175

        # 创建 QGraphicsProxyWidget 并将按钮嵌入到 QGraphicsScene 中
        proxy_widget = QtWidgets.QGraphicsProxyWidget()
        proxy_widget.setWidget(self.topBtn1)
        proxy_widget.setPos(400, self.proxy_widget_height)  # 设置按钮在场景中的位置
        # 将 QGraphicsProxyWidget 添加到场景中
        self.view.scene().addItem(proxy_widget)

        # 创建 QGraphicsProxyWidget 并将按钮嵌入到 QGraphicsScene 中
        proxy_widget = QtWidgets.QGraphicsProxyWidget()
        proxy_widget.setWidget(self.topBtn2)
        proxy_widget.setPos(600, self.proxy_widget_height)  # 设置按钮在场景中的位置
        self.view.scene().addItem(proxy_widget)

        proxy_widget = QtWidgets.QGraphicsProxyWidget()
        proxy_widget.setWidget(self.topBtn3)
        proxy_widget.setPos(800, self.proxy_widget_height)  # 设置按钮在场景中的位置
        self.view.scene().addItem(proxy_widget)

        proxy_widget = QtWidgets.QGraphicsProxyWidget()
        proxy_widget.setWidget(self.topBtn4)
        proxy_widget.setPos(1000, self.proxy_widget_height)  # 设置按钮在场景中的位置
        self.view.scene().addItem(proxy_widget)

        proxy_widget = QtWidgets.QGraphicsProxyWidget()
        proxy_widget.setWidget(self.topBtn5)
        proxy_widget.setPos(1200, self.proxy_widget_height)  # 设置按钮在场景中的位置
        self.view.scene().addItem(proxy_widget)

        proxy_widget = QtWidgets.QGraphicsProxyWidget()
        proxy_widget.setWidget(self.topBtn6)
        proxy_widget.setPos(1400, self.proxy_widget_height)  # 设置按钮在场景中的位置
        self.view.scene().addItem(proxy_widget)

        proxy_widget = QtWidgets.QGraphicsProxyWidget()
        proxy_widget.setWidget(self.leftBtn1)
        proxy_widget.setPos(50, 480)  # 设置按钮在场景中的位置
        self.view.scene().addItem(proxy_widget)

        proxy_widget = QtWidgets.QGraphicsProxyWidget()
        proxy_widget.setWidget(self.leftBtn2)
        proxy_widget.setPos(50, 620)  # 设置按钮在场景中的位置
        self.view.scene().addItem(proxy_widget)

    def initScene(self):
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
                self.leftBtn1.setStyleSheet((self.leftBtnStyleSheet))
                self.leftBtn2.setStyleSheet((self.leftBtnSelectedStyleSheet))

        else:
            self.topBtn3.setStyleSheet(self.topBtnStyleSheet)
            self.leftBtn1.setStyleSheet(self.leftBtnStyleSheet)
            self.leftBtn2.setStyleSheet(self.leftBtnStyleSheet)
            self.topBtn3Tag = 0
            self.leftBtn1Tag = 0
            self.leftBtn2Tag = 0

            if self.topBtn1Tag == 1 and self.topBtn2Tag == 1 and self.topBtn3Tag == 0 and self.topBtn4Tag == 0 and self.topBtn5Tag == 0 and self.topBtn6Tag == 0:
                self.leftBtn1.setStyleSheet((self.leftBtnSelectedStyleSheet))

            self.pixmap_xintiao.setVisible(False)

    def topBtn4_click(self):
        if self.topBtn4Tag == 0:
            self.topBtn4.setStyleSheet(self.topBtnSelectedStyleSheet)
            self.leftBtn1.setStyleSheet(self.leftBtnStyleSheet)
            self.topBtn4Tag = 1
            self.leftBtn1Tag = 0
            self.pixmap_xunlian2.setVisible(True)

            if self.topBtn1Tag == 1 and self.topBtn2Tag == 1 and self.topBtn3Tag == 1 and self.topBtn4Tag == 1 and self.topBtn5Tag == 1 and self.topBtn6Tag == 1:
                self.leftBtn1.setStyleSheet((self.leftBtnStyleSheet))
                self.leftBtn2.setStyleSheet((self.leftBtnSelectedStyleSheet))

        else:
            self.topBtn4.setStyleSheet(self.topBtnStyleSheet)
            self.leftBtn1.setStyleSheet(self.leftBtnStyleSheet)
            self.leftBtn2.setStyleSheet(self.leftBtnStyleSheet)
            self.topBtn4Tag = 0
            self.leftBtn1Tag = 0
            self.leftBtn2Tag = 0

            if self.topBtn1Tag == 1 and self.topBtn2Tag == 1 and self.topBtn3Tag == 0 and self.topBtn4Tag == 0 and self.topBtn5Tag == 0 and self.topBtn6Tag == 0:
                self.leftBtn1.setStyleSheet((self.leftBtnSelectedStyleSheet))

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
                self.leftBtn1.setStyleSheet((self.leftBtnSelectedStyleSheet))

            self.pixmap_xunlian3.setVisible(False)

    def leftBtn1_click(self):
        if self.leftBtn1Tag == 0:
            self.reset()
            self.leftBtn1Tag = 1
            self.leftBtn2Tag = 0
            self.topBtn1Tag = 1
            self.topBtn2Tag = 1

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
        else:
            self.reset()

    def leftBtn2_click(self):
        if self.leftBtn2Tag == 0:
            self.leftBtn1Tag = 0
            self.leftBtn2Tag = 1
            self.topBtn1Tag = 1
            self.topBtn2Tag = 1
            self.topBtn3Tag = 1
            self.topBtn4Tag = 1
            self.topBtn5Tag = 1
            self.topBtn6Tag = 1

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
        else:
            self.reset()


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