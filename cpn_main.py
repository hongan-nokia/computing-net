# -*- coding: utf-8 -*-
"""
@Time: 5/17/2024 11:26 AM
@Author: Honggang Yuan
@Email: honggang.yuan@nokia-sbell.com
Description:
"""
import sys
import time
from multiprocessing import Pipe, Queue

import PyWinMouse
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import QApplication, QPushButton

from nodemodels.cfndemomanager import CfnDemoManager
from resourcevisiualize.resvisualize import data_visualize
from testscenes.computingpowerawareaddressroute import ComputingPowerAwareAddressRouteWindow
from testscenes.scene3 import Scene3
from testscenes.scene4 import Scene4
from testscenes.systemsyntheticresutilize import SystemSyntheticResUtilize
from utils.configparser import DemoConfigParser
from utils.repeatimer import repeatTimer
from utils.tools import check_port

import threading


class CpnAppWindow(QtWidgets.QMainWindow):
    def __init__(self, demo_manager: CfnDemoManager):
        super().__init__()
        geo = {
            'top': 0,
            'left': 0,
            'width': 1920,
            'height': 1080}
        self.setGeometry(geo['left'], geo['top'], geo['width'], geo['height'])
        self.nokia_blue = QtGui.QColor(18, 65, 145)
        self.cfn_manager = demo_manager
        # self.node_names = demo_manager.node_names
        self.mainTitle = QtWidgets.QLabel(parent=self)
        self._initResMonitorQueue()

        self.task2_flag = False

        self.update_interval = 1  # Interval in seconds
        self.timer = None
        self.stop_event = threading.Event()

        self._initView()
        self._initMainTitle()
        self._initTestScenes()
        self._initDataVisualize()
        self._initScenarioButtons()
        self.mouse = PyWinMouse.Mouse()
        self.mouse_pos_mon = repeatTimer(1, self.get_mouse_position, autostart=True)
        self.mouse_pos_mon.start()

    def _initResMonitorQueue(self):
        self.c_node1_cpu_queue = self.cfn_manager.resource_StatMon['c_node1_cpu']
        self.c_node2_cpu_queue = self.cfn_manager.resource_StatMon['c_node2_cpu']
        self.c_node2_cpu_queue = self.cfn_manager.resource_StatMon['c_node2_cpu']

    def scenesQueueInfoSync(self):
        for i, queue in enumerate(self.c_nodes_cpu_queues):
            if not queue.empty():
                self.scene1_heatMap_QueueL[i].put(queue.get())
                self.scene2_heatMap_QueueL[i].put(queue.get())
                self.scene3_heatMap_QueueL[i].put(queue.get())

    def _initTestScenes(self):
        self.CPAARWidget = ComputingPowerAwareAddressRouteWindow(self, self.cfn_manager)
        self.CPAARWidget.setVisible(False)
        self.SSRUWidget = SystemSyntheticResUtilize(self, cfn_manager)
        self.SSRUWidget.setVisible(False)
        self.scene3 = Scene3(self, cfn_manager)
        self.scene3.setVisible(False)
        self.scene4 = Scene4(self, cfn_manager)
        self.scene4.setVisible(False)

    def _initDataVisualize(self):
        self.data_visual = data_visualize(parent=self, demo_manager=self.cfn_manager, res_queue_dict=None)
        self.data_visual.setVisible(False)
        self.startRequestResourceInfoThread()
        self.data_visual.updateHeatMap.connect(self.updateHeatMapIndex)
        self.computingNetResMonTimer = QtCore.QTimer(self)
        self.computingNetResMonTimer.setInterval(1000)
        self.computingNetResMonTimer.timeout.connect(self.updateNodesInfoThread)

        print("_initDataVisualize Done ")

    def startRequestResourceInfoThread(self):
        def run():
            while not self.stop_event.is_set():
                threading.Thread(target=self.data_visual.requestResourceInfo).start()
                time.sleep(self.update_interval)

        self.timer_thread = threading.Thread(target=run)
        self.timer_thread.start()

    def stopRequestResourceInfoThread(self):
        self.stop_event.set()
        self.timer_thread.join()

    def updateNodesInfoThread(self):
        self.data_visual.updateNodesInfo()

    def updateHeatMapIndex(self, data):
        # print("signal")
        self.CPAARWidget.cloud1_hm.queue_cpu.append(data[0])
        self.CPAARWidget.cloud2_hm.queue_cpu.append(data[1])
        self.CPAARWidget.cloud3_hm.queue_cpu.append(data[2])
        self.CPAARWidget.cloud1_hm.avg_cpu = sum(self.CPAARWidget.cloud1_hm.queue_cpu) / len(
            self.CPAARWidget.cloud1_hm.queue_cpu)
        self.CPAARWidget.cloud2_hm.avg_cpu = sum(self.CPAARWidget.cloud2_hm.queue_cpu) / len(
            self.CPAARWidget.cloud2_hm.queue_cpu)
        self.CPAARWidget.cloud3_hm.avg_cpu = sum(self.CPAARWidget.cloud3_hm.queue_cpu) / len(
            self.CPAARWidget.cloud3_hm.queue_cpu)

        self.SSRUWidget.s2cloud1_hm.queue_cpu.append(data[0])
        self.SSRUWidget.s2cloud2_hm.queue_cpu.append(data[1])
        self.SSRUWidget.s2cloud3_hm.queue_cpu.append(data[2])
        self.SSRUWidget.s2cloud1_hm.avg_cpu = sum(self.SSRUWidget.s2cloud1_hm.queue_cpu) / len(
            self.SSRUWidget.s2cloud1_hm.queue_cpu)
        self.SSRUWidget.s2cloud2_hm.avg_cpu = sum(self.SSRUWidget.s2cloud2_hm.queue_cpu) / len(
            self.SSRUWidget.s2cloud2_hm.queue_cpu)
        self.SSRUWidget.s2cloud3_hm.avg_cpu = sum(self.SSRUWidget.s2cloud3_hm.queue_cpu) / len(
            self.SSRUWidget.s2cloud3_hm.queue_cpu)

        self.scene3.scene31.cloud1_hm.queue_cpu.append(data[0])
        self.scene3.scene31.cloud2_hm.queue_cpu.append(data[1])
        self.scene3.scene31.cloud3_hm.queue_cpu.append(data[2])
        self.scene3.scene31.cloud1_hm.avg_cpu = sum(self.scene3.scene31.cloud1_hm.queue_cpu) / len(
            self.scene3.scene31.cloud1_hm.queue_cpu)
        self.scene3.scene31.cloud2_hm.avg_cpu = sum(self.scene3.scene31.cloud2_hm.queue_cpu) / len(
            self.scene3.scene31.cloud2_hm.queue_cpu)
        self.scene3.scene31.cloud3_hm.avg_cpu = sum(self.scene3.scene31.cloud3_hm.queue_cpu) / len(
            self.scene3.scene31.cloud3_hm.queue_cpu)

        self.scene3.scene32.cloud1_hm.queue_cpu.append(data[0])
        self.scene3.scene32.cloud2_hm.queue_cpu.append(data[1])
        self.scene3.scene32.cloud3_hm.queue_cpu.append(data[2])
        self.scene3.scene32.cloud1_hm.avg_cpu = sum(self.scene3.scene32.cloud1_hm.queue_cpu) / len(
            self.scene3.scene32.cloud1_hm.queue_cpu)
        self.scene3.scene32.cloud2_hm.avg_cpu = sum(self.scene3.scene32.cloud2_hm.queue_cpu) / len(
            self.scene3.scene32.cloud2_hm.queue_cpu)
        self.scene3.scene32.cloud3_hm.avg_cpu = sum(self.scene3.scene32.cloud3_hm.queue_cpu) / len(
            self.scene3.scene32.cloud3_hm.queue_cpu)

        self.scene3.scene33.cloud1_hm.queue_cpu.append(data[0])
        self.scene3.scene33.cloud2_hm.queue_cpu.append(data[1])
        self.scene3.scene33.cloud3_hm.queue_cpu.append(data[2])
        self.scene3.scene33.cloud1_hm.avg_cpu = sum(self.scene3.scene33.cloud1_hm.queue_cpu) / len(
            self.scene3.scene33.cloud1_hm.queue_cpu)
        self.scene3.scene33.cloud2_hm.avg_cpu = sum(self.scene3.scene33.cloud2_hm.queue_cpu) / len(
            self.scene3.scene33.cloud2_hm.queue_cpu)
        self.scene3.scene33.cloud3_hm.avg_cpu = sum(self.scene3.scene33.cloud3_hm.queue_cpu) / len(
            self.scene3.scene33.cloud3_hm.queue_cpu)

        self.CPAARWidget.cloud1_hm.index = data[0]
        self.CPAARWidget.cloud2_hm.index = data[1]
        self.CPAARWidget.cloud3_hm.index = data[2]

        self.SSRUWidget.s2cloud1_hm.index = data[0]
        self.SSRUWidget.s2cloud2_hm.index = data[1]
        self.SSRUWidget.s2cloud3_hm.index = data[2]

        self.scene3.scene31.cloud1_hm.index = data[0]
        self.scene3.scene31.cloud2_hm.index = data[1]
        self.scene3.scene31.cloud3_hm.index = data[2]

        self.scene3.scene32.cloud1_hm.index = data[0]
        self.scene3.scene32.cloud2_hm.index = data[1]
        self.scene3.scene32.cloud3_hm.index = data[2]

        self.scene3.scene33.cloud1_hm.index = data[0]
        self.scene3.scene33.cloud2_hm.index = data[1]
        self.scene3.scene33.cloud3_hm.index = data[2]

    def _initView(self):
        self.setWindowTitle(" ")
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.view = QtWidgets.QGraphicsView(parent=self)
        self.view.setBackgroundBrush(QtGui.QBrush(QtGui.QImage('./images/main_bg_cn.png')))
        self.view.setCacheMode(QtWidgets.QGraphicsView.CacheBackground)
        self.view.setScene(QtWidgets.QGraphicsScene())
        self.view.setSceneRect(0, 0, 1920, 1080)
        self.view.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        self.view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setRenderHint(QtGui.QPainter.Antialiasing)
        self.view.setGeometry(0, 0, 1920, 1080)

    def _initMainTitle(self):
        self.mainTitle.setText("")
        font = QtGui.QFont("Arial", 30, QtGui.QFont.Bold)
        self.mainTitle.setFont(font)
        self.mainTitle.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignCenter)  # Qt.AlignRight
        palette = self.palette()
        palette.setColor(self.foregroundRole(), self.nokia_blue)
        self.mainTitle.setPalette(palette)
        self.mainTitle.setGeometry(465, 30, 965, 69)
        self.mainTitle.raise_()

    def _initScenarioButtons(self):
        btn_font = QtGui.QFont("微软雅黑", 18, QtGui.QFont.Bold)
        self.net_compute_aware_btn = QPushButton(parent=self)
        self.net_compute_aware_btn.setText("实时算网资源")
        self.net_compute_aware_btn.setFont(btn_font)
        self.net_compute_aware_btn.setGeometry(30, 1000, 378, 60)
        self.net_compute_aware_btn.setStyleSheet(
            "border-radius:8px;border-style:outset;border:none;background-color: {}".format(QColor(0, 45, 127).name()))
        palette = self.net_compute_aware_btn.palette()
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))  # 设置按钮上字体的颜色为红色
        self.net_compute_aware_btn.setPalette(palette)

        self.main_page_btn = QPushButton(parent=self)
        self.main_page_btn.setText("主页")
        self.main_page_btn.setFont(btn_font)
        self.main_page_btn.setGeometry(20, 40, 100, 60)
        self.main_page_btn.setStyleSheet(
            "border-radius:8px;border-style:outset;border:none;background-color: {}".format(QColor(0, 45, 127).name()))
        palette = self.main_page_btn.palette()
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))  # 设置按钮上字体的颜色为红色
        self.main_page_btn.setPalette(palette)

        self.test1_btn = QPushButton(parent=self)
        self.test1_btn.setText("测试一")
        self.test1_btn.setFont(btn_font)
        self.test1_btn.setGeometry(20, 110, 100, 60)
        self.test1_btn.setStyleSheet(
            "border-radius:8px;border-style:outset;border:none;background-color: {}".format(QColor(0, 45, 127).name()))
        palette = self.test1_btn.palette()
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))  # 设置按钮上字体的颜色为红色
        self.test1_btn.setPalette(palette)

        self.test2_btn = QPushButton(parent=self)
        self.test2_btn.setText("测试二")
        self.test2_btn.setFont(btn_font)
        self.test2_btn.setGeometry(20, 180, 100, 60)
        self.test2_btn.setStyleSheet(
            "border-radius:8px;border-style:outset;border:none;background-color: {}".format(QColor(0, 45, 127).name()))
        palette = self.test2_btn.palette()
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))  # 设置按钮上字体的颜色为红色
        self.test2_btn.setPalette(palette)

        self.test3_btn = QPushButton(parent=self)
        self.test3_btn.setText("测试三")
        self.test3_btn.setFont(btn_font)
        self.test3_btn.setGeometry(20, 250, 100, 60)
        self.test3_btn.setStyleSheet(
            "border-radius:8px;border-style:outset;border:none;background-color: {}".format(QColor(0, 45, 127).name()))
        palette = self.test3_btn.palette()
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))  # 设置按钮上字体的颜色为红色
        self.test3_btn.setPalette(palette)

        self.test4_btn = QPushButton(parent=self)
        self.test4_btn.setText("测试四")
        self.test4_btn.setFont(btn_font)
        self.test4_btn.setGeometry(20, 320, 100, 60)
        self.test4_btn.setStyleSheet(
            "border-radius:8px;border-style:outset;border:none;background-color: {}".format(QColor(0, 45, 127).name()))
        palette = self.test4_btn.palette()
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))  # 设置按钮上字体的颜色为红色
        self.test4_btn.setPalette(palette)

        self.net_compute_aware_btn.show()
        self.main_page_btn.show()
        self.test1_btn.show()
        self.test2_btn.show()
        self.test3_btn.show()
        self.test4_btn.show()

        self.net_compute_aware_btn.clicked.connect(self._resourceAwarenessShow)
        self.main_page_btn.clicked.connect(self._showMainPage)
        self.test1_btn.clicked.connect(self._showTestScene1)

        self.test2_btn.clicked.connect(self._showTestScene2)
        self.test3_btn.clicked.connect(self._showTestScene3)
        self.test4_btn.clicked.connect(self._showTestScene4)

    def _resourceAwarenessShow(self):
        print("_resourceAwarenessShow")
        if self.data_visual.isVisible():
            print("self.data_visual.isVisible() -> True")
            self.data_visual.setVisible(False)
            self.data_visual.history1.setVisible(False)
            self.data_visual.history2.setVisible(False)
            self.data_visual.history3.setVisible(False)
            self.data_visual.history4.setVisible(False)
            # self.computingNetResMonTimer.stop()
        else:
            print("self.data_visual.isVisible() -> False")
            self.data_visual.setVisible(True)
            # self.data_visual.history1.drawRateAndTime()
            # self.data_visual.history2.drawRateAndTime()
            # self.data_visual.history3.drawRateAndTime()
            # self.data_visual.history4.drawRateAndTime()
            # self.computingNetResMonTimer.start()

    def _showMainPage(self):
        self.CPAARWidget.setVisible(False)
        self.SSRUWidget.setVisible(False)
        self.scene3.setVisible(False)
        self.scene3.scene31.setVisible(False)
        self.scene3.scene32.setVisible(False)
        self.scene3.scene33.setVisible(False)
        self.scene4.setVisible(False)
        self.CPAARWidget.reset()
        if self.task2_flag:
            self.SSRUWidget.reset()
            self.task2_flag = False
        self.scene3.reset()
        self.scene3.scene31.reset()
        self.scene3.scene32.reset()
        self.scene3.scene33.reset()
        self.scene4.reset()
        self.computingNetResMonTimer.stop()
        print("Show Main Page")

    def _showTestScene1(self):
        self.SSRUWidget.setVisible(False)
        self.CPAARWidget.reset()
        if self.task2_flag:
            self.SSRUWidget.reset()
            self.task2_flag = False
        self.scene3.reset()
        self.scene3.scene31.reset()
        self.scene3.scene32.reset()
        self.scene3.scene33.reset()
        self.scene4.reset()
        # self.CPAARWidget.user_first_pkg.label.setVisible(True)
        self.CPAARWidget.setVisible(True)
        self.scene3.setVisible(False)
        self.scene3.scene31.setVisible(False)
        self.scene3.scene32.setVisible(False)
        self.scene3.scene33.setVisible(False)
        self.scene4.setVisible(False)
        self.CPAARWidget.start_timer()

        self.computingNetResMonTimer.stop()
        self.data_visual.history1.drawRateAndTime()
        self.data_visual.history2.drawRateAndTime()
        self.data_visual.history3.drawRateAndTime()
        self.data_visual.history4.drawRateAndTime()
        self.computingNetResMonTimer.start()
        print("This is TestScene1")

    def _showTestScene2(self):
        self.CPAARWidget.setVisible(False)

        self.CPAARWidget.reset()
        if self.task2_flag:
            self.SSRUWidget.reset()
            self.task2_flag = False
        self.task2_flag = True
        self.scene3.reset()
        self.scene3.scene31.reset()
        self.scene3.scene32.reset()
        self.scene3.scene33.reset()
        self.scene4.reset()
        self.SSRUWidget.setVisible(True)
        self.scene3.setVisible(False)
        self.scene3.scene31.setVisible(False)
        self.scene3.scene32.setVisible(False)
        self.scene3.scene33.setVisible(False)
        self.scene4.setVisible(False)
        self.SSRUWidget.start_timer()

        self.computingNetResMonTimer.stop()
        self.data_visual.history1.drawRateAndTime()
        self.data_visual.history2.drawRateAndTime()
        self.data_visual.history3.drawRateAndTime()
        self.data_visual.history4.drawRateAndTime()
        self.computingNetResMonTimer.start()
        print("This is TestScene2")

    def _showTestScene3(self):
        self.SSRUWidget.setVisible(False)
        self.CPAARWidget.setVisible(False)
        self.scene3.setVisible(True)
        self.scene3.scene31.setVisible(False)
        self.scene3.scene32.setVisible(False)
        self.scene3.scene33.setVisible(False)
        self.scene4.setVisible(False)
        self.CPAARWidget.reset()
        if self.task2_flag:
            self.SSRUWidget.reset()
            self.task2_flag = False
        self.scene3.reset()
        self.scene3.scene31.reset()
        self.scene3.scene32.reset()
        self.scene3.scene33.reset()
        self.scene4.reset()

        self.computingNetResMonTimer.stop()
        self.data_visual.history1.drawRateAndTime()
        self.data_visual.history2.drawRateAndTime()
        self.data_visual.history3.drawRateAndTime()
        self.data_visual.history4.drawRateAndTime()
        self.computingNetResMonTimer.start()
        print("This is TestScene3")

    def _showTestScene4(self):
        self.computingNetResMonTimer.stop()

        self.SSRUWidget.setVisible(False)
        self.CPAARWidget.setVisible(False)
        self.scene3.setVisible(True)
        self.scene3.scene31.setVisible(False)
        self.scene3.scene32.setVisible(False)
        self.scene3.scene33.setVisible(False)
        self.scene4.setVisible(True)
        self.CPAARWidget.reset()
        if self.task2_flag:
            self.SSRUWidget.reset()
            self.task2_flag = False
        self.scene3.reset()
        self.scene3.scene31.reset()
        self.scene3.scene32.reset()
        self.scene3.scene33.reset()
        self.scene4.reset()
        time.sleep(0.2)
        self.scene4.addrRequest()
        self.scene4.drawRateAndTime()
        self.scene4.timer.start()
        self.scene4.timer_count_lable.start()

        print("This is TestScene4")

    # def keyPressEvent(self, KEvent):
    #     k = KEvent.key()
    #     if k == QtCore.Qt.Key_R:
    #         if self.isVisible():
    #             self.reset()
    #         elif self.CPAARWidget.isVisible():
    #             self.CPAARWidget.reset()
    #         elif self.SSRUWidget.isVisible():
    #             self.SSRUWidget.reset()
    #         elif self.scene3.scene31.isVisible():
    #             self.scene3.scene31.reset()
    #         elif self.scene3.scene32.isVisible():
    #             self.scene3.scene32.reset()
    #         elif self.scene3.scene33.isVisible():
    #             self.scene3.scene33.reset()
    #     elif k == QtCore.Qt.Key_1:
    #         print("Pressed Key-1")
    #         self.CPAARWidget.deployAITrainerOnCNode1()
    #     elif k == QtCore.Qt.Key_2:
    #         self.CPAARWidget.reset()
    #         # self.CPAARWidget.user_first_pkg.label.setVisible(True)
    #         self.CPAARWidget.user_first_pkg.start("sc1_sp1")
    #     elif k == QtCore.Qt.Key_Q:
    #         print("Pressed Key-Q")
    #         self.scene3.scene31.reset()
    #         # self.scene3.scene31.service_step1.label.setVisible(True)
    #         self.scene3.scene31.service_step1.start("sp1")
    #     elif k == QtCore.Qt.Key_W:
    #         self.scene3.scene32.reset()
    #         # self.scene3.scene32.service_step1.label.setVisible(True)
    #         self.scene3.scene32.step1_label1.setVisible(True)
    #         self.scene3.scene32.step1_label2.setVisible(True)
    #         self.scene3.scene32.service_step1.start("sp1")
    #     elif k == QtCore.Qt.Key_E:
    #         self.scene3.scene33.reset()
    #         # self.scene3.scene33.service_step1.label.setVisible(True)
    #         self.scene3.scene33.service_step1.start("sp1")
    #     elif k == QtCore.Qt.Key_N:
    #         self.cfn_manager.send_command("c_node1", "task", "surveillance up")
    #     elif k == QtCore.Qt.Key_M:
    #         self.cfn_manager.send_command("c_node1", "stop_task", "surveillance up")
    #     else:
    #         pass

    def get_mouse_position(self):
        x, y = self.mouse.get_mouse_pos()
        if y < 900:
            self.net_compute_aware_btn.setVisible(False)
        else:
            self.net_compute_aware_btn.setVisible(True)
        if x < 100:
            self.test1_btn.setVisible(True)
            self.test2_btn.setVisible(True)
            self.test3_btn.setVisible(True)
            self.test4_btn.setVisible(True)
            self.main_page_btn.setVisible(True)
        else:
            self.test1_btn.setVisible(False)
            self.test2_btn.setVisible(False)
            self.test3_btn.setVisible(False)
            self.test4_btn.setVisible(False)
            self.main_page_btn.setVisible(False)

    def reset(self):
        self.cfn_manager.close()
        print("This is Reset")



if __name__ == '__main__':
    app = QApplication(sys.argv)
    configuration = DemoConfigParser("cpn_config.json")
    check_port(configuration.gui_controller_host_port)
    inter_process_resource_NodeMan = [(i['node_name'], Pipe()) for i in configuration.nodes]
    inter_process_resource_StatMon = [(i['monitoring_source_name'], Queue(-1)) for i in configuration.monitoring_sources]  # for state_monitor_process. new Queue()
    cfn_manager = CfnDemoManager(configuration, inter_process_resource_NodeMan, inter_process_resource_StatMon)
    print(cfn_manager.n_nodes)
    mainWidget = CpnAppWindow(cfn_manager)
    mainWidget.show()
    sys.exit(app.exec())
