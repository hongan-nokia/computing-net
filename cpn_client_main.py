import argparse
import random
import signal
import socket
import struct
import sys
import threading
import time
from pathlib import Path

from PyQt5.QtCore import Qt, pyqtSlot, QSize, QThread, pyqtSignal, QMutex, QMutexLocker
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtGui import QKeyEvent, QPixmap, QIcon, QColor
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QStackedWidget, QWidget, QVBoxLayout, QGroupBox, \
    QHBoxLayout, QSpacerItem, QSizePolicy

from Surveillance import Surveillance
from nodemodels.cfnnodemodel import CfnNodeModel
from nodemodels.fogcamera import FogCam
from utils.configparser import DemoConfigParser

from multiprocessing import Pipe, Queue


# TCP
# class SocketThread(QThread):
#     message_received = pyqtSignal(str)
#
#     def __init__(self, ip, port, num_packets):
#         super().__init__()
#         self.ip = ip
#         self.port = port
#         self.num_packets = num_packets
#         self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#         self.connected = False
#         self.running = True
#
#     def run(self):
#         try:
#             self.socket.connect((self.ip, self.port))
#             self.connected = True
#             self.listen_for_messages()
#         except Exception as e:
#             self.message_received.emit(f"Failed to connect to {self.ip}:{self.port} - {str(e)}")
#
#     def listen_for_messages(self):
#         while self.running and self.connected:
#             try:
#                 data = self.socket.recv(1024)
#                 if data:
#                     self.message_received.emit(f"Received from {self.ip}:{self.port} - {data.decode('utf-8')}")
#             except Exception as e:
#                 self.message_received.emit(f"Error receiving data from {self.ip}:{self.port} - {str(e)}")
#                 self.connected = False
#
#     def send_message(self, message):
#         if self.connected:
#             try:
#                 message = message.encode('utf-8')
#                 message_length = struct.pack('>I', len(message))
#                 self.socket.sendall(message_length + message)
#                 # print(message)
#             except Exception as e:
#                 self.message_received.emit(f"Error sending data to {self.ip}:{self.port} - {str(e)}")
#
#     def send_multiple_messages(self, message):
#         for _ in range(self.num_packets):
#             if not self.running:
#                 break
#             self.send_message(message)
#         self.close()
#
#     def close(self):
#         self.running = False
#         self.connected = False
#         self.socket.close()


class SocketThread(QThread):
    message_received = pyqtSignal(str)

    def __init__(self, ip, port):
        super().__init__()
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.running = True
        self.mutex = QMutex()

    def run(self):
        self.listen_for_messages()

    def listen_for_messages(self):
        try:
            self.socket.bind((self.ip, self.port))
            while self.running:
                data, addr = self.socket.recvfrom(1024)
                if data:
                    self.message_received.emit(f"Received from {addr[0]}:{addr[1]} - {data.decode('utf-8')}")
        except Exception as e:
            self.message_received.emit(f"Error receiving data - {str(e)}")

    def send_message(self, message):
        try:
            with QMutexLocker(self.mutex):
                message = message.encode('utf-8')
                self.socket.sendto(message, (self.ip, self.port))
        except Exception as e:
            self.message_received.emit(f"Error sending data - {str(e)}")

    def close(self):
        self.running = False
        self.socket.close()


class SendPacketsThread(QThread):
    def __init__(self, socket_thread, num_packets, probabilities, nodes_name):
        super().__init__()
        self.socket_thread = socket_thread
        self.num_packets = num_packets
        self.running = True
        self.probabilities = probabilities
        self.nodes_name = []
        self.random_node_id = 1

        for i in range(10000):
            self.nodes_name.append(f"node{i}")

    def run(self):
        self.send_multiple_messages()

    def send_multiple_messages(self):
        for _ in range(self.num_packets):
            if not self.running:
                break
            choice = random.choices([0, 1], weights=self.probabilities)[0]
            if choice == 0:
                # 从给定的列表中随机读取一个值
                message = random.choice(self.nodes_name)
                # print("随机读取值:", message)
            else:
                # 随机生成一个值
                message = f"Node_{self.random_node_id}"
                self.random_node_id += 1
            # print(message)
            self.socket_thread.send_message(message)

    def stop(self):
        self.running = False


