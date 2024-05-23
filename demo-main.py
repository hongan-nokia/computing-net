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
        super().__init__()  # QtWidgets.QMainWindow.__init__(self)
        self.hm_tag = 0
        self.container_mng = None
        self.is_scenario3 = False
        self.is_scenario2 = False
        self.flow_priority = 40100
        self.curNodeList = []
        geo = {
            'top': 0,
            'left': 0,
            'width': 1920,
            'height': 1080}
        self.setGeometry(geo['left'], geo['top'], geo['width'], geo['height'])
        self.pre_onos_port = -1
        self.nokia_blue = QtGui.QColor(18, 65, 145)
        self.cfn_manager = demo_manager
        self.node_names = demo_manager.node_names
        self.res_q = Queue(10000)
        self.exit_dialog = ExitDialog()
        self._initMonitorQueue()
        self._initView()
        self._initMainTitle()
        self._initServiceDeployment()
        self.initConnections()
        self._initShowServiceResource()  # 展示用户算力请求信息
        self._initDataVisualize()
        self._initScenarioButtons()
        self._initFlowCtrlButtons()
        self._initHeatMaps()
        self._initScenariosSwitchButtons()
        self._initServiceScenarios()
        self.mouse = PyWinMouse.Mouse()
        self.mouse_pos_mon = repeatTimer(1, self.get_mouse_position, autostart=True)
        self.mouse_pos_mon.start()
        self.ue_message_getter = repeatTimer(1, self.ue_msg_receiver, autostart=True)
        self.ue_message_getter.start()
        self.serviceResourceInfo_hide_timer = QTimer(self)
        self.serviceResourceInfo_hide_timer.setInterval(10000 * 6)
        self.serviceResourceInfo_hide_timer.timeout.connect(self.serviceResourceInfo.hide)
        self.cfn_manager.send_command('jump_server', 'task', 'cfnres report')

    # def _initServiceDeployment(self):
    #     self.primaryWidget = RectangleWidget(parent=self, color=QColor(55, 204, 115))
    #     self.primaryWidget.setGeometry(0, 60, 605, 365)
    #     self.primaryWidget.setPalette(QPalette(QColor(255, 255, 255)))
    #     self.primaryWidget.setStyleSheet("background-color: white;")
    #     self.primaryLayout = QHBoxLayout()
    #     self.primaryWidget.setLayout(self.primaryLayout)
    #
    #     self.SDW = ServiceDeploymentWidgetCN(self.cfn_manager, self.res_q, self.monitor_q_net_list)
    #     self.primaryLayout.addWidget(self.SDW)
    #     self.primaryWidget.setVisible(False)

    def _initShowServiceResource(self):
        # 表格

        self.serviceResourceInfo = QtWidgets.QTableWidget(self)
        self.serviceResourceInfo.setGeometry(90, 450, 200, 182)
        self.serviceResourceInfo.setColumnCount(1)
        self.serviceResourceInfo.setRowCount(4)

        # "Live Broadcast", "1.216 Gflops", "127.4 MB", "1.1 Mbps"

        self.serviceResourceInfo.setItem(0, 0, QTableWidgetItem("Live Broadcast"))
        self.serviceResourceInfo.setItem(1, 0, QTableWidgetItem("CPU: 1.216 Gflops"))
        self.serviceResourceInfo.setItem(2, 0, QTableWidgetItem("MEM: 127.4 MB"))
        self.serviceResourceInfo.setItem(3, 0, QTableWidgetItem("BW: 1.1 Mbps"))

        self.serviceResourceInfo.setColumnWidth(0, 200)

        font = QtGui.QFont("Arial", 10, QtGui.QFont.Bold)
        self.serviceResourceInfo.item(0, 0).setBackground(QColor(0, 191, 255))
        self.serviceResourceInfo.item(0, 0).setFont(font)
        self.serviceResourceInfo.item(0, 0).setTextAlignment(Qt.AlignCenter)
        self.serviceResourceInfo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.serviceResourceInfo.horizontalHeader().setVisible(False)  # 隐藏列索引
        self.serviceResourceInfo.verticalHeader().setVisible(False)
        self.serviceResourceInfo.hide()
        self.serviceResourceInfo.setEditTriggers(QTableWidget.NoEditTriggers)

    # def hide_serviceResourceInfo(self):
    #     self.serviceResourceInfo.hide()

    def _initDataVisualize(self):
        self.data_visual = data_visualize(parent=self, bw_list=self.monitor_q_net_list)
        self.data_visual.setVisible(False)

    # from scenario3 switch to scenario2, need switch the background?
    def _serviceDeploymentShow(self):
        # self.cfn_manager.send_command('jump_server', 'task', 'cfnres report')
        if not self.is_scenario2 and not self.is_scenario3:
            self.is_scenario2 = True
            self.is_scenario3 = False
            self.primaryWidget.setVisible(True)
            self.view.setBackgroundBrush(QtGui.QBrush(QtGui.QImage('./front_page/img/cfn_cn_bk.png')))
        elif self.is_scenario2 and self.primaryWidget.isHidden():
            self.primaryWidget.setVisible(True)
        elif self.is_scenario2 and self.primaryWidget.isVisible():
            self.primaryWidget.setVisible(False)
        # if self.primaryWidget.isVisible():
        #     self.primaryWidget.setVisible(False)
        # elif self.is_scenario2:
        #     self.primaryWidget.setVisible(True)
        elif self.is_scenario3:
            self.is_scenario3 = False
            self.pre_onos_port = -1
            self.node1_flow_btn.setChecked(False)
            self.node2_flow_btn.setChecked(False)
            self.node3_flow_btn.setChecked(False)
            self.auto_flow_btn.setChecked(False)
            self.cfn_manager.send_command('neat_host', 'task',
                                          f'onos_add_all 224.10.10.0#224.20.10.0#224.30.10.0#224.40.10.0')
            self.view.setBackgroundBrush(QtGui.QBrush(QtGui.QImage('./front_page/img/cfn_cn_bk.png')))
            self.primaryWidget.setVisible(True)
            self.is_scenario2 = True
        else:
            self.primaryWidget.setVisible(True)

    def _resourceAwarenessShow(self):
        if self.data_visual.isVisible():
            self.data_visual.setVisible(False)
            self.data_visual.history1.setVisible(False)
            self.data_visual.history2.setVisible(False)
            self.data_visual.history3.setVisible(False)
        else:
            # self.cfn_manager.send_command('jump_server', 'task', 'cfnres report')
            self.data_visual.show()
        if self.flow_btn_widget.isVisible():
            self.flow_btn_widget.setVisible(False)
        if self.hm_tag:
            self._ocp_cpu_hm.setVisible(False)
            self._worker1_cpu_hm.setVisible(False)
            self._worker2_cpu_hm.setVisible(False)
            self.CFN_Service_Dep_btn.setVisible(False)
            self.CFN_Stream_Ctrl_btn.setVisible(False)
            self.hm_tag = 0
        else:
            self._ocp_cpu_hm.setVisible(True)
            self._worker1_cpu_hm.setVisible(True)
            self._worker2_cpu_hm.setVisible(True)
            self.CFN_Service_Dep_btn.setVisible(True)
            self.CFN_Stream_Ctrl_btn.setVisible(True)
            self.hm_tag = 1

    def _initView(self):
        self.setWindowTitle(" ")
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.view = QtWidgets.QGraphicsView(parent=self)
        self.view.setBackgroundBrush(QtGui.QBrush(QtGui.QImage('./front_page/img/cfn_cn_bk.png')))
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
        scene = QtWidgets.QGraphicsScene()
        self.master_s1 = BlinkingPic(QtGui.QPixmap("./front_page/img/Live.png"), auto_dim=True,
                                     dim_opacity=0.1).pixmap_item
        self.master_s2 = BlinkingPic(QtGui.QPixmap("./front_page/img/Learning.png"), auto_dim=True,
                                     dim_opacity=0.1).pixmap_item
        self.master_s3 = BlinkingPic(QtGui.QPixmap("./front_page/img/Surveillance.png"), auto_dim=True,
                                     dim_opacity=0.1).pixmap_item
        self.master_s4 = BlinkingPic(QtGui.QPixmap("./front_page/img/Brain.png"), auto_dim=True,
                                     dim_opacity=0.1).pixmap_item

        self.worker1_s1 = BlinkingPic(QtGui.QPixmap("./front_page/img/Live.png"), auto_dim=True,
                                      dim_opacity=0.1).pixmap_item
        self.worker1_s2 = BlinkingPic(QtGui.QPixmap("./front_page/img/Learning.png"), auto_dim=True,
                                      dim_opacity=0.1).pixmap_item
        self.worker1_s3 = BlinkingPic(QtGui.QPixmap("./front_page/img/Surveillance.png"), auto_dim=True,
                                      dim_opacity=0.1).pixmap_item
        self.worker1_s4 = BlinkingPic(QtGui.QPixmap("./front_page/img/Brain.png"), auto_dim=True,
                                      dim_opacity=0.1).pixmap_item

        self.worker2_s1 = BlinkingPic(QtGui.QPixmap("./front_page/img/Live.png"), auto_dim=True,
                                      dim_opacity=0.1).pixmap_item
        self.worker2_s2 = BlinkingPic(QtGui.QPixmap("./front_page/img/Learning.png"), auto_dim=True,
                                      dim_opacity=0.1).pixmap_item
        self.worker2_s3 = BlinkingPic(QtGui.QPixmap("./front_page/img/Surveillance.png"), auto_dim=True,
                                      dim_opacity=0.1).pixmap_item
        self.worker2_s4 = BlinkingPic(QtGui.QPixmap("./front_page/img/Brain.png"), auto_dim=True,
                                      dim_opacity=0.1).pixmap_item

        self.link_crowded = BlinkingPic(QtGui.QPixmap("./front_page/img/link_crowd.png"), auto_dim=True,
                                        dim_opacity=0.1).pixmap_item

        self.oc_cpu_hm_l1 = QtWidgets.QLabel(parent=self)
        self.oc_cpu_hm_l2 = QtWidgets.QLabel(parent=self)
        self.oc_cpu_hm_l3 = QtWidgets.QLabel(parent=self)
        self.oc_cpu_hm_l1.setText("0%")
        self.oc_cpu_hm_l2.setText("100%")
        self.oc_cpu_hm_l3.setText("cpu")
        self.oc_cpu_hm_l1.setGeometry(485, 610, 20, 10)
        self.oc_cpu_hm_l2.setGeometry(480, 540, 30, 10)
        self.oc_cpu_hm_l3.setGeometry(502, 615, 20, 20)

        self.w1_cpu_hm_l1 = QtWidgets.QLabel(parent=self)
        self.w1_cpu_hm_l2 = QtWidgets.QLabel(parent=self)
        self.w1_cpu_hm_l3 = QtWidgets.QLabel(parent=self)
        self.w1_cpu_hm_l1.setText("0%")
        self.w1_cpu_hm_l2.setText("100%")
        self.w1_cpu_hm_l3.setText("cpu")
        self.w1_cpu_hm_l1.setGeometry(1381, 735, 20, 10)
        self.w1_cpu_hm_l2.setGeometry(1376, 665, 30, 10)
        self.w1_cpu_hm_l3.setGeometry(1398, 740, 20, 20)

        self.w2_cpu_hm_l1 = QtWidgets.QLabel(parent=self)
        self.w2_cpu_hm_l2 = QtWidgets.QLabel(parent=self)
        self.w2_cpu_hm_l3 = QtWidgets.QLabel(parent=self)
        self.w2_cpu_hm_l1.setText("0%")
        self.w2_cpu_hm_l2.setText("100%")
        self.w2_cpu_hm_l3.setText("cpu")
        self.w2_cpu_hm_l1.setGeometry(1370, 450, 20, 10)
        self.w2_cpu_hm_l2.setGeometry(1365, 380, 30, 10)
        self.w2_cpu_hm_l3.setGeometry(1387, 455, 20, 20)

        scene.addWidget(self.oc_cpu_hm_l1)
        scene.addWidget(self.oc_cpu_hm_l2)
        scene.addWidget(self.oc_cpu_hm_l3)
        scene.addWidget(self.w1_cpu_hm_l1)
        scene.addWidget(self.w1_cpu_hm_l2)
        scene.addWidget(self.w1_cpu_hm_l3)
        scene.addWidget(self.w2_cpu_hm_l1)
        scene.addWidget(self.w2_cpu_hm_l2)
        scene.addWidget(self.w2_cpu_hm_l3)

        scene.addItem(self.master_s1)
        scene.addItem(self.master_s2)
        scene.addItem(self.master_s3)
        scene.addItem(self.master_s4)
        scene.addItem(self.worker1_s1)
        scene.addItem(self.worker1_s2)
        scene.addItem(self.worker1_s3)
        scene.addItem(self.worker1_s4)
        scene.addItem(self.worker2_s1)
        scene.addItem(self.worker2_s2)
        scene.addItem(self.worker2_s3)
        scene.addItem(self.worker2_s4)
        scene.addItem(self.link_crowded)

        self.master_s1.setPos(QtCore.QPointF(430, 850))
        self.master_s2.setPos(QtCore.QPointF(530, 854))
        self.master_s3.setPos(QtCore.QPointF(610, 852))
        self.master_s4.setPos(QtCore.QPointF(355, 852))
        self.worker1_s1.setPos(QtCore.QPointF(1550, 900))
        self.worker1_s2.setPos(QtCore.QPointF(1650, 904))
        self.worker1_s3.setPos(QtCore.QPointF(1730, 902))
        self.worker1_s4.setPos(QtCore.QPointF(1475, 902))
        self.worker2_s1.setPos(QtCore.QPointF(1580, 300))
        self.worker2_s2.setPos(QtCore.QPointF(1680, 304))
        self.worker2_s3.setPos(QtCore.QPointF(1760, 302))
        self.worker2_s4.setPos(QtCore.QPointF(1505, 302))
        self.link_crowded.setPos(QtCore.QPointF(1228, 670))

        self.master_s1.setVisible(False)
        self.master_s2.setVisible(False)
        self.master_s3.setVisible(False)
        self.master_s4.setVisible(False)
        self.worker1_s1.setVisible(False)
        self.worker1_s2.setVisible(False)
        self.worker1_s3.setVisible(False)
        self.worker1_s4.setVisible(False)
        self.worker2_s1.setVisible(False)
        self.worker2_s2.setVisible(False)
        self.worker2_s3.setVisible(False)
        self.worker2_s4.setVisible(False)
        self.link_crowded.setVisible(False)

        return scene

    def _initMainTitle(self):
        self.mainTitle = QtWidgets.QLabel(parent=self)
        self.mainTitle.setText("")
        font = QtGui.QFont("Arial", 30, QtGui.QFont.Bold)
        self.mainTitle.setFont(font)
        self.mainTitle.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignCenter)  # Qt.AlignRight
        palette = self.palette()
        palette.setColor(self.foregroundRole(), self.nokia_blue)
        self.mainTitle.setPalette(palette)
        self.mainTitle.setGeometry(465, 30, 965, 69)
        self.mainTitle.raise_()

    def _initMonitorQueue(self):
        self.monitor_q_net_node1 = self.cfn_manager.resource_StatMon['node1_bw']  # 算力节点1 带宽
        self.monitor_q_net_node2 = self.cfn_manager.resource_StatMon['node2_bw']  # 算力节点2 带宽
        self.monitor_q_net_node3 = self.cfn_manager.resource_StatMon['node3_bw']  # 算力节点3 带宽
        self.monitor_q_net_list = [self.monitor_q_net_node1, self.monitor_q_net_node2, self.monitor_q_net_node3]
        self.monitor_ocp_cpu_hm = Queue(10000)
        self.monitor_w1_cpu_hm = Queue(10000)
        self.monitor_w2_cpu_hm = Queue(10000)

    def initConnections(self):

        self.exit_dialog.okButton.clicked.connect(self.elegantQuit)
        self.SDW.QtSignals.service_deploy.connect(self.update_service_deploy_info)

        self.cfn_manager.signal_emitter.QtSignals.container_connected.connect(self.slaver_info_init)
        self.cfn_manager.signal_emitter.QtSignals.container_resource_report.connect(self.cfn_data_report)
        self.cfn_manager.signal_emitter.QtSignals.container_task_list.connect(self.show_node_list)
        self.cfn_manager.signal_emitter.QtSignals.container_ue_msg.connect(self.ue_msg_handler)
        self.cfn_manager.signal_emitter.QtSignals.container_service_deploy.connect(self.slave_service_management)

    def _initScenarioButtons(self):
        btn_font = QtGui.QFont("微软雅黑", 18, QtGui.QFont.Bold)
        self.net_compute_aware_btn = QPushButton(parent=self)
        self.net_compute_aware_btn.setText("资源感知")
        self.net_compute_aware_btn.setFont(btn_font)
        self.net_compute_aware_btn.setGeometry(40, 990, 378, 60)
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
        self.service_deploy_btn.clicked.connect(self._serviceDeploymentShow)
        self.dynamic_scheduling_btn.clicked.connect(self._switchScenario3)

        self.net_compute_aware_btn.show()
        self.service_deploy_btn.show()
        self.dynamic_scheduling_btn.show()

    def _switchScenario3(self):
        if self.flow_btn_widget.isVisible():
            self.flow_btn_widget.setVisible(False)
        else:
            self.flow_btn_widget.setVisible(True)

    def _initFlowCtrlButtons(self):
        self.flow_btn_widget = QtWidgets.QWidget(self)
        self.flow_btn_h_layout = QHBoxLayout(self.flow_btn_widget)
        flow_btn_font = QtGui.QFont("Arial", 15, 15, QtGui.QFont.Bold)
        self.flow_btn_v_layout1 = QVBoxLayout()
        self.flow_btn_v_layout2 = QVBoxLayout()
        self.node1_flow_btn = QtWidgets.QRadioButton('Node1', parent=self.flow_btn_widget)
        self.node2_flow_btn = QtWidgets.QRadioButton('Node2', parent=self.flow_btn_widget)
        self.node3_flow_btn = QtWidgets.QRadioButton('Node3', parent=self.flow_btn_widget)
        self.auto_flow_btn = QtWidgets.QRadioButton('Auto', parent=self.flow_btn_widget)
        self.node1_flow_btn.setFont(flow_btn_font)
        self.node2_flow_btn.setFont(flow_btn_font)
        self.node3_flow_btn.setFont(flow_btn_font)
        self.auto_flow_btn.setFont(flow_btn_font)

        self.flow_btn_v_layout1.addWidget(self.node1_flow_btn)
        self.flow_btn_v_layout1.addWidget(self.node3_flow_btn)
        self.flow_btn_v_layout2.addWidget(self.node2_flow_btn)
        self.flow_btn_v_layout2.addWidget(self.auto_flow_btn)
        self.flow_btn_h_layout.addLayout(self.flow_btn_v_layout1)
        self.flow_btn_h_layout.addLayout(self.flow_btn_v_layout2)
        self.flow_btn_widget.setGeometry(1160, 880, 300, 90)
        self.flow_btn_widget.setFixedSize(300, 90)
        self.node1_flow_btn.toggled.connect(lambda: self._flow_ctrl(self.node1_flow_btn))
        self.node2_flow_btn.toggled.connect(lambda: self._flow_ctrl(self.node2_flow_btn))
        self.node3_flow_btn.toggled.connect(lambda: self._flow_ctrl(self.node3_flow_btn))
        self.auto_flow_btn.toggled.connect(lambda: self._flow_ctrl(self.auto_flow_btn))
        self.flow_btn_widget.setVisible(False)

    def _flow_ctrl(self, btn):
        if not self.is_scenario3:
            self.is_scenario3 = True
            self.is_scenario2 = False
            self.cfn_manager.send_command('neat_host', 'task', f'onos_del_all 224.10.10.0#224.20.10.0#224.30.10.0')

        if btn.text() == 'Node1':
            if btn.isChecked():
                print(btn.text() + " is selected")
                self.flow_priority += 10
                self.view.setBackgroundBrush(QtGui.QBrush(QtGui.QImage('./front_page/img/cfn_cn_bk_s1.png')))
                self.cfn_manager.send_command('neat_host', 'task',
                                              f'onos 224.10.10.0#12#{self.pre_onos_port}#6#{self.flow_priority}')
                self.cfn_manager.send_command('neat_host', 'task',
                                              f'onos 224.20.10.0#12#{self.pre_onos_port}#6#{self.flow_priority}')
                self.cfn_manager.send_command('neat_host', 'task',
                                              f'onos 224.30.10.0#12#{self.pre_onos_port}#6#{self.flow_priority}')
                self.pre_onos_port = 6
            else:
                print(btn.text() + " is deselected")
        elif btn.text() == 'Node2':  # worker1
            if btn.isChecked():
                print(btn.text() + " is selected")
                self.flow_priority += 10
                self.view.setBackgroundBrush(QtGui.QBrush(QtGui.QImage('./front_page/img/cfn_cn_bk_s2.png')))
                self.cfn_manager.send_command('neat_host', 'task',
                                              f'onos 224.10.10.0#12#{self.pre_onos_port}#10#{self.flow_priority}')
                self.cfn_manager.send_command('neat_host', 'task',
                                              f'onos 224.20.10.0#12#{self.pre_onos_port}#10#{self.flow_priority}')
                self.cfn_manager.send_command('neat_host', 'task',
                                              f'onos 224.30.10.0#12#{self.pre_onos_port}#10#{self.flow_priority}')
                self.pre_onos_port = 10
            else:
                print(btn.text() + " is deselected")
        elif btn.text() == 'Node3':  # worker1
            if btn.isChecked():
                print(btn.text() + " is selected")
                self.flow_priority += 10
                self.view.setBackgroundBrush(QtGui.QBrush(QtGui.QImage('./front_page/img/cfn_cn_bk_s3.png')))
                self.cfn_manager.send_command('neat_host', 'task',
                                              f'onos 224.10.10.0#12#{self.pre_onos_port}#8#{self.flow_priority}')
                self.cfn_manager.send_command('neat_host', 'task',
                                              f'onos 224.20.10.0#12#{self.pre_onos_port}#8#{self.flow_priority}')
                self.cfn_manager.send_command('neat_host', 'task',
                                              f'onos 224.30.10.0#12#{self.pre_onos_port}#8#{self.flow_priority}')
                self.pre_onos_port = 8
            else:
                print(btn.text() + " is deselected")

        elif btn.text() == 'Auto':  # Auto == worker2
            if btn.isChecked():
                print(btn.text() + " is selected")
                self.flow_priority += 10
                self.view.setBackgroundBrush(QtGui.QBrush(QtGui.QImage('./front_page/img/cfn_cn_bk_s2.png')))
                self.cfn_manager.send_command('neat_host', 'task',
                                              f'onos 224.10.10.0#12#{self.pre_onos_port}#10#{self.flow_priority}')
                self.cfn_manager.send_command('neat_host', 'task',
                                              f'onos 224.20.10.0#12#{self.pre_onos_port}#10#{self.flow_priority}')
                self.cfn_manager.send_command('neat_host', 'task',
                                              f'onos 224.30.10.0#12#{self.pre_onos_port}#10#{self.flow_priority}')
                self.pre_onos_port = 10
            else:
                print(btn.text() + " is deselected")

    def _initHeatMaps(self):

        self._ocp_cpu_hm = HeatMap(parent=self, geo=[500, 550, 40, 80], interval=1500, data_q=self.monitor_ocp_cpu_hm)
        self._worker1_cpu_hm = HeatMap(parent=self, geo=[1396, 675, 40, 80], interval=1500,
                                       data_q=self.monitor_w1_cpu_hm)
        self._worker2_cpu_hm = HeatMap(parent=self, geo=[1385, 390, 40, 80], interval=1500,
                                       data_q=self.monitor_w2_cpu_hm)
        # self.ocp_cpu_hm.setWindowFlags(Qt.WindowStaysOnTopHint)
        # self.worker1_cpu_hm.setWindowFlags(Qt.WindowStaysOnTopHint)
        # self.worker2_cpu_hm.setWindowFlags(Qt.WindowStaysOnTopHint)
        self._ocp_cpu_hm.timer.start()
        self._worker1_cpu_hm.timer.start()
        self._worker2_cpu_hm.timer.start()
        self._ocp_cpu_hm.setHidden(False)
        self._worker1_cpu_hm.setHidden(False)
        self._worker2_cpu_hm.setHidden(False)
        self.hm_tag = 1

    def _initScenariosSwitchButtons(self):
        btn_font = QtGui.QFont("微软雅黑", 26, QtGui.QFont.Bold)
        self.CFN_Service_Dep_btn = QPushButton(parent=self)
        self.CFN_Service_Dep_btn.setText("算网大脑/编排器")
        self.CFN_Service_Dep_btn.setFont(btn_font)
        self.CFN_Service_Dep_btn.setGeometry(814, 204, 270, 50)
        self.CFN_Service_Dep_btn.setFlat(True)
        self.CFN_Service_Dep_btn.setStyleSheet(
            "border-radius:8px;color:gray;border-style:outset;border:none;background-color: {}".format(
                QColor(242, 242, 242).name()))
        # palette = self.CFN_Service_Dep_btn.palette()
        # palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        # self.CFN_Service_Dep_btn.setPalette(palette)

        self.CFN_Stream_Ctrl_btn = QPushButton(parent=self)
        self.CFN_Stream_Ctrl_btn.setGeometry(141, 609, 95, 110)
        self.CFN_Stream_Ctrl_btn.setFlat(True)
        self.CFN_Stream_Ctrl_btn.setStyleSheet("border-radius:8px;border-style:outset;border:none")
        self.CFN_Stream_Ctrl_btn.setWindowFlags(Qt.WindowStaysOnTopHint)

        self.CFN_Service_Dep_btn.show()
        self.CFN_Stream_Ctrl_btn.show()
        self.CFN_Service_Dep_btn.clicked.connect(self.serviceScheduling)
        self.CFN_Stream_Ctrl_btn.clicked.connect(self.netStreamScheduling)

    def _initServiceScenarios(self):
        self.cfn_manager.send_command('master', 'task', 'bk_svc up')
        self.master_s4.setVisible(True)
        self.cfn_manager.send_command('worker2', 'task', 'bk_svc up')
        self.worker2_s4.setVisible(True)
        # self.cfn_manager.send_command('jump_server', 'task', 'cfnres report')
        # Service Deployment initialization
        # service-1,2,3 on Node1(master), Node3(node2)
        # self.SDW.s1_n1.click()
        # self.SDW.s2_n1.click()
        # self.SDW.s3_n1.click()
        # self.SDW.s1_n3.click()

    def serviceScheduling(self):
        self.CFN_Service_Dep_btn.setStyleSheet(
            "border-radius:8px;color:black;border-style:outset;border:none;background-color: {}".format(
                QColor(242, 242, 242).name()))
        self.cfn_manager.send_command('master', 'stop_task', 'bk_svc up')
        self.master_s4.setVisible(False)
        self.cfn_manager.send_command('worker1', 'task', 'bk_svc up')
        self.worker1_s4.setVisible(True)
        self.SDW.s1_n2.click()
        self.SDW.s1_n1.click()

    def netStreamScheduling(self):
        self.node2_flow_btn.click()

    @pyqtSlot(int)
    def slaver_info_init(self, containerId: int):
        node_conf = self.cfn_manager.demo_config.get_node(containerId)
        if node_conf['node_name'] == 'master':
            service_node1 = [self.SDW.s1_n1, self.SDW.s2_n1, self.SDW.s3_n1]
            for n1_s in service_node1:
                if n1_s.isChecked():
                    n1_s.setChecked(False)
                    n1_s.setIcon(QIcon("./front_page/img/node1_unsel.png"))
        elif node_conf['node_name'] == 'worker1':
            service_node2 = [self.SDW.s1_n2, self.SDW.s2_n2, self.SDW.s3_n2]
            for n2_s in service_node2:
                if n2_s.isChecked():
                    n2_s.setChecked(False)
                    n2_s.setIcon(QIcon("./front_page/img/node2_unsel.png"))
        elif node_conf['node_name'] == 'worker2':
            service_node3 = [self.SDW.s1_n3, self.SDW.s2_n3, self.SDW.s3_n3]
            for n3_s in service_node3:
                if n3_s.isChecked():
                    n3_s.setChecked(False)
                    n3_s.setIcon(QIcon("./front_page/img/node3_unsel.png"))
        if node_conf['node_name'] == 'neat_host':
            # add onos flow(one fwd three) for 3 services  (initialization)
            self.cfn_manager.send_command('neat_host', 'task',
                                          f'onos_add_all 224.10.10.0#224.20.10.0#224.30.10.0#224.40.10.0')
        if node_conf['node_name'] == 'k8s_master':
            self.cfn_manager.send_command('k8s_master', 'task', 'kubernetes_del all')

    @pyqtSlot(int, dict)
    def cfn_data_report(self, containerId: int, cfn_data: dict):
        i = 0
        print(f"\ncfn_data_report return:{cfn_data}\n")
        self.data_visual.update_start(cfn_data)
        self.res_q.put(cfn_data)
        worker1_data, worker2_data, ocp_data = self.data_visual.read_json(cfn_data)
        while i < 3:
            i += 1
            self.monitor_ocp_cpu_hm.put(ocp_data[0])
            self.monitor_w1_cpu_hm.put(worker1_data[0])
            self.monitor_w2_cpu_hm.put(worker2_data[0])

    @pyqtSlot(int, dict)
    def show_node_list(self, containerId: int, task_list: dict):
        print(f"cfn_data_report containerId:{self.cfn_manager.node_names[containerId]}")
        print(f"cfn_data_report show_node_list:{task_list}")

    @pyqtSlot(str)
    def ue_msg_handler(self, ue_msg: str):
        # show ue-service request info on GUI
        # ueServiceName = {"Live Broadcast": "s1", "E-Meeting": "s2", "Surveillance": "s3"}
        # font = QtGui.QFont("Arial", 10, 5)
        print(f"\n ue_msg_handler>>>>>>> ... msg is:{ue_msg} ... <<<<<<\n")
        if ue_msg == "Crowded":
            self.link_crowded.setVisible(True)
            self.link_crowded.start_blink()
            # self.data_visual.set_WN1_Bandwidth()
            self.view.setBackgroundBrush(QtGui.QBrush(QtGui.QImage('./front_page/img/cfn_cn_bk_s3.png')))
            self.flow_priority += 10
            # from 10 to 8 (Auto)        Params: multicast_ip, in_port, cur_outport, tar_outport, priority
            self.cfn_manager.send_command('neat_host', 'task',
                                          f'onos 224.10.10.0#12#{self.pre_onos_port}#8#{self.flow_priority}')
            self.cfn_manager.send_command('neat_host', 'task',
                                          f'onos 224.20.10.0#12#{self.pre_onos_port}#8#{self.flow_priority}')
            self.cfn_manager.send_command('neat_host', 'task',
                                          f'onos 224.30.10.0#12#{self.pre_onos_port}#8#{self.flow_priority}')
            self.pre_onos_port = 8
        elif ue_msg == "UnCrowded":
            if self.link_crowded.isVisible():
                self.link_crowded.setVisible(False)
                self.link_crowded.stop_blink()
        else:
            ue_params = ue_msg.split('_')
            service_name, cpu, mem, bandWidth = ue_params[1], ue_params[2], ue_params[3], ue_params[4]
            # self.serviceResourceInfo.setItem(0, 0, QTableWidgetItem(service_name))
            # self.serviceResourceInfo.setItem(1, 0, QTableWidgetItem(cpu))
            # self.serviceResourceInfo.setItem(2, 0, QTableWidgetItem(mem))
            # self.serviceResourceInfo.setItem(3, 0, QTableWidgetItem(bandWidth))

            # font = QtGui.QFont("Arial", 10, QtGui.QFont.Bold)
            # self.serviceResourceInfo.item(0, 0).setBackground(QColor(0, 191, 255))
            # self.serviceResourceInfo.item(0, 0).setFont(font)
            # self.serviceResourceInfo.item(0, 0).setTextAlignment(Qt.AlignCenter)
            # self.serviceResourceInfo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

            # self.serviceResourceInfo.show()
            # self.serviceResourceInfo.setEditTriggers(QTableWidget.NoEditTriggers)
            # self.serviceResourceInfo_hide_timer.start()
            self.node2_flow_btn.click()

    def ue_msg_receiver(self):
        ip, port = '10.70.16.251', 10068
        listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        listener.bind((ip, port))
        data, _ = listener.recvfrom(4096)
        if data:
            ue_msg = data.decode()
            print(f"\n ue_msg_receiver>>>>>>> ... msg is:{ue_msg} ... <<<<<<\n")
            self.cfn_manager.signal_emitter.QtSignals.container_ue_msg.emit(ue_msg)
        listener.close()

    @pyqtSlot(int, str)
    def cmd_dbg_process(self, node_id: int, cmd_n_arg: str):
        command_line = cmd_n_arg.split()
        cmd = command_line[0]
        arg = ' '.join(command_line[1:])
        try:
            self.cfn_manager.send_command(node_id, cmd, arg)
        except Exception as err:
            print(f"((( --> CMD send error: {err}")

    @pyqtSlot(int, str, str)
    def update_service_deploy_info(self, tag: int, node_name: str, service_name: str):
        service_deployed = f"{node_name}_{service_name}"
        Service_Icon = {'master_s1': self.master_s1, 'master_s2': self.master_s2, 'master_s3': self.master_s3,
                        'worker1_s1': self.worker1_s1, 'worker1_s2': self.worker1_s2, 'worker1_s3': self.worker1_s3,
                        'worker2_s1': self.worker2_s1, 'worker2_s2': self.worker2_s2, 'worker2_s3': self.worker2_s3,
                        }
        Service_Icon[service_deployed].setVisible(tag == 1)

    @pyqtSlot(int, str)
    def slave_service_management(self, node_id: int, service_name: str):
        # handle signal from slaver side
        # deploy or delete one service
        print(f"\n handle signal from slaver side.... ")
        node_conf = self.cfn_manager.demo_config.get_node(node_id)
        if node_conf['node_name'] == 'master':
            match service_name:
                case 's1':
                    self.SDW.s1_n1.click()
                case 's2':
                    self.SDW.s2_n1.click()
                case 's3':
                    self.SDW.s3_n1.click()
        elif node_conf['node_name'] == 'worker1':
            match service_name:
                case 's1':
                    self.SDW.s1_n2.click()
                case 's2':
                    self.SDW.s2_n2.click()
                case 's3':
                    self.SDW.s3_n2.click()
        elif node_conf['node_name'] == 'worker2':
            match service_name:
                case 's1':
                    self.SDW.s1_n3.click()
                case 's2':
                    self.SDW.s2_n3.click()
                case 's3':
                    self.SDW.s3_n3.click()

    def elegantQuit(self):
        # end all subprocesses and exit.
        self.SDW.cfn_manager.close()
        self.cfn_manager.close()
        self.mouse_pos_mon.stop()
        try:
            self.SDW.close()
        except Exception as err:
            print(f" >>>> ... EXIT ERROR as:{err}")
        self.close()

    def keyPressEvent(self, KEvent):
        k = KEvent.key()
        if k == QtCore.Qt.Key_Escape:
            self.exit_dialog.show()
        elif k == QtCore.Qt.Key_V:
            if self.data_visual.isVisible():
                self.data_visual.setVisible(False)
                self.data_visual.history1.setVisible(False)
                self.data_visual.history2.setVisible(False)
                self.data_visual.history3.setVisible(False)
            else:
                self.cfn_manager.send_command('jump_server', 'task', 'cfnres report')
                self.data_visual.show()

        # elif k == QtCore.Qt.Key_C:
        #     self.link_crowded.setVisible(True)
        #     self.link_crowded.start_blink()
        #     # self.data_visual.set_WN1_Bandwidth()
        #     self.view.setBackgroundBrush(QtGui.QBrush(QtGui.QImage('./front_page/img/cfn_cn_bk_s3.png')))
        #     self.flow_priority += 10
        #     # from 10 to 8 (Auto)        Params: multicast_ip, in_port, cur_outport, tar_outport, priority
        #     self.cfn_manager.send_command('neat_host', 'task',
        #                                   f'onos 224.10.10.0#12#{self.pre_onos_port}#8#{self.flow_priority}')
        #     self.cfn_manager.send_command('neat_host', 'task',
        #                                   f'onos 224.20.10.0#12#{self.pre_onos_port}#8#{self.flow_priority}')
        #     self.cfn_manager.send_command('neat_host', 'task',
        #                                   f'onos 224.30.10.0#12#{self.pre_onos_port}#8#{self.flow_priority}')
        #     self.pre_onos_port = 8
        # elif k == QtCore.Qt.Key_N:
        #     self.cfn_manager.send_command('worker1', 'task', f'bk_service 1')
        # elif k == QtCore.Qt.Key_M:
        #     self.cfn_manager.send_command('worker1', 'stop_task', f'bk_service 1')

        elif k == QtCore.Qt.Key_R:
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
        self.cfn_manager.send_command('neat_host', 'task',
                                      f'onos_add_all 224.10.10.0#224.20.10.0#224.30.10.0#224.40.10.0')
        self.view.setBackgroundBrush(QtGui.QBrush(QtGui.QImage('./front_page/img/cfn_cn_bk.png')))
        self.cfn_manager.send_command('jump_server', 'task', 'cfnres report')
        self.CFN_Service_Dep_btn.setStyleSheet(
            "border-radius:8px;color:gray;border-style:outset;border:none;background-color: {}".format(
                QColor(242, 242, 242).name()))
        self.is_scenario3, self.is_scenario2, self.pre_onos_port = False, False, -1
        self.flow_priority = 40100
        self.link_crowded.setVisible(False)
        self.SDW.resetAllServiceDeploy()
        # self.data_visual.unset_WN1_Bandwidth()
        self.node1_flow_btn.setChecked(False)
        self.node2_flow_btn.setChecked(False)
        self.node3_flow_btn.setChecked(False)
        self.auto_flow_btn.setChecked(False)

        self.node1_flow_btn.setCheckable(False)
        self.node2_flow_btn.setCheckable(False)
        self.node3_flow_btn.setCheckable(False)
        self.auto_flow_btn.setCheckable(False)

        self.node1_flow_btn.setCheckable(True)
        self.node2_flow_btn.setCheckable(True)
        self.node3_flow_btn.setCheckable(True)
        self.auto_flow_btn.setCheckable(True)

        self.flow_btn_widget.setVisible(False)
        self.primaryWidget.setVisible(False)
        self.cfn_manager.send_command('k8s_master', 'task', 'kubernetes_del all')
        self._initServiceScenarios()
        self.cfn_manager.send_command('worker1', 'stop_task', 'bk_svc up')
        self.worker1_s4.setVisible(False)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    configuration = DemoConfigParser("cpn_config-test.json")
    inter_process_resource_NodeMan = [(i['node_name'], Pipe()) for i in configuration.nodes]
    inter_process_resource_StatMon = [(i['monitoring_source_name'], Queue(15)) for i in configuration.monitoring_sources]  # for state_monitor_process. new Queue()

    cfn_manager = CfnDemoManager(configuration, inter_process_resource_NodeMan, inter_process_resource_StatMon)
    print(cfn_manager.n_nodes)
    mainWidget = CpnAppWindow(cfn_manager)

    mainWidget.show()
    sys.exit(app.exec())