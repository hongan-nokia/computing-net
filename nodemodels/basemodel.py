# -*- coding: utf-8 -*-
"""
@Time: 5/17/2024 9:53 AM
@Author: Honggang Yuan
@Email: honggang.yuan@nokia-sbell.com
Description: 
"""
import time
from abc import ABC, abstractmethod
from typing import Any, Callable, Tuple
from threading import Lock, Thread
from multiprocessing import Event, connection
from time import sleep
import sys

from utils.configparser import DemoConfigParser, NodeConfig

# 所有子进程通过判断下面这个event退出，以及用一个queue往主进程发消息（单向），一个task_cancel由主进程指示某个task结束
demo_terminate_event = Event()


class TerminateDemoCmd:
    def __eq__(self, other):
        return True if other in ['terminate', 'shutdown'] else False


terminate_demo_cmd = TerminateDemoCmd()


class ConnBreakErr(ValueError):
    pass


def GUI_msg_handler(node_model_specific_msg_handler):
    def wrapper(msg: Tuple[str, Any], node_obj: 'BaseNodeModel'):
        try:
            cmd, args = msg[0], msg[1:]
        except:
            node_obj.print("GUI's message parsing error. Do nothing.")
            node_obj.send2gui(('warning', 'message parsing error, wronng cmd format!'))
            return
        try:
            ret = node_model_specific_msg_handler(cmd, args, node_obj)
        except Exception as err:
            s = f"command {cmd, args} processing error: {err}."
            node_obj.print(s)
            node_obj.send2gui(('warning', s))
            return

        if not ret:  # 没有返回值就是成功处理了
            return
        else:  # 没成功的处理，原样返回 (cmd, arg)
            try:
                cmd, args = ret
            except:
                node_obj.print(f"{node_model_specific_msg_handler.__name__} returns {ret}. Should return (cmd, arg).")
                node_obj.send2gui(('warning', f'unsuccessful cmd processing {msg}'))
                return

            # 下面是经过 node_model_specific_msg_handler() 却没被处理的命令：
            if cmd in ['startlocal', 'startremote', 'poweron']:
                node_obj.print(f'Obsoleted cmd: {cmd}, do nothing')
                return
            elif cmd in ['shutdown', 'terminate']:
                node_obj.send2gui(('_disconnect', None))
                node_obj.print('setting terminalDemo to True')
                node_obj.terminateDemo = True
                node_obj.terminate_event.set()

            else:
                node_obj.print(f'received unknown cmd: {cmd}, ???')

    return wrapper


def GUI_task_cmd_handler(node_model_specific_task_cmd_handler: Callable):
    """
    封装task子命令的处理函数。主要是1.检查命令格式；2.接住异常
    """

    def wrapper(task_subcmd: str, node_obj: 'BaseNodeModel'):
        # 输入是个包含task名字和参数的字符串, 格式为 ‘task_name[空格]task_params’
        t = tuple(task_subcmd.split())
        if len(t) != 2:
            node_obj.send2gui(('Error',
                               "task command's arguments must be `task_name`+space+`task_params`. task_params cannot have spaces"))
            node_obj.print(f"Received task command, content= {t}. Format error. Do nothing.")
        else:
            node_obj.print(f"Received task command, content= {t}. ")
            try:
                ret = node_model_specific_task_cmd_handler(t[0], t[1], node_obj)
                if ret:
                    s = f'Unrecognized task command: {t}. Ignore.'
                else:
                    return
            except Exception as err:
                s = err
            node_obj.send2gui(('warning', s))
            node_obj.print(s)

    return wrapper


