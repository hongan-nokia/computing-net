import argparse
import sys
from pathlib import Path

from PyQt5.QtCore import Qt, pyqtSlot, QSize
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtGui import QKeyEvent, QPixmap, QIcon, QColor
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QStackedWidget, QWidget, QVBoxLayout, QGroupBox, \
    QHBoxLayout, QSpacerItem, QSizePolicy

from nodemodels.cfnnodemodel import CfnNodeModel
from utils.configparser import DemoConfigParser


class Canvas(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QtWidgets.QHBoxLayout(self)
        self.setWindowTitle("")
        self.resize(1920, 1080)
        self.groupBox = QGroupBox("")

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

        self._initTitle()

        self.left_spacer = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout.addItem(self.left_spacer)

        self._initTaskOne()

        self.middle_spacer = QSpacerItem(200, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.horizontalLayout.addItem(self.middle_spacer)

        self._initTaskTwo()

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
        self.teak2_box = QtWidgets.QGroupBox(self.view_box)
        self.teak2_box.setStyleSheet("background: #ccc; border-radius: 50px;")
        self.teak2_layout = QtWidgets.QVBoxLayout(self.teak2_box)

        # ####
        self.task2_title_box = QtWidgets.QGroupBox(self.teak2_box)
        self.task2_title_box.setStyleSheet("border-radius: 20px; width: 400px;")
        self.task2_title_layout = QtWidgets.QVBoxLayout(self.task2_title_box)

        self.task2_title = QtWidgets.QLabel(self.teak2_box)
        self.task2_title.setText("测试三")
        self.task2_title.setFont(self.task_font_size)
        self.task2_title.setStyleSheet("color: #222;")
        self.task2_title.setAlignment(Qt.AlignCenter)

        self.task2_title_layout.addWidget(self.task2_title)
        self.teak2_layout.addWidget(self.task2_title_box)

        # ####
        self.task2_btn1_box = QtWidgets.QGroupBox(self.teak2_box)
        self.task2_btn1_layout = QtWidgets.QVBoxLayout(self.task2_btn1_box)

        self.task2_btn1 = QtWidgets.QPushButton(self.teak2_box)
        self.task2_btn1.setText("服务寻址测试")
        self.task2_btn1.setFont(self.task_font_size)
        self.task2_btn1.setStyleSheet(self.btn_style)

        self.task2_btn1_layout.addWidget(self.task2_btn1)
        self.teak2_layout.addWidget(self.task2_btn1_box)

        self.horizontalLayout.addWidget(self.teak2_box)

        # ####
        self.task2_btn2_box = QtWidgets.QGroupBox(self.teak2_box)
        self.task2_btn2_layout = QtWidgets.QVBoxLayout(self.task2_btn2_box)

        self.teak2_btn2 = QtWidgets.QPushButton(self.teak2_box)
        self.teak2_btn2.setText("算力寻址测试")
        self.teak2_btn2.setFont(self.task_font_size)
        self.teak2_btn2.setStyleSheet(self.btn_style)

        self.task2_btn2_layout.addWidget(self.teak2_btn2)
        self.teak2_layout.addWidget(self.task2_btn2_box)

        self.horizontalLayout.addWidget(self.teak2_box)

        # ####
        self.teak2_btn3_box = QtWidgets.QGroupBox(self.teak2_box)
        self.teak2_btn3_layout = QtWidgets.QVBoxLayout(self.teak2_btn3_box)

        self.teak2_btn3 = QtWidgets.QPushButton(self.teak2_box)
        self.teak2_btn3.setText("内容寻址测试")
        self.teak2_btn3.setFont(self.task_font_size)
        self.teak2_btn3.setStyleSheet(self.btn_style)

        self.teak2_btn3_layout.addWidget(self.teak2_btn3)
        self.teak2_layout.addWidget(self.teak2_btn3_box)

        self.horizontalLayout.addWidget(self.teak2_box)

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


class ClientWindow(QWidget):
    def __init__(self, manager: CfnNodeModel):
        super().__init__()
        self.setWindowTitle(" ")
        self.setGeometry(0, 0, 1920, 1080)
        self.client_manager = manager
        self.canvas = Canvas()
        self.setStyleSheet("border:none; background-color: {}".format(QColor(0, 17, 53).name()))
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.canvas)
        self.setLayout(self.layout)


if __name__ == '__main__':

    GuiHosts = ['c_node1', 'c_node2', 'c_node3']
    parser = argparse.ArgumentParser(description='cpn_node')
    parser.add_argument('config', metavar="CONFIG_FILE", type=str, help="Demo configuration JSON file.",
                        default="cpn_config-test.json")
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

    # node_model = CfnNodeModel(demo_config, node_config)
    # node_model.start()
    node_model = None

    app = QApplication(sys.argv)
    if node_name in ['client']:
        c_window = ClientWindow(node_model)
        c_window.show()
    sys.exit(app.exec_())
