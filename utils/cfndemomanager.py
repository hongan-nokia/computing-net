# -*- coding: utf-8 -*-
"""
@Time: 5/16/2024 10:49 AM
@Author: Honggang Yuan
@Email: honggang.yuan@nokia-sbell.com
Description: 
"""
from PyQt5.QtCore import QObject, pyqtSignal
from threading import Thread
from multiprocessing.connection import wait, Client
from typing import Union

from utils.configparser import DemoConfigParser
from utils.nodehandler import NodeManager
from utils.statemonitor import StateMonitor

_EXIT_DEMO_SIGNAL = 'demo terminate'  # 调试的时侯用于结束进程


class CfnDemoManagerSignals(QObject):
    """
    Demo界面所需要的后端触发信号, 都在这里定义进行。

    一般来说这些信号的意义, 都是为了通知前端GUI “刚刚收到了某个node发来的某种消息”,
    从而GUI可触发动画或者其他操作。
    具体什么消息映射到哪个signal, 其逻辑都在下面SgnlEmitter.signal_emit_logic()函数实现。
    """
    container_connected = pyqtSignal(int)  # node_id
    container_disconnected = pyqtSignal(int)  # node_id
    container_state_report = pyqtSignal(int, str)  # node_id, current state

    container_service_deploy = pyqtSignal(int, str)  # node_id, state ('come' or 'gone')
    container_resource_report = pyqtSignal(int, dict)  # node_id, pulse rate
    container_task_list = pyqtSignal(int, dict)  # node_id, pulse rate
    container_ue_msg = pyqtSignal(str)  # node_id, pulse rate


class SgnlEmitter:
    """
    这个class是demo_manager的Qt信号发射器。即, 根据节点发来的消息, 按需转换成发给GUI的signal。
    其核心内容, 就是一个signal_emit_logic()函数, 控制着GUI前端所需的信号触发逻辑。
    """

    def __init__(self, dm: 'CfnDemoManager') -> None:
        self.demo_manager = dm
        self.QtSignals = CfnDemoManagerSignals()

    def signal_emit_logic(self, node_name: str, command: str, command_arg):
        """
        函数参数就是从节点发来的信息, 格式是个三元组: node_name, command, command_arg, 分别代表
        节点名(谁发来的命令)、命令关键字、命令参数。本函数负责判断这些信息, 并转换成某种具体的信号触发。

        当然可以不仅仅触发Qt信号, 还可以调用self.demo_manager的其他接口, 实现任何需要做的动作。
        """
        node_id = self.demo_manager.node_names.index(node_name) if (node_name in self.demo_manager.node_names) else -1
        ret = ''

        if command == '_disconnect':
            self.QtSignals.container_disconnected.emit(node_id)
            self.demo_manager.send_command(node_name, '_disconnect')
        elif command == 'ready':
            self.demo_manager.send_command(node_name, 'startlocal')
            self.QtSignals.container_connected.emit(node_id)

        elif command == 'cfnret':
            self.QtSignals.container_resource_report.emit(node_id, command_arg)

        elif command == 'state':
            print(f'node {node_name} reported state: {command_arg}')
            self.QtSignals.container_state_report.emit(node_id, command_arg)

        elif command == 'current_tasks':
            self.QtSignals.container_task_list.emit(node_id, command_arg)

        elif command == 'warning':
            print(f"{node_name} says WARNING: {command_arg}")

        elif command == 'ue_msg':
            self.QtSignals.container_ue_msg.emit(command_arg)

        elif command == 'service_mgn':
            self.QtSignals.container_service_deploy.emit(node_id, command_arg)
        elif command == _EXIT_DEMO_SIGNAL:
            ret = _EXIT_DEMO_SIGNAL
        else:
            print('????????? (signal_emit_logic) msg =', (node_name, command, command_arg))

        return ret


