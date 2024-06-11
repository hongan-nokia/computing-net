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


class Scene32(QWidget):
    def __init__(self, parent, demo_manager):
        super().__init__()
        self.queueFlag = None
        self.path = 1
        geo = {
            'top': 0,
            'left': 0,
            'width': 1920,
            'height': 1080}
        self._heartrate_update_cnt = 0
        self._previous_position = -1
        self.person_position = -1
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
        self._initHearRate()

    def _initView(self):
        self.setWindowTitle(" ")
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.view = QtWidgets.QGraphicsView(parent=self)
        self.view.setBackgroundBrush(QtGui.QBrush(QtGui.QImage('./images_test3/test_scenario32_bg.png')))
        self.view.setCacheMode(QtWidgets.QGraphicsView.CacheBackground)
        self.view.setScene(QtWidgets.QGraphicsScene())
        self.view.setSceneRect(0, 0, 1920, 1080)
        self.view.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        self.view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setRenderHint(QtGui.QPainter.Antialiasing)
        self.view.setGeometry(0, 0, 1920, 1080)

    def _initScene(self):

        c_node1_heart_rate_img = QtGui.QPixmap("./images/heart_rate.png").scaled(QSize(80, 60))
        c_node2_heart_rate_img = QtGui.QPixmap("./images/heart_rate.png").scaled(QSize(80, 60))
        c_node3_heart_rate_img = QtGui.QPixmap("./images/heart_rate.png").scaled(QSize(80, 60))
        self.c_node1_heart_rate = BlinkingPic(parent=self, pixmap=c_node1_heart_rate_img, auto_dim=True, dim_opacity=0.1,
                                              blink_period=1200).pixmap_item
        self.c_node2_heart_rate = BlinkingPic(parent=self, pixmap=c_node2_heart_rate_img, auto_dim=True, dim_opacity=0.1,
                                              blink_period=1200).pixmap_item
        self.c_node3_heart_rate = BlinkingPic(parent=self, pixmap=c_node3_heart_rate_img, auto_dim=True, dim_opacity=0.1,
                                              blink_period=1200).pixmap_item

        self.view.scene().addItem(self.c_node1_heart_rate)
        self.view.scene().addItem(self.c_node2_heart_rate)
        self.view.scene().addItem(self.c_node3_heart_rate)

        self.c_node1_heart_rate.setPos(906, 428)
        self.c_node2_heart_rate.setPos(1140, 535)
        self.c_node3_heart_rate.setPos(1098, 840)

        self.c_node1_heart_rate.setVisible(False)
        self.c_node2_heart_rate.setVisible(False)
        self.c_node3_heart_rate.setVisible(False)

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

        font1 = QtGui.QFont("Nokia Pure Text", 11)
        self.step1_label1 = QtWidgets.QLabel(parent=self)
        self.step1_label1.setText("a.算力需求用于处理心跳检测")
        self.step1_label1.setWordWrap(True)
        self.step1_label1.setGeometry(587, 446, 110, 50)
        self.step1_label1.setFont(font1)
        self.view.scene().addWidget(self.step1_label1)
        self.step1_label1.setVisible(False)

        font2 = QtGui.QFont("Nokia Pure Text", 14)
        self.step1_label2 = QtWidgets.QLabel(parent=self)
        self.step1_label2.setText("寻址请求")
        self.step1_label2.setWordWrap(True)
        self.step1_label2.setGeometry(921, 500, 110, 50)
        self.step1_label2.setFont(font2)
        self.view.scene().addWidget(self.step1_label2)
        self.step1_label2.setVisible(False)

    def _initMonitorQueue(self):
        self.monitor_q_cpu_hm_node1 = self.cfn_manager.resource_StatMon['c_node1_cpu']  # 算力节点1 CPU
        self.monitor_q_cpu_hm_node2 = self.cfn_manager.resource_StatMon['c_node2_cpu']  # 算力节点2 CPU
        self.monitor_q_cpu_hm_node3 = self.cfn_manager.resource_StatMon['c_node3_cpu']  # 算力节点3 CPU

    def _initHeapMap(self):
        self.cloud1_hm = HeatMap(parent=self, geo=[793, 365, 40, 80], interval=4000, data_q=self.monitor_q_cpu_hm_node1)
        self.cloud2_hm = HeatMap(parent=self, geo=[1058, 520, 40, 80], interval=4000, data_q=self.monitor_q_cpu_hm_node2)
        self.cloud3_hm = HeatMap(parent=self, geo=[986, 857, 40, 80], interval=4000, data_q=self.monitor_q_cpu_hm_node3)
        self.cloud1_hm.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.cloud2_hm.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.cloud3_hm.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.cloud1_hm.setVisible(True)
        self.cloud2_hm.setVisible(True)
        self.cloud3_hm.setVisible(True)

    def _initImageLoad(self):
        # -------------------------------------- Scenario_0 --------------------------------------
        self.service_step1 = ImageLoader(parent=self, geo=[325, 450, 1040, 130],
                                         image_url='./images_test3/computing_power_addressing_step1.png',
                                         img_scale_w=1040,
                                         img_scale_h=130,
                                         direction="l2r",
                                         interval=3, title='1.首包', tag_geo=[130, 30, 100, 20])
        self.service_step2 = ImageLoader(parent=self, geo=[1360, 375, 443, 150],
                                         image_url='./images_test3/computing_power_addressing_step2.png',
                                         img_scale_w=200,
                                         img_scale_h=1,
                                         direction="l2r",
                                         interval=3, title='2.算网融合调度编排(算力寻址，计算最优算力资源路由组合)', tag_geo=[35, 0, 303, 120])
        self.service_step31 = ImageLoader(parent=self, geo=[908, 420, 650, 200],
                                          image_url='./images_test3/computing_power_addressing_step31.png',
                                          img_scale_w=650,
                                          img_scale_h=200,
                                          direction="r2l",
                                          interval=3, title='3.心跳检测处理实例化', tag_geo=[100, 0, 400, 20])
        self.service_step32 = ImageLoader(parent=self, geo=[1145, 530, 600, 80],
                                          image_url='./images_test3/computing_power_addressing_step32.png',
                                          img_scale_w=420,
                                          img_scale_h=80,
                                          direction="r2l",
                                          interval=3, title='3.心跳检测处理实例化', tag_geo=[230, 30, 400, 20])
        self.service_step33 = ImageLoader(parent=self, geo=[1080, 630, 480, 280],
                                          image_url='./images_test3/computing_power_addressing_step33.png',
                                          img_scale_w=480,
                                          img_scale_h=280,
                                          direction="r2l",
                                          interval=3, title='3.心跳检测处理实例化', tag_geo=[100, 230, 400, 20])
        self.service_step41 = ImageLoader(parent=self, geo=[880, 550, 475, 170],
                                          image_url='./images_test3/computing_power_addressing_step41.png',
                                          img_scale_w=475,
                                          img_scale_h=75,
                                          direction="r2l",
                                          interval=3, title='4.网络路径控制', tag_geo=[260, 60, 200, 30])
        self.service_step42 = ImageLoader(parent=self, geo=[1040, 615, 350, 180],
                                          image_url='./images_test3/computing_power_addressing_step42.png',
                                          img_scale_w=350,
                                          img_scale_h=180,
                                          direction="r2l",
                                          interval=3, title='4.网络路径控制', tag_geo=[160, 120, 200, 30])
        self.service_step43 = ImageLoader(parent=self, geo=[1040, 615, 350, 180],
                                          image_url='./images_test3/computing_power_addressing_step43.png',
                                          img_scale_w=350,
                                          img_scale_h=180,
                                          direction="r2l",
                                          interval=3, title='4.网络路径控制', tag_geo=[130, 120, 200, 30])
        self.service_step51 = ImageLoader(parent=self, geo=[320, 460, 550, 120],
                                          image_url='./images_test3/computing_power_addressing_step51.png',
                                          img_scale_w=550,
                                          img_scale_h=120,
                                          direction="l2r",
                                          interval=3, title='5.业务数据流', tag_geo=[20, 80, 200, 30])
        self.service_step52 = ImageLoader(parent=self, geo=[340, 490, 800, 290],
                                          image_url='./images_test3/computing_power_addressing_step52.png',
                                          img_scale_w=800,
                                          img_scale_h=290,
                                          direction="l2r",
                                          interval=3, title='5.业务数据流', tag_geo=[20, 35, 200, 30])
        self.service_step53 = ImageLoader(parent=self, geo=[340, 490, 750, 400],
                                          image_url='./images_test3/computing_power_addressing_step53.png',
                                          img_scale_w=750,
                                          img_scale_h=400,
                                          direction="l2r",
                                          interval=3, title='5.业务数据流', tag_geo=[20, 35, 200, 30])
        self.service_step51.tag_label.setStyleSheet("color: rgb(224,61,205);")
        self.service_step52.tag_label.setStyleSheet("color: rgb(224,61,205);")
        self.service_step53.tag_label.setStyleSheet("color: rgb(224,61,205);")

    def initConnections(self):
        self.service_step1.QtSignals.anim_over.connect(self.service_provision_anim)
        self.service_step2.QtSignals.anim_over.connect(self.service_provision_anim)
        self.service_step31.QtSignals.anim_over.connect(self.service_provision_anim)
        self.service_step32.QtSignals.anim_over.connect(self.service_provision_anim)
        self.service_step33.QtSignals.anim_over.connect(self.service_provision_anim)
        self.service_step41.QtSignals.anim_over.connect(self.service_provision_anim)
        self.service_step42.QtSignals.anim_over.connect(self.service_provision_anim)
        self.service_step43.QtSignals.anim_over.connect(self.service_provision_anim)
        self.service_step51.QtSignals.anim_over.connect(self.service_provision_anim)
        self.service_step52.QtSignals.anim_over.connect(self.service_provision_anim)
        self.service_step53.QtSignals.anim_over.connect(self.service_provision_anim)
        self.cfn_manager.signal_emitter.QtSignals.computingAddr_test.connect(self.computingAddrWorkFlow)
        self.cfn_manager.signal_emitter.QtSignals.container_pulsate_update.connect(self.update_pulserate)
        self.cfn_manager.signal_emitter.QtSignals.container_person_state.connect(self.show_person_position)

    def _initHearRate(self):
        self.heartrate = QtWidgets.QLabel(parent=self)
        self.heartrate.setText("---")
        font = QtGui.QFont("Nokia Pure Text", 28)
        self.heartrate.setFont(font)
        # self.heartrate.setFrameStyle(22)  # show border
        self.heartrate.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignCenter)  # Qt.AlignRight

        palette = self.palette()
        palette.setColor(self.foregroundRole(), self.nokia_blue)
        self.heartrate.setPalette(palette)
        # self.heartrate.setGeometry(1600, 225, 180, 100)
        self.heartrate.setGeometry(1517, 257, 180, 100)

        self.heartrateTag = QtWidgets.QLabel(parent=self)
        self.heartrateTag.setPixmap(QtGui.QPixmap('./images/heartrate_tag.png'))
        self.heartrateTag.setFont(font)
        self.heartrateTag.setPalette(palette)
        self.heartrateTag.setGeometry(1532, 257, 180, 100)
        self.heartrate.raise_()
        self.heartrate.setVisible(True)
        self.heartrateTag.setVisible(True)

    @pyqtSlot(int, float)
    def update_pulserate(self, containerId: int, pulserate: float):
        if pulserate == -1:
            pass
        else:
            self.heartrate.setText('%.0f' % pulserate)
        # print(f'container={containerId}, '
        #       f'person_position={self.person_position}, pulserate={pulserate}, cnt={self._heartrate_update_cnt}')

    @pyqtSlot(int, str)
    def show_person_position(self, containerId: int, presence: str):
        """ When person comes in or go out of a camera's view, it triggers a
            signal with corresponding container id and 'come' or 'gone' flag.
            This function therefore triggers animation of the person's picture.
        """
        print(f'person state change in camera {containerId}: {presence}')
        print(f'self.person_position:  {self.person_position}')
        if self.person_position != -1:
            self._previous_position = self.person_position  # update previous position record
        if containerId == 0:
            if presence == 'come':
                self.person_position = 0
                print(f'@@@@@   person state change in camera {containerId}: {presence}')
            else:  # should be 'gone'
                self.person_position = -1
                self.heartrate.setText("---")
        elif containerId == 1:
            if presence == 'come':
                self.person_position = 0
                print(f'@@@@@   person state change in camera {containerId}: {presence}')
            else:  # should be 'gone'
                self.person_position = -1
                self.heartrate.setText("---")
        elif containerId == 2:  # cloud
            if presence == 'come':
                self.person_position = 0
                print(f'@@@@@   person state change in camera {containerId}: {presence}')
            else:  # should be 'gone'
                self.person_position = -1
        else:
            pass

    @pyqtSlot(str)
    def service_provision_anim(self, destination: str):
        self.queueFlag = 1
        if destination == "sp1":
            # self.service_step2.label.setVisible(True)
            self.service_step2.start("sp2")
        elif destination == "sp2":
            temp1, temp2, temp3 = 0, 0, 0
            if not self.monitor_q_cpu_hm_node1.empty():
                temp1 = self.monitor_q_cpu_hm_node1.get()[-1]
            else:
                self.queueFlag = 0
            if not self.monitor_q_cpu_hm_node2.empty():
                temp2 = self.monitor_q_cpu_hm_node2.get()[-1]
            else:
                self.queueFlag = 0
            if not self.monitor_q_cpu_hm_node3.empty():
                temp3 = self.monitor_q_cpu_hm_node3.get()[-1]
            else:
                self.queueFlag = 0
            temps = [temp1, temp2, temp3]
            print(f"------------------------------------------------------------------------------\n"
                  f">>>> Computing Addressing self.queueFlag is: {self.queueFlag}, CPU utilization's are: {temps} "
                  f"------------------------------------------------------------------------------\n")
            if self.queueFlag:
                self.path = temps.index(min(temps)) + 1
            if self.path == 1:
                self.service_step31.start("sp3")
                self.service_step31.QtSignals.anim_over.connect(self.on_animation_over)
            elif self.path == 2:
                self.service_step32.start("sp3")
                self.service_step32.QtSignals.anim_over.connect(self.on_animation_over)
            elif self.path == 3:
                self.service_step33.start("sp3")
                self.service_step33.QtSignals.anim_over.connect(self.on_animation_over)
        elif destination == "sp3":
            if self.path == 1:
                self.service_step41.start("sp4")
                self.c_node1_heart_rate.setVisible(True)
            elif self.path == 2:
                self.service_step42.start("sp4")
                self.c_node2_heart_rate.setVisible(True)
            elif self.path == 3:
                self.service_step43.start("sp4")
                self.c_node3_heart_rate.setVisible(True)
        elif destination == "sp4":
            if self.path == 1:
                self.service_step51.start("")
                self.c_node1_heart_rate.setVisible(True)
                self.cfn_manager.send_command(f'c_node{self.path}', 'task', 'cam_health camera_1')
            elif self.path == 2:
                self.service_step52.start("")
                self.c_node2_heart_rate.setVisible(True)
                self.cfn_manager.send_command(f'c_node{self.path}', 'task', 'cam_health camera_1')
            elif self.path == 3:
                self.service_step53.start("")
                self.c_node3_heart_rate.setVisible(True)
                self.cfn_manager.send_command(f'c_node{self.path}', 'task', 'cam_health camera_1')

    @pyqtSlot(int, str)
    def computingAddrWorkFlow(self):
        self.reset()
        self.service_step1.start("sp1")

    def on_animation_over(self, target_node):
        if self.path == 1:
            self.c_node1_heart_rate.setVisible(True)
        elif self.path == 2:
            self.c_node2_heart_rate.setVisible(True)
        elif self.path == 3:
            self.c_node3_heart_rate.setVisible(True)

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
        self.service_step31.tag_label.setVisible(False)
        self.service_step32.tag_label.setVisible(False)
        self.service_step33.tag_label.setVisible(False)
        self.service_step41.tag_label.setVisible(False)
        self.service_step42.tag_label.setVisible(False)
        self.service_step43.tag_label.setVisible(False)
        self.service_step51.tag_label.setVisible(False)
        self.service_step52.tag_label.setVisible(False)
        self.service_step53.tag_label.setVisible(False)
        self.service_step1.label.setVisible(False)
        self.service_step2.label.setVisible(False)
        self.service_step31.label.setVisible(False)
        self.service_step32.label.setVisible(False)
        self.service_step33.label.setVisible(False)
        self.service_step41.label.setVisible(False)
        self.service_step42.label.setVisible(False)
        self.service_step43.label.setVisible(False)
        self.service_step51.label.setVisible(False)
        self.service_step52.label.setVisible(False)
        self.service_step53.label.setVisible(False)
        self.c_node1_heart_rate.setVisible(False)
        self.c_node2_heart_rate.setVisible(False)
        self.c_node3_heart_rate.setVisible(False)

        self.step1_label1.setVisible(False)
        self.step1_label2.setVisible(False)
        self.cfn_manager.send_command('c_node1', 'stop_task', 'cam_health camera_1')
        self.cfn_manager.send_command('c_node2', 'stop_task', 'cam_health camera_1')
        self.cfn_manager.send_command('c_node3', 'stop_task', 'cam_health camera_1')

        self.stop_timer()
