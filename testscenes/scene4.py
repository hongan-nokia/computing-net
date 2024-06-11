# -*- coding: utf-8 -*-
"""
@Time: 5/23/2024 8:48 PM
@Author: Honggang Yuan
@Email: honggang.yuan@nokia-sbell.com
Description:
"""
import random
import signal
import socket
import struct
import sys
import threading
import time
from multiprocessing import Pipe, Queue
from time import sleep

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import pyqtSlot, Qt, QTimer, QObject, pyqtSignal
from PyQt5.QtGui import QPalette, QColor, QBrush, QPixmap, QIcon
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QPushButton, QLabel, QGroupBox, QVBoxLayout, QTableWidgetItem, \
    QHeaderView, QTableWidget, QWidget
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from utils import DemoConfigParser
from utils.HeatMap import HeatMap


class MplCanvas(FigureCanvas):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig, self.ax = plt.subplots(figsize=(width, height), dpi=dpi)
        super(MplCanvas, self).__init__(fig)


# class RateUpdater(QObject):
#     rate_updated = pyqtSignal(float)
#
#     def __init__(self):
#         super().__init__()
#
#     def update_rate(self, rate):
#         self.rate_updated.emit(rate)
#
#
# class ServerThread(threading.Thread):
#     def __init__(self, ip, port):
#         super().__init__()
#         self.ip = ip
#         self.port = port
#         self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         self.server_socket.bind((self.ip, self.port))
#         self.server_socket.listen(5)  # Allow up to 5 connections
#         self.total_packet_count = 0
#         self.packet_count = 0
#         self.running = True
#         print(f"Server started at {self.ip}:{self.port}")
#
#         self.rate = 0
#
#         configuration = DemoConfigParser("cpn_config-test-only-cpu.json")
#         inter_process_resource_NodeMan = [(i['node_name'], Pipe()) for i in configuration.nodes]
#         resource_NodeMan = dict(inter_process_resource_NodeMan)
#         self.nodes_name = list(resource_NodeMan.keys())
#
#     def run(self):
#         packet_counter_thread = threading.Thread(target=self.count_packets)
#         packet_counter_thread.start()
#
#         while self.running:
#             client_socket, addr = self.server_socket.accept()
#             print(f"Connection from {addr}")
#             client_handler = threading.Thread(target=self.handle_client, args=(client_socket,))
#             client_handler.start()
#
#     def handle_client(self, client_socket):
#         with client_socket:
#             while self.running:
#                 message = self.recv_message(client_socket).decode('utf-8')
#                 if not message:
#                     break
#                 check_node = message in self.nodes_name
#                 # print(f"{message}:{check_node}")
#                 self.packet_count += 1
#                 self.total_packet_count += 1
#
#     def recv_message(self, client_socket):
#         # Read message length
#         raw_msglen = self.recvall(client_socket, 4)
#         if not raw_msglen:
#             return None
#         msglen = struct.unpack('>I', raw_msglen)[0]
#         # Read the message data
#         return self.recvall(client_socket, msglen)
#
#     def recvall(self, client_socket, n):
#         # Helper function to receive n bytes or return None if EOF is hit
#         data = b''
#         while len(data) < n:
#             packet = client_socket.recv(n - len(data))
#             if not packet:
#                 return None
#             data += packet
#         return data
#
#     def count_packets(self):
#         while self.running:
#             time.sleep(1)
#             print(f"Packets received in the last second: {self.packet_count}")
#             self.rate = self.packet_count
#             self.packet_count = 0
#             # print(self.total_packet_count)
#
#     def stop(self):
#         self.running = False
#         self.server_socket.close()
#         print("Server stopped.")


class RateUpdater(QObject):
    rate_updated = pyqtSignal(float)

    def __init__(self):
        super().__init__()

    def update_rate(self, rate):
        self.rate_updated.emit(rate)


class ServerThread(threading.Thread):
    def __init__(self, ip, port):
        super().__init__()
        self.ip = ip
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind((self.ip, self.port))
        self.total_packet_count = 0
        self.packet_count = 0
        self.running = True
        print(f"Server started at {self.ip}:{self.port}")

        self.rate = 0

        configuration = DemoConfigParser("cpn_config-test-only-cpu.json")
        inter_process_resource_NodeMan = [(i['node_name'], Pipe()) for i in configuration.nodes]
        resource_NodeMan = dict(inter_process_resource_NodeMan)
        self.nodes_name = list(resource_NodeMan.keys())

    def run(self):
        packet_counter_thread = threading.Thread(target=self.count_packets)
        packet_counter_thread.start()

        while self.running:
            data, addr = self.server_socket.recvfrom(1024)
            message = data.decode('utf-8')
            check_node = message in self.nodes_name
            # print(f"{message}:{check_node}")
            self.packet_count += 1
            self.total_packet_count += 1

    def count_packets(self):
        while self.running:
            time.sleep(1)
            print(f"Packets received in the last second: {self.packet_count}")
            self.rate = self.packet_count
            self.packet_count = 0
            # print(self.total_packet_count)

    def stop(self):
        self.running = False
        self.server_socket.close()
        print("Server stopped.")