class ClientCanvas(QWidget):
    def __init__(self, parent, client_mgn: CfnNodeModel):
        super().__init__()
        self.setParent(parent)
        self.layout = QtWidgets.QHBoxLayout(self)
        self.setWindowTitle("")
        self.resize(1920, 1080)
        self.groupBox = QGroupBox("")
        self.client_mgn = client_mgn

        configuration = DemoConfigParser("cpn_config-test-only-cpu.json")
        inter_process_resource_NodeMan = [(i['node_name'], Pipe()) for i in configuration.nodes]
        resource_NodeMan = dict(inter_process_resource_NodeMan)
        self.nodes_name = list(resource_NodeMan.keys())

        self.random_node_id = 1

        self.threads = []

        self.selected_button = None

        # 最外层布局、字体、粗体、字体大小
        self.mainLayout = QtWidgets.QVBoxLayout(self.groupBox)
        self.font = QtGui.QFont()
        self.font.setFamily("Arial")
        self.font.setBold(True)
        self.font.setPointSize(30)

        self.btn_style = """
            QPushButton {
                border: 10px solid #2980b9;
                    color: blue;
                    padding: 30px;
                    border-radius: 30px;
                }
                QPushButton:hover {
                    color: red;
                    border: 10px inset #2980b9;
                }
            """
        self.task_font_size = QtGui.QFont()
        self.task_font_size.setFamily("Arial")
        self.task_font_size.setBold(True)
        self.task_font_size.setPointSize(20)

        self.task_font_size1 = QtGui.QFont()
        self.task_font_size1.setFamily("Arial")
        self.task_font_size1.setBold(True)
        self.task_font_size1.setPointSize(15)
        self._initTitle()

        self.left_spacer = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout.addItem(self.left_spacer)

        self._initTaskOne()

        self.middle_spacer = QSpacerItem(200, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.horizontalLayout.addItem(self.middle_spacer)

        self._initTaskTwo()

        self.right_spacer = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout.addItem(self.right_spacer)

        self._initTaskFour()

        self.right_spacer = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout.addItem(self.right_spacer)

        # self.horizontalLayout.setStretch(0, 1)
        # self.horizontalLayout.setStretch(1, 1)
        # self.horizontalLayout.setStretch(2, 1)

        self.mainLayout.addWidget(self.view_box)

        spacerItem = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.mainLayout.addItem(spacerItem)

        # 在底部添加logo
        self._initNokiaLogo()
        self.mainLayout.setStretch(0, 1)
        self.mainLayout.setStretch(1, 5)
        self.mainLayout.setStretch(2, 1)

        self.layout.addWidget(self.groupBox)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setVisible(True)

    def _initTitle(self):
        self.title_box = QtWidgets.QGroupBox(self.groupBox)
        self.titleLayout = QtWidgets.QVBoxLayout(self.title_box)

        title = "<span style='color: #fff;'>" + "用户端测试界面" + "</span>"
        self.title = QtWidgets.QLabel(self.title_box)
        self.title.setText(title)
        self.title.setFont(self.font)
        self.title.setStyleSheet("font-size: 80px; padding: 75px;")
        self.title.setAlignment(Qt.AlignCenter)
        self.titleLayout.addWidget(self.title)
        self.mainLayout.addWidget(self.title_box)

        self.view_box = QtWidgets.QGroupBox(self.groupBox)

        self.horizontalLayout = QtWidgets.QHBoxLayout(self.view_box)

    def _initTaskOne(self):
        self.task1_box = QtWidgets.QGroupBox(self.view_box)
        self.task1_box.setStyleSheet("background: #ccc; border-radius: 50px;")
        self.task1_layout = QtWidgets.QVBoxLayout(self.task1_box)

        # ####
        self.task1_title_box = QtWidgets.QGroupBox(self.task1_box)
        self.task1_title_box.setStyleSheet("color: #222; border-radius: 20px; width: 400px;")
        self.task1_title_box_layout = QtWidgets.QVBoxLayout(self.task1_title_box)

        self.task1_title = QtWidgets.QLabel(self.task1_box)
        self.task1_title.setText("测试一")
        self.task1_title.setFont(self.task_font_size)

        self.task1_title.setAlignment(Qt.AlignCenter)

        self.task1_title_box_layout.addWidget(self.task1_title)
        self.task1_layout.addWidget(self.task1_title_box)

        # ####
        self.task1_btn_box = QtWidgets.QGroupBox(self.task1_box)
        self.task1_btn_layout = QtWidgets.QVBoxLayout(self.task1_btn_box)

        self.task1_btn = QtWidgets.QPushButton(self.task1_box)
        self.task1_btn.setText("首包响应时延测试")
        self.task1_btn.setFont(self.task_font_size)
        self.task1_btn.setStyleSheet(self.btn_style)
        self.task1_btn_layout.addWidget(self.task1_btn)
        self.task1_layout.addWidget(self.task1_btn_box)
        self.task1_btn.clicked.connect(self._firstPkgRespLatency)

        # ####
        self.task1_text1_box = QtWidgets.QGroupBox(self.task1_box)
        self.task1_text1_box.setStyleSheet("color: #484889; border-radius: 3px;")
        self.task1_text1_layout = QtWidgets.QVBoxLayout(self.task1_text1_box)

        self.task1_text1 = QtWidgets.QLabel(self.task1_box)
        self.task1_text1.setText("业务首包时延（ms）")
        self.task1_text1.setFont(self.task_font_size)
        self.task1_text1.setAlignment(Qt.AlignCenter)

        self.task1_text1_layout.addWidget(self.task1_text1)
        self.task1_layout.addWidget(self.task1_text1_box)

        # ###
        self.task1_text2_box = QtWidgets.QGroupBox(self.task1_box)
        self.task1_text2_box.setStyleSheet("border-radius: 30px;")
        self.task1_text2_layout = QtWidgets.QVBoxLayout(self.task1_text2_box)

        self.task1_text2 = QtWidgets.QLabel(self.task1_box)
        self.task1_text2.setText("---")
        self.task1_text2.setFont(self.task_font_size)
        self.task1_text2.setStyleSheet("background: #fff;")
        self.task1_text2.setFixedWidth(200)
        self.task1_text2.setAlignment(Qt.AlignCenter)

        self.task1_text2_center_layout = QHBoxLayout()
        self.spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.task1_text2_center_layout.addItem(self.spacer)

        self.task1_text2_center_layout.addWidget(self.task1_text2)

        self.spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.task1_text2_center_layout.addItem(self.spacer)

        self.task1_text2_layout.addLayout(self.task1_text2_center_layout)
        self.task1_layout.addWidget(self.task1_text2_box)

        self.horizontalLayout.addWidget(self.task1_box)

    def _initTaskTwo(self):
        self.task2_box = QtWidgets.QGroupBox(self.view_box)
        self.task2_box.setStyleSheet("background: #ccc; border-radius: 50px;")
        self.task2_layout = QtWidgets.QVBoxLayout(self.task2_box)

        # ####
        self.task2_title_box = QtWidgets.QGroupBox(self.task2_box)
        self.task2_title_box.setStyleSheet("border-radius: 20px; width: 400px;")
        self.task2_title_layout = QtWidgets.QVBoxLayout(self.task2_title_box)

        self.task2_title = QtWidgets.QLabel(self.task2_box)
        self.task2_title.setText("测试三")
        self.task2_title.setFont(self.task_font_size)
        self.task2_title.setStyleSheet("color: #222;")
        self.task2_title.setAlignment(Qt.AlignCenter)

        self.task2_title_layout.addWidget(self.task2_title)
        self.task2_layout.addWidget(self.task2_title_box)

        # ####
        self.task2_btn1_box = QtWidgets.QGroupBox(self.task2_box)
        self.task2_btn1_layout = QtWidgets.QVBoxLayout(self.task2_btn1_box)

        self.task2_btn1 = QtWidgets.QPushButton(self.task2_box)
        self.task2_btn1.setText("服务寻址测试")
        self.task2_btn1.setFont(self.task_font_size)
        self.task2_btn1.setStyleSheet(self.btn_style)
        self.task2_btn1.clicked.connect(self._serviceAddress)

        self.task2_btn1_layout.addWidget(self.task2_btn1)
        self.task2_layout.addWidget(self.task2_btn1_box)

        self.horizontalLayout.addWidget(self.task2_box)

        # ####
        self.task2_btn2_box = QtWidgets.QGroupBox(self.task2_box)
        self.task2_btn2_layout = QtWidgets.QVBoxLayout(self.task2_btn2_box)

        self.task2_btn2 = QtWidgets.QPushButton(self.task2_box)
        self.task2_btn2.setText("算力寻址测试")
        self.task2_btn2.setFont(self.task_font_size)
        self.task2_btn2.setStyleSheet(self.btn_style)
        self.task2_btn2.clicked.connect(self._computingAddress)

        self.task2_btn2_layout.addWidget(self.task2_btn2)
        self.task2_layout.addWidget(self.task2_btn2_box)

        self.horizontalLayout.addWidget(self.task2_box)

        # ####
        self.task2_btn3_box = QtWidgets.QGroupBox(self.task2_box)
        self.task2_btn3_layout = QtWidgets.QVBoxLayout(self.task2_btn3_box)

        self.task2_btn3 = QtWidgets.QPushButton(self.task2_box)
        self.task2_btn3.setText("内容寻址测试")
        self.task2_btn3.setFont(self.task_font_size)
        self.task2_btn3.setStyleSheet(self.btn_style)
        self.task2_btn3.clicked.connect(self._contentAddress)

        self.task2_btn4 = QtWidgets.QRadioButton("房间监控")
        self.task2_btn4.toggled.connect(self.onRadioButtonToggled)
        self.task2_btn4.setChecked(True)
        self.task2_btn4.setFont(self.task_font_size1)
        self.task2_btn4.setStyleSheet("padding-left:30px;")

        self.task2_label_box = QtWidgets.QGroupBox()
        self.task2_label_layout = QtWidgets.QHBoxLayout(self.task2_label_box)

        self.task2_btn5 = QtWidgets.QRadioButton("视频")
        self.task2_btn5.toggled.connect(self.onRadioButtonToggled)
        self.task2_btn5.setFont(self.task_font_size1)
        self.task2_label_layout.addWidget(self.task2_btn5)
        self.task2_btn5.setStyleSheet("padding-left:20px;")

        self.task2_btn5_edit1 = QtWidgets.QLineEdit()
        self.task2_btn5_edit1.setFont(self.task_font_size1)
        self.task2_btn5_edit1.setStyleSheet("background: #fff;border-radius:12px;padding:5px;")
        self.task2_btn5_edit1.setMaximumWidth(80)
        self.task2_btn5_edit1.setText("football")
        self.task2_label_layout.addWidget(self.task2_btn5_edit1)

        self.task2_btn5_label1 = QtWidgets.QLabel("第")
        self.task2_btn5_label1.setFont(self.task_font_size1)
        self.task2_btn5_label1.setMaximumWidth(30)
        self.task2_label_layout.addWidget(self.task2_btn5_label1)

        self.task2_btn5_edit2 = QtWidgets.QLineEdit()
        self.task2_btn5_edit2.setFont(self.task_font_size1)
        self.task2_btn5_edit2.setStyleSheet("background:#fff;border-radius:12px;padding:5px;")
        self.task2_btn5_edit2.setMaximumWidth(80)
        self.task2_btn5_edit2.setText("36")
        self.task2_btn5_edit2.setAlignment(Qt.AlignRight)
        self.task2_label_layout.addWidget(self.task2_btn5_edit2)

        self.task2_btn5_label2 = QtWidgets.QLabel("秒")
        self.task2_btn5_label2.setFont(self.task_font_size1)
        self.task2_label_layout.addWidget(self.task2_btn5_label2)

        self.task2_radioBtnGroup = QtWidgets.QButtonGroup(self.task2_box)
        self.task2_radioBtnGroup.addButton(self.task2_btn4)
        self.task2_radioBtnGroup.addButton(self.task2_btn5)

        self.task2_btn3_layout.addWidget(self.task2_btn3)
        self.task2_btn3_layout.addWidget(self.task2_btn4)
        # self.task2_btn3_layout.addWidget(self.task2_btn5)
        self.task2_btn3_layout.addWidget(self.task2_label_box)

        self.task2_layout.addWidget(self.task2_btn3_box)

        self.horizontalLayout.addWidget(self.task2_box)

    def _initTaskFour(self):
        self.task4_box = QtWidgets.QGroupBox(self.view_box)
        self.task4_box.setStyleSheet("background: #ccc; border-radius: 50px;")
        self.task4_layout = QtWidgets.QVBoxLayout(self.task4_box)

        # ####
        self.task4_title_box = QtWidgets.QGroupBox(self.task4_box)
        self.task4_title_box.setStyleSheet("border-radius: 20px; width: 400px;")
        self.task4_title_layout = QtWidgets.QVBoxLayout(self.task4_title_box)

        self.task4_title = QtWidgets.QLabel(self.task4_box)
        self.task4_title.setText("测试四")
        self.task4_title.setFont(self.task_font_size)
        self.task4_title.setStyleSheet("color: #222;")
        self.task4_title.setAlignment(Qt.AlignCenter)

        self.task4_title_layout.addWidget(self.task4_title)
        self.task4_layout.addWidget(self.task4_title_box)

        # ######
        self.task4_btn2_box = QtWidgets.QGroupBox(self.task4_box)
        self.task4_btn2_layout = QtWidgets.QVBoxLayout(self.task4_btn2_box)

        self.task4_btn2 = QtWidgets.QPushButton(self.task4_box)
        self.task4_btn2.setText("寻址请求发生器")
        self.task4_btn2.setFont(self.task_font_size)
        self.task4_btn2.setStyleSheet(self.btn_style)
        self.task4_btn2.clicked.connect(self._addressingRequest)

        self.task4_btn2_layout.addWidget(self.task4_btn2)
        self.task4_layout.addWidget(self.task4_btn2_box)

        self.horizontalLayout.addWidget(self.task4_box)

        # ####
        self.task4_btn1_box = QtWidgets.QGroupBox(self.task4_box)
        self.task4_btn1_layout = QtWidgets.QHBoxLayout(self.task4_btn1_box)

        self.task2_btn5_label1 = QtWidgets.QLabel("寻址命中率")
        self.task2_btn5_label1.setFont(self.task_font_size)
        # self.task2_btn5_label1.setStyleSheet("margin-left:18px;")
        self.task4_btn1_layout.addWidget(self.task2_btn5_label1)

        self.task4_inputbtn = QtWidgets.QLineEdit(self.task4_box)
        self.task4_inputbtn.setFont(self.task_font_size)
        self.task4_inputbtn.setStyleSheet("background: #fff;border-radius:20px;padding:20px;")
        self.task4_inputbtn.setAlignment(Qt.AlignCenter)
        self.task4_inputbtn.setFixedWidth(200)
        self.task4_inputbtn.setText("0.3")

        self.task4_inputbtn_center_layout = QHBoxLayout()
        self.spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.task4_inputbtn_center_layout.addItem(self.spacer)

        self.task4_inputbtn_center_layout.addWidget(self.task4_inputbtn)

        self.spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.task4_inputbtn_center_layout.addItem(self.spacer)

        self.task4_btn1_layout.addLayout(self.task4_inputbtn_center_layout)
        self.task4_layout.addWidget(self.task4_btn1_box)

        self.horizontalLayout.addWidget(self.task4_box)

        # ####
        self.task4_btn3_box = QtWidgets.QGroupBox(self.task4_box)
        self.task4_btn3_layout = QtWidgets.QVBoxLayout(self.task4_btn3_box)

        self.task4_btn3 = QtWidgets.QPushButton(self.task4_box)
        self.task4_btn3.setText("寻址请求终止器")
        self.task4_btn3.setFont(self.task_font_size)
        # self.task4_btn3.setStyleSheet(self.btn_style)
        self.task4_btn3.setStyleSheet("border: 10px solid #222; color: #222; padding: 30px; border-radius: 30px;")
        self.task4_btn3.clicked.connect(self._stopServiceAddress)
        self.task4_btn3.setEnabled(False)

        self.task4_btn3_layout.addWidget(self.task4_btn3)
        self.task4_layout.addWidget(self.task4_btn3_box)

        self.horizontalLayout.addWidget(self.task4_box)

    def _initNokiaLogo(self):
        self.nokia_logo = QtWidgets.QLabel()
        self.nokia_logo.setPixmap(QtGui.QPixmap("./images/bell_logo.png"))
        self.nokia_logo.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.nokia_logo_layout = QtWidgets.QHBoxLayout()
        self.nokia_logo_layout.addStretch(19)
        self.nokia_logo_layout.addWidget(self.nokia_logo)
        self.nokia_logo_layout.addStretch(1)
        self.nokia_logo.setStyleSheet("border: none;")
        self.mainLayout.addLayout(self.nokia_logo_layout)

    def _initFirstPkgMonitorSocket(self):
        # self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.server_socket.bind((server_host, server_port))
        # self.server_socket.listen(5)
        # while True:
        #     self.conn, _ = self.server_socket.accept()
        #     client_thread = threading.Thread(target=self.listenFirstPkg, args=(self.conn,))
        #     client_thread.start()
        # 创建一个UDP套接字
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        port = 12313
        # 绑定到指定的端口
        server_address = ('', port)
        sock.bind(server_address)

        print(f"Listening on port {port}...")

        # 接收数据
        data, address = sock.recvfrom(4096)
        data = data.decode()
        print(f"Received message: {data} from {address}")
        if "RESPONSE" in data:
            print(f"listenFirstPkg >>>>> {data}")
            self.timeSpine2 = time.time()
            print(f"timeSpine1: {self.timeSpine1}")
            print(f"timeSpine2: {self.timeSpine2}")
            latency = round((self.timeSpine2 - self.timeSpine1) * 1000, 1)
            self.task1_text2.setText(str(latency))

    def _firstPkgRespLatency(self):
        print("This _firstPkgRespLatency func")
        server_thread = threading.Thread(target=self._initFirstPkgMonitorSocket)
        server_thread.start()
        self.client_mgn.conn_GUI.send(('cpn_test', 'firstPkgLat'))
        self.timeSpine1 = time.time()

    def _serviceAddress(self):
        print("This _serviceAddress func")
        self.client_mgn.conn_GUI.send(('cpn_test', 'serviceAddr'))

    def _computingAddress(self):
        print("This _serviceAddress func")
        self.client_mgn.conn_GUI.send(('cpn_test', 'computingAddr'))

    def _contentAddress(self):
        print("This _contentAddress func")
        if self.selected_button == self.task2_btn4:
            print("房间监控事件")
            self.client_mgn.conn_GUI.send(('cpn_test', 'contentAddr'))
        elif self.selected_button == self.task2_btn5:
            print("视频播放事件")
            video_name = self.task2_btn5_edit1.text()
            video_startTime = self.task2_btn5_edit2.text()
            video_tuple = (video_name, video_startTime)
            # self.client_mgn.conn_GUI.send(('cpn_test', 'contentAddr'))
            self.client_mgn.conn_GUI.send(('cpn_test', 'contentAddrVideo', video_tuple))

    def _addressingRequest(self):
        print("This _addressingRequest func")
        # self.client_mgn.conn_GUI.send(('cpn_test', 'addrRequest'))
        server_ip = self.client_mgn.demo_conf.gui_controller_host_ip  # 本地IP地址
        base_server_port = self.client_mgn.demo_conf.gui_controller_host_port  # 基础端口，后续端口依次递增
        thread_count = 1  # 直接在代码中设置线程数量
        num_packets = 1000000  # 每个线程发送的包数量
        nodes = [{"ip": "127.0.0.1", "port": 12345}]
        self.flagToSendMessage = True

        self.task4_btn2.setEnabled(False)
        self.task4_btn3.setEnabled(True)
        self.task4_btn2.setStyleSheet("border: 10px solid #222; color: #222; padding: 30px; border-radius: 30px;")
        self.task4_btn3.setStyleSheet(self.btn_style)

        probabilitie_value_QLineEdit = self.task4_inputbtn.text()
        try:
            probabilitie_value_QLineEdit = float(probabilitie_value_QLineEdit)  # 尝试将文本转换为浮点数
            print(f"转换后的值: {probabilitie_value_QLineEdit}")
        except ValueError:
            self.result_label.setText("输入的不是有效的数字")
        # 构建概率列表
        probabilities = [probabilitie_value_QLineEdit, 1 - probabilitie_value_QLineEdit]  # 分别对应随机读取和随机生成的概率

        for node in nodes:
            for _ in range(thread_count):
                thread = SocketThread(node["ip"], node["port"])
                thread.message_received.connect(self.display_message)

                send_thread = SendPacketsThread(thread, num_packets, probabilities, self.nodes_name)
                self.threads.append(send_thread)
                send_thread.start()

    def _stopServiceAddress(self):
        print("stopServiceAddress")
        self.task4_btn2.setEnabled(True)
        self.task4_btn3.setEnabled(False)
        self.task4_btn2.setStyleSheet(self.btn_style)
        self.task4_btn3.setStyleSheet("border: 10px solid #222; color: #222; padding: 30px; border-radius: 30px;")
        for send_thread in self.threads:
            send_thread.stop()

    def display_message(self, message):
        print(message)

    def closeEvent(self, event):
        self.close_all_threads()
        event.accept()

    def close_all_threads(self):
        for thread in self.threads:
            thread.close()

    def listenFirstPkg(self, server_conn):
        while True:
            data = "123"
            try:
                data = server_conn.recv(1024).decode('utf-8')
            except Exception as exp:
                print(f"Receive First Pkg ERROR: {exp}")
            if "RESPONSE" in data:
                print(f"listenFirstPkg >>>>> {data}")
                self.timeSpine2 = time.time()
                print(f"timeSpine1: {self.timeSpine1}")
                print(f"timeSpine2: {self.timeSpine2}")
                latency = round((self.timeSpine2 - self.timeSpine1) * 1000, 1)
                self.task1_text2.setText(str(latency))
                # self.server_socket.close()
                break

    def onRadioButtonToggled(self):
        self.selected_button = self.sender()
        if self.selected_button.isChecked():
            print(f'你选择了: {self.selected_button.text()}')

        if self.selected_button == self.task2_btn4:
            print("选项 1 被选中")
        elif self.selected_button == self.task2_btn5:
            print("选项 2 被选中")


def signal_handler(sig, frame):
    ClientWindow.close_all_threads()
    sys.exit(0)


class ClientWindow(QWidget):
    def __init__(self, manager: CfnNodeModel):
        super().__init__()
        self.setWindowTitle(" ")
        self.setGeometry(0, 0, 1920, 1080)
        self.client_manager = manager
        self.canvas = ClientCanvas(self, self.client_manager)
        self.setStyleSheet("border:none; background-color: {}".format(QColor(0, 17, 53).name()))
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.canvas)
        self.setLayout(self.layout)