class BaseNodeModel(ABC):
    """
    CPN Demo节点的基础定义。
    主要的attribute有：
        demo_conf/node_conf - 配置文件提取出的信息
        GUI_addr - 主程序地址(ip, port)
        conn_GUI - 跟主程序之间的连接（multiprocessing.connection对象）
        terminateDemo - 需要结束线程时置1
        terminate_event - 有时候动态启动一些子进程，通过这个跨进程Event结束之
        t_gui - 与GUI通信的线程
        process_GUI_msg - 需要在初始化时赋给msg_process_fn的消息处理函数

    主要的methods：
        _init_conn_GUI() - 建立连接
        _gui_interaction() - 作为一个独立线程一直运行，负责从GUI收命令交由process_GUI_msg()处理。
        send2gui() - 发(msg, arg)格式的消息给GUI
        start() - 抽象方法（必须由子类进行重构），一般是启动节点行为逻辑子进程/线程
        close() - 抽象方法，与start()对应的，手动释放资源

    抽象方法（节点模型子类必须重载）:
        start() - 这个会被节点上运行的入口程序默认调用。作用是放启动子线程、子进程的逻辑代码
        close() - 这个在 t_gui 线程结束时会被自动调用。清理子线/进程的资源。
    """

    def __init__(self, demo_config: DemoConfigParser, node_config: NodeConfig, msg_process_fn: Callable) -> None:
        self.demo_conf = demo_config
        self.node_conf = node_config
        self.process_GUI_msg = msg_process_fn
        self.terminate_event = demo_terminate_event
        self.GUI_addr = (self.demo_conf.gui_controller_host_ip, self.demo_conf.gui_controller_host_port)
        self.conn_GUI = None  # 与主程序之间的通信连接接口
        self._conn_lock = Lock()
        self.terminateDemo = False
        print(f"[{self.node_conf.node_name}] - Node model `{self.__class__.__name__}` process starts.")
        # 尝试连接主程序节点
        if not self._init_conn_GUI():
            self.print('connect to cloud server failed! Exiting.')
            raise ValueError('connect to server failed.')

        # 启动主节点通信线程
        if self.node_conf.node_name == 'camera_1' or 'Service_Request' in self.node_conf.node_name:
            self.t_gui = Thread(name=f'{self.node_conf.node_name}_2GUI', target=self._gui_interaction_camera)
            self.t_gui.start()

        else:
            self.t_gui = Thread(name=f'{self.node_conf.node_name}_2GUI', target=self._gui_interaction)
            self.t_gui.start()

    def _init_conn_GUI(self, max_try=100):
        """
        Initialize the connection to GUI App.
        The first message after connecting to GUI is to report this node's name.
        """
        for i in range(max_try):
            try:
                self.conn_GUI = connection.Client(self.GUI_addr, authkey=b'cpn')
                print(f'[{self.node_conf.node_name}] connected to cloud server!')
                self.conn_GUI.send(self.node_conf.node_name)
                return True
            except:
                sleep(1)
                print(f'waiting for server @ {self.GUI_addr} {i}th time.')
            if i == max_try - 1:
                return False

    def _gui_interaction(self):
        msg = None
        idx = 0
        # while not self.terminateDemo and 'camera' not in self.node_conf.node_name:
        while not self.terminateDemo:
            # 从GUI侧接收消息
            try:
                if idx < 3:
                    if self.conn_GUI.poll(3):
                        msg = self.conn_GUI.recv()
                        idx = 0
                    else:
                        idx += 1
                else:
                    print(f" ###########################  Unknown is: \n")
                    raise ValueError
            # except (EOFError, ConnectionResetError, ConnectionAbortedError, ValueError, OSError) as err:
            except Exception as err:
                print(f" ###########################  err is: {str(err), repr(err)}")
                self.print('cloud connection broke!')
                print("self.conn_GUI.close()")
                self.conn_GUI.close()
                print("self._init_conn_GUI() done 11111")
                self._init_conn_GUI()
                # self.terminateDemo = True
                # self.terminate_event.set()
                continue
            # 处理消息。这里意外情形会比较多，所以尽量保留下面一坨异常处理别删掉
            try:
                if msg is None:
                    self.print('Unexpected msg receiving failure! ')
                self.process_GUI_msg(msg, self)
                if self.terminateDemo:
                    break
            except (OSError, ConnBreakErr) as err:  # GUI侧断开
                print(err, '\nExiting')
                # self.terminateDemo = True
                # self.terminate_event.set()
                self._init_conn_GUI()
                print("self._init_conn_GUI() done 22222")
            except:  # 处理消息过程中的错误，往往是往GUI发消息时网络出错
                print('#' * 50 + '\n#  ERROR: RECEIVED ' + str(msg) + '\n' + '#' * 50)
                # print("Unexpected error:", sys.exc_info()[0])
                # raise
                self._init_conn_GUI()
                print("self._init_conn_GUI() done 33333")
        self.print('exiting _gui_interaction()')
        self.conn_GUI.close()
        self.close()

    def _gui_interaction_camera(self):
        msg = None
        while not self.terminateDemo:
            # 从GUI侧接收消息
            try:
                msg = self.conn_GUI.recv()
                self.print(f'receives msg_cld = {msg}')  ########################### debug
            except (EOFError, ConnectionResetError):
                pass
                # self.print('cloud connection broke!')
                # self.terminateDemo = True
                # self.terminate_event.set()
                # break
            # 处理消息。这里意外情形会比较多，所以尽量保留下面一坨异常处理别删掉
            try:
                if msg == None: self.print('Unexpected msg receiving failure! ')
                self.process_GUI_msg(msg, self)
                if self.terminateDemo:
                    break
            except (OSError, ConnBreakErr) as err:  # GUI侧断开
                print(err, '\nExiting')
                self.terminateDemo = True
                self.terminate_event.set()
            except:  # 处理消息过程中的错误，往往是往GUI发消息时网络出错
                print('#' * 50 + '\n#  ERROR: RECEIVED ' + str(msg) + '\n' + '#' * 50)
                print("Unexpected error:", sys.exc_info()[0])
                raise
        self.print('exiting _gui_interaction_camera()')
        self.conn_GUI.close()
        self.close()

    def send2gui(self, msg: Tuple[str, any]):
        try:
            if self.conn_GUI:
                self._conn_lock.acquire()
                self.conn_GUI.send(msg)
                self._conn_lock.release()
            else:
                self.print("WARNING: send() before cloud connection exist!!!")
        except (OSError, ConnectionAbortedError) as err:
            print(err, '\nExiting')
            # raise ConnBreakErr
            self.terminateDemo = True
            self.terminate_event.set()
        except:
            print("Unexpected error when reporting state:", sys.exc_info()[0])
            raise

    def print(self, s: str):
        print(f'[{self.node_conf.node_name}] - {s}')

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def close(self):
        pass