class Scene4(QWidget):
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
        # self._initMonitorQueue()
        self._initView()

        # self.addrRequest()

        # self.timer = None
        self.server_thread = None

        # self.base_server_port = 10070  # 基础端口，后续端口依次递增
        # self.thread_count = 1
        # self.received_count = 0
        # self.lock = threading.Lock()

    def _initView(self):
        self.setWindowTitle(" ")
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.view = QtWidgets.QGraphicsView(parent=self)
        self.view.setBackgroundBrush(QtGui.QBrush(QtGui.QImage('./images_test3/test_scenario4_bg.png')))
        self.view.setCacheMode(QtWidgets.QGraphicsView.CacheBackground)
        self.view.setScene(QtWidgets.QGraphicsScene())
        self.view.setSceneRect(0, 0, 1920, 1080)
        self.view.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        self.view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setRenderHint(QtGui.QPainter.Antialiasing)
        self.view.setGeometry(0, 0, 1920, 1080)

        self.drawAddrRequestCountLable()

        self.drawRateAndTime()

    def _initMonitorQueue(self):
        self.monitor_q_cpu_hm_node1 = self.cfn_manager.resource_StatMon['c_node1_cpu']  # 算力节点1 CPU
        self.monitor_q_cpu_hm_node2 = self.cfn_manager.resource_StatMon['c_node2_cpu']  # 算力节点2 CPU
        self.monitor_q_cpu_hm_node3 = self.cfn_manager.resource_StatMon['c_node3_cpu']  # 算力节点3 CPU

    def initConnections(self):
        # self.cfn_manager.signal_emitter.QtSignals.addrRequest_test.connect(self.addrRequest)
        pass

    def addrRequest(self):
        server_ip = "127.0.0.1"
        server_port = 12345

        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.stop()

        self.server_thread = ServerThread(server_ip, server_port)
        self.server_thread.start()

        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, sig, frame):
        if self.server_thread:
            self.server_thread.stop()
        sys.exit(0)

    def stopServer(self):
        if self.server_thread:
            self.server_thread.stop()

    def drawRateAndTime(self):
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)

        self.plot_widget = QWidget()  # 创建一个包装了 MplCanvas 的 QWidget
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.plot_widget.setLayout(layout)

        # self.canvas.setMinimumSize(400, 300)  # 设置最小尺寸
        # self.canvas.setMaximumSize(800, 600)  # 设置最大尺寸

        self.y_data = [0]
        self.x_data = [0]  # 使用索引作为横坐标

        # main_layout = QVBoxLayout()
        # main_layout.addWidget(self.plot_widget)

        self.plot_widget.setGeometry(900, 200, 500, 375)

        self.view.scene().addWidget(self.plot_widget)

        self.rate_updater = RateUpdater()
        self.rate_updater.rate_updated.connect(lambda rate: self.update_plot(rate))

        self.timer = QTimer()
        self.timer.setInterval(1000)  # 更新间隔为1000毫秒，即1秒
        self.timer.timeout.connect(self.update_plot)
        # self.timer.start()

    # def simulate_rate_update(self):
    #     # 生成0到100之间的随机速率值
    #     simulated_rate = random.uniform(0, 100)
    #     self.rate_updater.update_rate(simulated_rate)

    def update_plot(self):
        current_rate = self.server_thread.rate

        self.y_data.append(current_rate)
        self.x_data.append(len(self.x_data))  # 添加索引

        self.canvas.ax.clear()
        self.canvas.ax.plot(self.x_data, self.y_data, label="Rate")

        self.canvas.ax.set_xlabel('Time/s')
        self.canvas.ax.set_ylabel('Rate')
        self.canvas.ax.legend()
        self.canvas.ax.grid(True)

        self.canvas.draw()

    def drawAddrRequestCountLable(self):
        font = QtGui.QFont("微软雅黑", 20)
        self.addrRequestTextLable = QtWidgets.QLabel(parent=self)
        self.addrRequestTextLable.setText("寻址请求总数:")
        self.addrRequestTextLable.setStyleSheet("color: #fff;")
        self.addrRequestTextLable.setWordWrap(True)
        self.addrRequestTextLable.setGeometry(550, 250, 180, 100)
        self.addrRequestTextLable.setFont(font)
        self.view.scene().addWidget(self.addrRequestTextLable)

        self.addrRequestCountLable = QtWidgets.QLabel(parent=self)
        self.addrRequestCountLable.setText("0")
        self.addrRequestCountLable.setStyleSheet("color: #fff;")
        self.addrRequestCountLable.setAlignment(Qt.AlignRight)
        self.addrRequestCountLable.setWordWrap(True)
        self.addrRequestCountLable.setGeometry(550, 330, 160, 100)
        self.addrRequestCountLable.setFont(font)
        self.view.scene().addWidget(self.addrRequestCountLable)

        self.timer_count_lable = QTimer()
        self.timer_count_lable.setInterval(1000)  # 更新间隔为1000毫秒，即1秒
        self.timer_count_lable.timeout.connect(self.updateLabel)

    def updateLabel(self):
        self.addrRequestCountLable.setText(str(self.server_thread.total_packet_count))

    def reset(self):
        self.timer.stop()
        self.timer_count_lable.stop()
        if self.server_thread != None:
            self.stopServer()
        print("reset scene 4")
        pass