class CfnDemoManager(object):
    """
    Computing Power Network demonstration backend interface.
    主要功能包括：
    1. Spawn 1 subprocess:
        - the `node_manager` process, which maintains communication with all nodes.
    2. Generate Qt signals based on nodes' activities.
        - the `gui_sgnl_gen` thread. Convert nodes' messages into frontend Qt signals.
    """

    def __init__(self, demo_config: DemoConfigParser, resource_NodeMan, resource_StatMon):
        """
        Arguments:
            demo_config - the demo configuration.
            resource_NodeMan - interprocess resource list for node_manager subprocess.   type:Pipe
            resource_StatMon - interprocess resource list for state_monitor subprocess.  type:Queue
            sim - if True, start simulation mode.
        """
        # important class variables
        self.demo_config = demo_config
        self.resource_NodeMan = dict(resource_NodeMan)  # inter process resource for node_manager
        self.resource_StatMon = dict(resource_StatMon)

        self.app_ip = demo_config.gui_controller_host_ip  # IP address of the host, for nodes/monitor sources to connect.
        self.app_port = demo_config.gui_controller_host_port  # TCP port the GUI listens on (for nodes to connect).

        # socket : 10.70.16.250:10070
        self.n_nodes = demo_config.n_nodes  # account of nodes
        self.node_names = [n['node_name'] for n in demo_config.nodes]
        self.monitor_names = [n['monitoring_source_name'] for n in demo_config.monitoring_sources]

        # 首先定义所有的跟前端互动的Qt signal。根据具体demo情景，修改`init_qt_signals()`函数
        self.signal_emitter = SgnlEmitter(self)

        # start GUI signal generation thread (nodes communication)
        self.gui_sig_gen_thread = Thread(target=self._gui_sgnl_gen, args=([i[1][0] for i in resource_NodeMan],))
        # (i[1][0]) : for node_StateMon
        # (i[1][0]) : <multiprocessing.connection.PipeConnection object at 0x000001C309C839D0> for resource_Nodeman
        self.gui_sig_gen_thread.start()

        # start subprocesses (including communication Threads and resource monitoring Threads)
        self._start_subprocesses()

    def _start_subprocesses(self):
        self.node_manager = NodeManager(self.resource_NodeMan, self.demo_config)
        self.state_monitor = StateMonitor(self.resource_StatMon, self.demo_config)
        self.node_manager.start()
        self.state_monitor.start()

    def _gui_sgnl_gen(self, gui_pipes):
        """
        本函数作为连接前后端的 “桥梁线程” 一直运行: 接收节点发过来的消息, 并根据消息内容产生Qt signal.
        通过 pipe->readers 接收算力节点的消息:msg，将msg转换为Qt signal并通过SgnlEmitter.signal_emit_logic()转发出去
        """
        msg = []
        readers = [i for i in gui_pipes]  # type : pipe
        while readers:  # loop until the container connections are all ended
            for conn in wait(readers):
                try:
                    msg = conn.recv()
                except EOFError:
                    readers.remove(conn)
                    break
                except Exception as err:
                    print('(gui_sgnl_gen) msg = ', msg, 'error=', err)

                ret = self.signal_emitter.signal_emit_logic(msg[0], msg[1], msg[2])
                if ret == _EXIT_DEMO_SIGNAL:
                    print(f"DEBUG - _gui_sgnl_gen thread received {_EXIT_DEMO_SIGNAL}, exiting.")
                    readers = []
                    break

        print(f'exiting gui_sgnl_gen()')
        self.close()

    def send_command(self, target_node: Union[str, int], cmd: str, cmd_arg=None):
        """
        target_node - 可以是int或者str, 分别代表node id和node name. 事实上id就是self.node_names中对应name的下标
        """
        if type(target_node) is int:
            target_node = self.node_names[target_node]
        print(f"DEBUG - Sending command to node: {target_node}: {cmd, cmd_arg}")
        self.node_manager.send_cmd_to_node(target_node, cmd, cmd_arg)

    def close(self):
        # end the subprocesses
        print("Closing demo_manager!")
        if self.node_manager.proc.is_alive():
            with Client((self.app_ip, self.app_port)) as conn:
                conn.send(_EXIT_DEMO_SIGNAL)
        self.node_manager.close()
        self.state_monitor.close()
        self.node_manager.proc.join()
        self.state_monitor.proc.join()
        # end the gui_sgnl_gen thread
        try:
            list(self.resource_NodeMan.values())[0][1].send(('', _EXIT_DEMO_SIGNAL, None))
        except Exception as err:
            print(err)
