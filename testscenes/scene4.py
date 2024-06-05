# -*- coding: utf-8 -*-
"""
@Time: 5/23/2024 8:48 PM
@Author: Honggang Yuan
@Email: honggang.yuan@nokia-sbell.com
Description:
"""
import signal
import socket
import sys
import threading
import time
from multiprocessing import Pipe, Queue
from time import sleep

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import pyqtSlot, Qt, QTimer
from PyQt5.QtGui import QPalette, QColor, QBrush, QPixmap, QIcon
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QPushButton, QLabel, QGroupBox, QVBoxLayout, QTableWidgetItem, \
    QHeaderView, QTableWidget, QWidget

from utils.HeatMap import HeatMap


class ServerThread(threading.Thread):
    def __init__(self, ip, port):
        super().__init__()
        self.ip = ip
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.ip, self.port))
        self.server_socket.listen(5)  # Allow up to 5 connections
        self.packet_count = 0
        self.running = True
        print(f"Server started at {self.ip}:{self.port}")

    def run(self):
        packet_counter_thread = threading.Thread(target=self.count_packets)
        packet_counter_thread.start()

        while self.running:
            client_socket, addr = self.server_socket.accept()
            print(f"Connection from {addr}")
            client_handler = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_handler.start()

    def handle_client(self, client_socket):
        with client_socket:
            while self.running:
                data = client_socket.recv(1024)
                if not data:
                    break
                self.packet_count += 1

    def count_packets(self):
        while self.running:
            time.sleep(1)
            print(f"Packets received in the last second: {self.packet_count}")
            self.packet_count = 0

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
        # self._initScene()
        self.initConnections()

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

    def _initMonitorQueue(self):
        self.monitor_q_cpu_hm_node1 = self.cfn_manager.resource_StatMon['c_node1_cpu']  # 算力节点1 CPU
        self.monitor_q_cpu_hm_node2 = self.cfn_manager.resource_StatMon['c_node2_cpu']  # 算力节点2 CPU
        self.monitor_q_cpu_hm_node3 = self.cfn_manager.resource_StatMon['c_node3_cpu']  # 算力节点3 CPU

    def initConnections(self):
        # self.cfn_manager.signal_emitter.QtSignals.addrRequest_test.connect(self.addrRequest)
        pass

    def signal_handler(self, sig, frame):
        self.server_thread.stop()
        sys.exit(0)

    def addrRequest(self):
        server_ip = "127.0.0.1"
        server_port = 12345
        self.server_thread = ServerThread(server_ip, server_port)
        self.server_thread.start()

        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.pause()

    def reset(self):
        # for i in self.threads:
        #     i.stop()
        # self.print_thread.stop()
        pass

