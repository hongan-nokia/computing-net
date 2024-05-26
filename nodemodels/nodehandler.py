# -*- coding: utf-8 -*-
"""
@Time: 5/16/2024 10:50 AM
@Author: Honggang Yuan
@Email: honggang.yuan@nokia-sbell.com
Description: 
"""
from time import sleep
from threading import Thread
from multiprocessing import Process
from multiprocessing.connection import Connection, Listener

from utils.configparser import DemoConfigParser

_SECRET_SIGNAL = 'demo terminate'  # 只是调试的时侯用于结束进程


def subproc_print(pid, msg):
    print(f'#### ({pid}) : {msg}')


def node_handler_node2gui(node_name: str, node_conn: Connection, gui_conn: Connection):
    """
    Handler for the nodes who use a Python connection.
    This function receive node's info and forwards to GUI frontend.
    """
    print(f"Starting {node_name} node2gui forwarding thread.")
    while True:
        try:
            msg = node_conn.recv()
        except (EOFError, ConnectionResetError):
            node_conn.close()
            gui_conn.send((node_name, '_disconnect', None))  # inform the gui to turn off the node
            break

        # 从node发来的消息格式，一般是(cmd: str, arg: Any)，这里把它加上一个node_name标识转发给GUI，变成：
        # （node_name: str, cmd:str, arg: Any）

        if type(msg) is tuple:
            (cmd, arg) = msg
        else:
            cmd = msg
            arg = None
        msg_with_name = (node_name, cmd, arg)
        if cmd == '_disconnect':  # special message
            gui_conn.send((node_name, '_disconnect', None))
            break
        elif cmd == '_discard':  # special message
            pass
        elif cmd == _SECRET_SIGNAL:  # special message
            gui_conn.send((node_name, _SECRET_SIGNAL, None))
            break
        else:
            gui_conn.send(msg_with_name)

    node_conn.close()
    print(f"Exiting {node_name} node2gui forwarding thread.")


def node_handler_gui2node(node_name: str, node_conn: Connection, gui_conn: Connection):
    """
    Handler for the nodes who use a Python connection.
    This function receive GUI's commands and forwards to node.
    """
    print(f"Starting {node_name} gui2node forwarding thread.")
    while True:
        try:
            msg = gui_conn.recv()
        except Exception as err:
            print(node_name, str(err))
            print(node_name, 'gui_conn problem! exiting subprocess...')
            break
        if (msg[0] == 'terminate') or (msg[0] == 'shutdown'):  # special message
            try:
                node_conn.send((msg[0], node_name))
            except Exception as err:
                print(node_name, str(err))
            break
        elif msg[0] == '_disconnect':  # 节点发出的断开请求
            break
        else:  # normal msg may be: 'start local', 'start remote', 'shutdown', 'power on'
            try:
                node_conn.send(msg)
            except Exception as err:
                print(node_name, str(err))
                print(node_name, 'node_conn problem!')
    print(f"Exiting {node_name} gui2node forwarding thread.")


class NodeManager(object):
    """
    This class provides a subprocess that handles node connections and signaling forwarding.
    """

    def __init__(self, resources: dict, demo_config: DemoConfigParser) -> None:
        self.demo_config = demo_config
        self.resources = resources
        self.nodes_to_connect = list(resources.keys())
        self.pipe_pairs = list(resources.values())  # double pipe
        if len(self.nodes_to_connect) != self.demo_config.n_nodes:
            raise ValueError("NodeManager: this should not happen.")
        print(f"Nodes to be connected: {self.nodes_to_connect}")
        self.proc = Process(target=self._mainfunc,
                            args=(self.nodes_to_connect, self.pipe_pairs,),
                            name='node_manager')
        self.node_threads = []

    def _mainfunc(self, nodes: list, pipe_pairs: list):
        """
        This will be spawned as a subprocess.
        根据Demo配置信息, 主动连接node或监听node连接请求。对每个node, 启动一个对应的handler线程。
        """
        address = (self.demo_config.gui_controller_host_ip, self.demo_config.gui_controller_host_port)
        print(f"Start server @ {address}")
        with Listener(address) as listener:
            while True:
                conn = listener.accept()
                print('$$$$$$$$$$$ connection accepted from', listener.last_accepted)
                msg = conn.recv()
                print(f'Init msg is: {msg}')
                name_reported = msg if type(msg == str) else msg[0]
                if name_reported in ['_END_DEMO_', _SECRET_SIGNAL]:
                    print("Demo termination signal received. Now try to exit node_manager process.")
                    self.close()
                    break
                elif name_reported not in self.nodes_to_connect:
                    print(f"{name_reported} is not a valid node name! Check the configuration!")
                    conn.close()
                else:
                    print(f"*******************************"
                          f"Start connect to slaver"
                          f"*******************************")
                    intfc_type = self.demo_config.get_node_interface_type(name_reported)
                    if intfc_type == 'tcp_client':
                        # node connection, Gui connection
                        t_n2g = Thread(target=node_handler_node2gui,
                                       args=(name_reported, conn, pipe_pairs[nodes.index(name_reported)][1]))
                        t_n2g.start()
                        t_g2n = Thread(target=node_handler_gui2node,
                                       args=(name_reported, conn, pipe_pairs[nodes.index(name_reported)][1]))
                        t_g2n.start()
                    else:
                        raise ValueError(f"Node interface type {intfc_type} Not implemented yet!")

                    self.node_threads.append((name_reported, (t_n2g, t_g2n)))

            print("Exiting node_manager process.")

    def send_cmd_to_node(self, node_name: str, cmd: str, cmd_arg=None) -> None:
        try:
            self.resources[node_name][0].send((cmd, cmd_arg))
        except Exception as err:
            print(f"send_cmd_to_node() ERROR - {err}")

    def close(self):
        """ same as stop(). """
        for n in self.nodes_to_connect:
            self.send_cmd_to_node(n, 'terminate')
            sleep(0.1)
        print("node_manager closed successfully.")

    def stop(self):
        """ same as close(). """
        self.close()

    def start(self):
        self.proc.start()