if __name__ == '__main__':

    GuiHosts = ['c_node1', 'c_node2', 'c_node3']
    parser = argparse.ArgumentParser(description='cpn_node')
    parser.add_argument('config', metavar="CONFIG_FILE", type=str, help="Demo configuration JSON file.",
                        default="cpn_config-test-only-cpu.json")
    parser.add_argument('node_name', metavar="NODE_NAME", type=str,
                        help="Name of this node (should match the demo config file).")
    args = parser.parse_args()

    # 根据程序运行参数，读取demo配置信息
    demo_config = DemoConfigParser(args.config)

    # 根据程序运行参数，对照配置信息种自己的node_name，提取本node的配置参数
    node_name = args.node_name
    print(f"node_name is :{node_name}")
    node_config = None
    try:
        node_config = demo_config.get_node(node_name)
        print(f"node_config is :{node_config}")
    except:
        print(f"Node name `{node_name}` does not match configuration file. Aborting.")
        sys.exit(1)
    print(f"\nRunning as node {node_name}!",
          '\n    ' + '    \n    '.join([str(k) + '=' + str(v) for k, v in node_config.items()]) + '\n')

    GUI_ip, GUI_port = demo_config.gui_controller_host_ip, demo_config.gui_controller_host_port
    print(f"Will connect to GUI @ ({GUI_ip}, {GUI_port})")

    # node_model = None
    if node_name == "camera_1":
        n = FogCam(demo_config, node_config, sim=False)
        n.start()
    else:
        node_model = CfnNodeModel(demo_config, node_config)
        node_model.start()

        app = QApplication(sys.argv)
        if node_name in ['client']:
            c_window = ClientWindow(node_model)
            c_window.show()
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
        if node_name in ['monitor_client']:
            monitor_window = Surveillance(node_model)
            monitor_window.show()
        sys.exit(app.exec_())
