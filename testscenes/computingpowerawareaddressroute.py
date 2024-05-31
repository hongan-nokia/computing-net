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
        # ComputingPowerAwareAddressRouteWindow
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
        self._initHeapMap()
        self._initImageLoad()
        self._initWarningBtn()
        self.initConnections()
        # self._initHearRate()
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

        c_node1_video_img = QtGui.QPixmap("./images/video_conversion.png").scaled(QSize(80, 60))
        c_node2_video_img = QtGui.QPixmap("./images/video_conversion.png").scaled(QSize(80, 60))
        c_node3_video_img = QtGui.QPixmap("./images/video_conversion.png").scaled(QSize(80, 60))
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
                                        interval=3, title='2.寻址请求', tag_geo=[170, 32, 150, 20])
        self.net_brain_ctrl = ImageLoader(parent=self, geo=[1360, 440, 443, 100],
                                          image_url='./images_test3/server_addressing_step3.png',
                                          img_scale_w=200,
                                          img_scale_h=3,
                                          direction="l2r",
                                          interval=3, title='3.算网融合调度编排', tag_geo=[90, 0, 200, 20])
        self.net_route_ctrl = ImageLoader(parent=self, geo=[880, 550, 476, 170],
                                          image_url='./images_test3/server_addressing_step41.png',
                                          img_scale_w=475,
                                          img_scale_h=75,
                                          direction="r2l",
                                          interval=3, title='4.网络路径控制', tag_geo=[280, 20, 200, 30])
        self.video_stream = ImageLoader(parent=self, geo=[320, 460, 550, 120],
                                        image_url='./images_test3/server_addressing_step51.png',
                                        img_scale_w=550,
                                        img_scale_h=120,
                                        direction="r2l",
                                        interval=3, title='5.视频传输数据', tag_geo=[20, 80, 200, 30])
        self.startAITrainer = ImageLoader(parent=self, geo=[779, 283, 400, 100],
                                          image_url='./images_test3/server_addressing_step3.png',
                                          img_scale_w=200,
                                          img_scale_h=3,
                                          direction="l2r",
                                          interval=3, title='6. 启动一计算密集型应用', tag_geo=[90, 0, 200, 20])
        self.reScheduling = ImageLoader(parent=self, geo=[1433, 342, 290, 100],
                                        image_url='./images_test3/server_addressing_step3.png',
                                        img_scale_w=200,
                                        img_scale_h=3,
                                        direction="l2r",
                                        interval=3, title='7. 感知算力变化，重新寻址调度编排', tag_geo=[90, 0, 180, 50])
        self.selNewService1 = ImageLoader(parent=self, geo=[1211, 541, 500, 300],
                                          image_url='./images_test3/scene1_step81.png',
                                          img_scale_w=350,
                                          img_scale_h=75,
                                          direction="r2l",
                                          interval=3, title='8. 选择新服务实例，完成网络路径控制',
                                          tag_geo=[300, 100, 200, 50])
        self.selNewService2 = ImageLoader(parent=self, geo=[1139, 617, 443, 300],
                                          image_url='./images/choose_new_svc.png',
                                          img_scale_w=410,
                                          img_scale_h=260,
                                          direction="r2l",
                                          interval=3, title='8. 选择新服务实例，完成网络路径控制',
                                          tag_geo=[90, 200, 200, 50])
        self.finalServiceProvideByNode2 = ImageLoader(parent=self, geo=[327, 510, 810, 280],
                                                      image_url='./images_test3/scene1_step91.png',
                                                      img_scale_w=810,
                                                      img_scale_h=280,
                                                      direction="r2l",
                                                      interval=3, title='',
                                                      tag_geo=[90, 0, 200, 20])
        self.finalServiceProvideByNode3 = ImageLoader(parent=self, geo=[327, 501, 755, 394],
                                                      image_url='./images_test3/scene1_step92.png',
                                                      img_scale_w=755,
                                                      img_scale_h=394,
                                                      direction="r2l",
                                                      interval=3, title='',
                                                      tag_geo=[90, 0, 200, 20])

    def _initWarningBtn(self):
        warning_icon_img = QtGui.QPixmap("./images_test3/warning.svg").scaled(QSize(80, 80))
        self.warning_icon = BlinkingPic(parent=self, pixmap=warning_icon_img, auto_dim=True, dim_opacity=0.1,
                                         blink_period=1200).pixmap_item

        self.view.scene().addItem(self.warning_icon)
        self.warning_icon.setPos(950, 350)
        self.warning_icon.start_blink()
        self.warning_icon.setVisible(True)

        self.warning_btn = QPushButton()
        self.warning_btn.setGeometry(950,350, 80, 80)
        self.warning_btn.setStyleSheet("background-color: rgba(240, 240, 240, 0);")
        self.warning_btn.clicked.connect(self.warning_event)
        self.warning_btn.raise_()
        self.view.scene().addWidget(self.warning_btn)

    def warning_event(self):
        # self.warning_icon.setVisible(False)
        pass

    def initConnections(self):
        # self.cfn_manager.signal_emitter.QtSignals.container_pulsate_update.connect(self.update_pulserate)
        # self.cfn_manager.signal_emitter.QtSignals.container_person_state.connect(self.show_person_position)
        self.cfn_manager.signal_emitter.QtSignals.firstPkgLat_test.connect(self.firstPkgLatWorkFlow)
        self.cfn_manager.signal_emitter.QtSignals.vlc_state_report.connect(self.VLC_migration)
        self.user_first_pkg.QtSignals.anim_over.connect(self.service_provision_anim)
        self.addr_request.QtSignals.anim_over.connect(self.service_provision_anim)
        self.net_brain_ctrl.QtSignals.anim_over.connect(self.service_provision_anim)
        self.net_route_ctrl.QtSignals.anim_over.connect(self.service_provision_anim)
        self.video_stream.QtSignals.anim_over.connect(self.service_provision_anim)
        self.startAITrainer.QtSignals.anim_over.connect(self.service_provision_anim)
        self.reScheduling.QtSignals.anim_over.connect(self.service_provision_anim)
        self.selNewService1.QtSignals.anim_over.connect(self.service_provision_anim)
        self.selNewService2.QtSignals.anim_over.connect(self.service_provision_anim)
        self.finalServiceProvideByNode2.QtSignals.anim_over.connect(self.service_provision_anim)
        self.finalServiceProvideByNode3.QtSignals.anim_over.connect(self.service_provision_anim)

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

    @pyqtSlot(str)
    def service_provision_anim(self, destination: str):
        print(f"destination is: {destination}")
        self.queueFlag = 1
        if destination == "sc1_sp1":
            self.user_first_pkg.setVisible(True)
            self.addr_request.setVisible(True)
            # self.addr_request.label.setVisible(True)
            self.addr_request.start("sc1_sp2")
        elif destination == "sc1_sp2":
            # self.net_brain_ctrl.label.setVisible(True)
            self.net_brain_ctrl.start("sc1_sp3")
        elif destination == "sc1_sp3":
            # self.net_route_ctrl.label.setVisible(True)
            self.net_route_ctrl.start("sc1_sp4")
        elif destination == "sc1_sp4":
            # self.video_stream.label.setVisible(True)
            self.video_stream.start("")
        elif destination == "sc1_sp6":
            print("sc1_sp7 sc1_sp7 sc1_sp7")
            # self.reScheduling.label.setVisible(True)
            self.reScheduling.start("sc1_sp7")
        elif destination == "sc1_sp7":
            print("sc1_sp8 sc1_sp8 sc1_sp8")
            temps = [0, 0]
            if not self.monitor_q_cpu_hm_node2.empty():
                temp2 = self.monitor_q_cpu_hm_node1.get()[-1]
            else:
                self.queueFlag = 0
            if not self.monitor_q_cpu_hm_node3.empty():
                temp3 = self.monitor_q_cpu_hm_node1.get()[-1]
            else:
                self.queueFlag = 0

            if self.queueFlag:
                temps = [temp2, temp3]
                self.path = temps.index(min(temps)) + 1
            # self.path = 1

            if self.path == 1:
                # self.selNewService1.label.setVisible(True)
                self.selNewService1.start("sc1_sp8")
            elif self.path == 2:
                # self.selNewService2.label.setVisible(True)
                self.selNewService2.start("sc1_sp8")

        elif destination == "sc1_sp8":
            if self.path == 1:
                self.cfn_manager.send_command("c_node1", "stop_task", "vlc worldCup.mp4_0")
                # self.finalServiceProvideByNode2.label.setVisible(True)
                self.finalServiceProvideByNode2.start("")
            elif self.path == 2:
                # self.finalServiceProvideByNode3.label.setVisible(True)
                self.finalServiceProvideByNode3.start("")
                self.cfn_manager.send_command("c_node1", "stop_task", "vlc worldCup.mp4_0")
        else:
            pass

    @pyqtSlot(int, str)
    def firstPkgLatWorkFlow(self, node_id, command_args):
        print("Here is firstPkgLatWorkFlow")
        self.user_first_pkg.start("sc1_sp1")
        self._sendFirstPkg2UE()
        # self.cfn_manager.send_command("c_node1", "task", "send_pkg2ue")

    @pyqtSlot(int, float)
    def update_pulserate(self, containerId: int, pulserate: float):
        if pulserate == -1:
            pass
        else:
            self.heartrate.setText('%.0f' % pulserate)
        print(f'container={containerId}, '
              f'person_position={self.person_position}, pulserate={pulserate}, cnt={self._heartrate_update_cnt}')

    @pyqtSlot(int, str)
    def show_person_position(self, containerId: int, presence: str):
        """ When person comes in or go out of a camera's view, it triggers a
            signal with corresponding container id and 'come' or 'gone' flag.
            This function therefore triggers animation of the person's picture.
        """
        print(f'person state change in camera {containerId}: {presence}')
        print(f'self.work_mode:  {self.work_mode}')
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

    def _sendFirstPkg2UE(self):
        print("Here is _sendFirstPkg2UE")
        # client_host = self.cfn_manager.demo_config.get_node('client')['node_ip']
        # # client_host = "127.0.0.1"
        # client_port = 12354
        # client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # message = "RESPONSE FROM C-NODE1"
        # sleep(0.1)
        # try:
        #     client_socket.connect((client_host, client_port))
        # except Exception as exp:
        #     print(f"*&&&&&&&&&&&&&&& {exp}")
        # try:
        #     client_socket.sendall(message.encode())
        # except Exception as exp:
        #     print(f"*-------------- {exp}")
        # print("FirstPkg Message Sent")
        # client_socket.close()
        self.cfn_manager.send_command("c_node1", "task", "sendFirstPkg up")
        self.cfn_manager.send_command("c_node1", "task", "vlc worldCup.mp4_0")

    def deployAITrainerOnCNode1(self):
        self.cfn_manager.send_command("c_node1", "task", "AI_trainer1 up")
        self.startAITrainer.label.setVisible(True)
        self.startAITrainer.start("sc1_sp6")

    @pyqtSlot(int, str)
    def VLC_migration(self, containerId: int, current_position: str):
        """ This slot is only triggered when the container sends in a 'state' message.
                    to check the current streaming position of source VLC-server, and send a command
                    to the target VLC-server to continue the streaming work.
                """
        # print(f' VLC_migration reported streaming position: {current_position}')
        # self.cfn_manager.send_command(f'c_node{self.path + 1}', 'task', 'vlc worldCup.mp4_' + current_position)
        if self.cfn_manager.node_names[containerId] == 'c_node1' and self.path == 1:
            self.cfn_manager.send_command('c_node2', 'task', 'vlc worldCup.mp4_' + current_position)
        elif self.cfn_manager.node_names[containerId] == 'c_node1' and self.path == 2:
            self.cfn_manager.send_command('c_node3', 'task', 'vlc worldCup.mp4_' + current_position)

    def reset(self):
        self.user_first_pkg.tag_label.setVisible(False)
        self.addr_request.tag_label.setVisible(False)
        self.net_brain_ctrl.tag_label.setVisible(False)
        self.net_route_ctrl.tag_label.setVisible(False)
        self.video_stream.tag_label.setVisible(False)
        self.startAITrainer.tag_label.setVisible(False)
        self.reScheduling.tag_label.setVisible(False)
        self.selNewService1.tag_label.setVisible(False)
        self.selNewService2.tag_label.setVisible(False)
        self.finalServiceProvideByNode2.tag_label.setVisible(False)
        self.finalServiceProvideByNode3.tag_label.setVisible(False)

        self.user_first_pkg.label.setVisible(False)
        self.addr_request.label.setVisible(False)
        self.net_brain_ctrl.label.setVisible(False)
        self.net_route_ctrl.label.setVisible(False)
        self.video_stream.label.setVisible(False)
        self.startAITrainer.label.setVisible(False)
        self.reScheduling.label.setVisible(False)
        self.selNewService1.label.setVisible(False)
        self.selNewService2.label.setVisible(False)
        self.finalServiceProvideByNode2.label.setVisible(False)
        self.finalServiceProvideByNode3.label.setVisible(False)

        self.cfn_manager.send_command("c_node1", "stop_task", "AI_trainer1 up")
        self.cfn_manager.send_command("c_node1", "stop_task", "vlc worldCup.mp4_0")
        self.cfn_manager.send_command("c_node2", "stop_task", "vlc worldCup.mp4")
        self.cfn_manager.send_command('c_node3', 'stop_task', 'vlc worldCup.mp4')
