# -*- coding: utf-8 -*-
"""
@Time: 5/23/2024 2:09 PM
@Author: Honggang Yuan
@Email: honggang.yuan@nokia-sbell.com
Description: 
"""

import random
from multiprocessing import Process, SimpleQueue, Value
from threading import Thread
from typing import Union

from PyQt5.QtCore import QObject, pyqtSignal

from nodemodels.basemodel import GUI_msg_handler, GUI_task_cmd_handler, BaseNodeModel
from utils import DemoConfigParser, NodeConfig
from utils.computetaskutils import *


@GUI_msg_handler
def process_GUI_msg(cmd: str, args: tuple, node_obj: 'CfnNodeModel'):
    """
    命令执行逻辑，都写在这个函数里。
    msg - 主程序(GUI)发来的命令
    node_obj - 响应命令的节点对象(在后面具体定义的)

    可以调用node_obj的方法做出节点行为.
    """

    if cmd == 'task':  # 收到task命令时，跟着的参数是一个task子命令字符串，丢给专门的task处理函数
        # task命令的参数是一个字符串，包含一个子命令系统：格式为 ‘task_name[空格]task_params’
        task_sub_cmd = args[0]
        node_obj.start_task(task_sub_cmd, node_obj)
        return

    elif cmd == "show_task":  # 返回当前的所有task列表
        node_obj.send2gui(('current_tasks', node_obj.tasks))
        node_obj.print(f'current tasks: {node_obj.tasks}')

    elif cmd in ['cancel_task', 'stop_task']:
        # （跟"task"命令完全对应，那边是启动，这里是结束）
        task_key = args[0]
        node_obj.print(f"Received cancel_task command, content= {task_key}. ")
        task_name = task_key.split(" ")[0]
        task_args = task_key.split(" ")[1]
        # node_obj.signal_emitter.signal_emit_logic(task_name, 'down', task_args)
        node_obj.cancel_task(task_key)
        return

    else:
        return cmd, args


task_cmd_q = SimpleQueue()  # 每个task进程需要发消息给GUI时，消息放到这个queue里
task_cancel = Value('i', 0)  # 每个task进程，当发现 task_cancel.value 等于自己的pid, 就结束自己（并且把value置会0）


@GUI_task_cmd_handler
def start_node_task(taskname: str, args: str, node_obj: 'CfnNodeModel'):
    """
        Task子命令处理函数。GUI发过来的原始消息是('task', 'taskname arg1_arg2_arg3')，其中
        taskname字符串就对应到这里函数输入的 taskname参数, 下划线或连字符连起来的args字符串，就是这里函数输入的args。
    """
    ServiceName = ['s1', 's2', 's3']
    if f'{taskname} {args}' in node_obj.tasks.keys():  # 检查一下是否这个同样的task已经在运行
        node_obj.print(f'Already running task {taskname} {args}. Do nothing.')
        node_obj.send2gui(
            ('warning', f'Already running task {taskname} {args}. Do nothing.'))
        return

    elif taskname in ServiceName:
        # node_obj.signal_emitter.signal_emit_logic(taskname, 'up', args)
        task_pid = random.randint(10, 100)
        node_obj.tasks[f'{taskname} {args}'] = task_pid

    elif taskname == 'vlc':  # vlc作为server将文件stream到指定的client
        file_path = './' + str(args).split('_', -1)[0]  # 所要播放的文件路径
        start_pos = str(args).split('_', -1)[1]
        addr, port = "192.168.2.128", "1234"
        p = Process(target=vlc_streaming, args=(addr, port, file_path, start_pos, task_cmd_q, task_cancel, node_obj.terminate_event))
        node_obj.tasks[f'{taskname}'] = -1
        p.start()

    elif taskname == 'vlcc':  # vlc作为server将文件stream到指定的client
        file_path = './' + str(args).split('_', -1)[0]  # 所要播放的文件路径
        start_pos = str(args).split('_', -1)[1]
        addr, port = "192.168.2.128", "1234"
        p = Process(target=vlcc_streaming, args=(addr, port, file_path, start_pos, task_cmd_q, task_cancel, node_obj.terminate_event))
        node_obj.tasks[f'{taskname}'] = -1
        p.start()

    elif taskname == 'mvlc':  # 在server端部署vlc接收程序接收来自UE侧的视频流（多播）
        params = args.split("#")
        param_list = [params[0], params[1]]
        addr, eth_face = param_list[0], param_list[1]
        print("execute mvlc")
        p = Process(target=vlc_receiver, args=(addr, eth_face, task_cmd_q, task_cancel, node_obj.terminate_event))
        node_obj.tasks[f'{taskname} {args}'] = -1
        p.start()
    # elif taskname == 'cfnres':
    #     print(args)
    #     p = Process(target=cfnResHandler, args=(task_cmd_q, task_cancel, node_obj.terminate_event))
    #     node_obj.tasks[f'{taskname} {args}'] = -1
    #     p.start()
    # elif taskname == 'onos':
    #     onos_tag = onos_handler(pid_args=args)
    #     print(f"onos_handler tag is: {onos_tag}")
    #
    # elif taskname == 'onos_del_all':
    #     onos_del_tag = onos_del_all_flow(pid_args=args)
    #     print(f"onos_del_all_flow tag is: {onos_del_tag}")
    #
    # elif taskname == 'onos_add_all':
    #     onos_post_tag = onos_post_all_flow(pid_args=args)
    #     print(f"onos_add_all_flow tag is: {onos_post_tag}")

    # elif taskname == 'kubernetes':
    #     p = Process(target=kubernetes_pod_handler, args=(taskname, args, task_cmd_q, task_cancel, node_obj.terminate_event))
    #     node_obj.tasks[f'{taskname} {args}'] = -1
    #     p.start()
    #
    # elif taskname == 'kubernetes_del':
    #     _stdout = sys.stdout
    #     _stderr = sys.stderr
    #     _stdout = subprocess.DEVNULL
    #     _stderr = subprocess.DEVNULL
    #     del_cmd = f"kubectl delete --all pods -n default --force"
    #     subprocess.run(del_cmd, shell=True, stdout=_stdout, stderr=_stderr)
    #     sleep(1)

    elif taskname == 'AI_trainer1':
        p = Process(target=cfn_bk_service, args=(taskname, args, task_cmd_q, task_cancel, node_obj.terminate_event))
        node_obj.tasks[f'{taskname} {args}'] = -1
        p.start()
    elif taskname == 'AI_trainer2':
        p = Process(target=cfn_bk_service, args=(taskname, args, task_cmd_q, task_cancel, node_obj.terminate_event))
        node_obj.tasks[f'{taskname} {args}'] = -1
        p.start()
    elif taskname == 'AI_trainer3':
        p = Process(target=cfn_bk_service, args=(taskname, args, task_cmd_q, task_cancel, node_obj.terminate_event))
        node_obj.tasks[f'{taskname} {args}'] = -1
        p.start()
    else:
        return taskname, args


class CfnNodeModel(BaseNodeModel):
    """
    The node behavior model for "FogHealth" computing node.
    边缘计算节点, 一方面连接到主控程序(GUI), 一方面根据指令执行compute task（例如从某个sensor node读取数据）。
    每个task对应一个进程, 当前的所有task都记录在self.compute_tasks字典中
    """

    def __init__(self, demo_config: DemoConfigParser, node_config: NodeConfig, msg_process_fn=process_GUI_msg,
                 task_cmd_handler=start_node_task) -> None:

        self.current_state = 'NodePowerOn'
        self.tasks = dict()  # 记录当前正在执行的task。格式：task_name: str, task_param
        self.task_cmd_q = task_cmd_q
        self.start_task = task_cmd_handler
        self.signal_emitter = SlaverSgnlEmitter(self)
        super().__init__(demo_config, node_config, msg_process_fn)

    def start(self):
        # 任务通信线程。由于每个任务都以子进程形式存在，所以通过下面这个线程来转发子进程的发的消息（在一个task_cmd_q队列里）给主GUI。
        Thread(name=f"{self.node_conf.node_name}_taskcmd",
               target=self._task_cmd_forward).start()

    def _task_cmd_forward(self):
        """
        功能：
        1. 如果task子进程发来的消息是('_PID', xxx), 表示这是刚启动的task，正注册自己的pid。记录在self.task字典里即可。
           将来主进程需要结束task时, 会查字典并在task_cancel这个共享值里写入其pid
        2. task进程所产生的其他所有消息，都会直接转发给主GUI.
        """
        while not self.terminateDemo:
            task_cmd = self.task_cmd_q.get()
            if task_cmd[0] == '_PID':
                task_key, pid = task_cmd[1]
                self.tasks[task_key] = pid
                self.print(f"updated self.tasks to {self.tasks}")
            elif task_cmd[0] == '_abort':  # 任务启动失败，例如源sensor没连上
                pid = task_cmd[1]
                self.send2gui(('warning', task_cmd[2]))
                self.cancel_task(pid)
            elif task_cmd[0] == '_terminateDemo':
                break
            else:
                self.send2gui(task_cmd)
        self.print('exiting _task_cmd_fwd().')

    def cancel_task(self, task: Union[int, str]):
        """
        与handel_task 对应，结束某个任务。
        参数task可以是self.task字典里的key, 也可以是pid值(self.task里的value)
        """
        to_del = None
        if type(task) == int:  # 这种情况是task自己要求取消(发 _abort 消息到task_cmd_q里),
            # task已经退出，这里删除self.tasks对应的item即可
            self.print(f"task subprocess abort actively, pid={task}")
            for k, v in self.tasks.items():
                if task == v:
                    to_del = k
                    break
            try:
                self.tasks.pop(to_del)
            except:
                pass
        else:
            if task not in self.tasks.keys():
                s = f'No such task. Current tasks: {list(self.tasks.keys())}'
                self.print(s)
                self.send2gui(('warning', s))
                return
            else:
                # 实现的方法是通过task_cancel这个进程间变量，把其值置为要cancel的task的pid
                self.print(f"尝试结束进程：{task}, pid={self.tasks[task]}, current tasks={self.tasks}")
                task_cancel.value = self.tasks[task]
                # 从记录的task字典中除这个task
                self.tasks.pop(task)
                self.print(f"after deletion: {self.tasks}")

    def close(self):
        print('closing.')
        try:
            self.conn_GUI.close()
            if self.ue_conn.is_alive():
                self.ue_conn.stop()
        except:
            pass
        self.task_cmd_q.put(('_terminateDemo', None))


class CfnDemoSlaverSignals(QObject):
    service_ctrl = pyqtSignal(str, str, str)  # node_id, current state
    service_state = pyqtSignal(str, dict)  # node_id, pulse rate


class SlaverSgnlEmitter:
    """
    这个class是demo_manager的Qt信号发射器。即, 根据节点发来的消息, 按需转换成发给GUI的signal。
    其核心内容, 就是一个signal_emit_logic()函数, 控制着GUI前端所需的信号触发逻辑。
    """

    def __init__(self, dm: 'CfnNodeModel') -> None:
        self.dm = dm
        self.QtSignals = CfnDemoSlaverSignals()

    def signal_emit_logic(self, service_name: str, action: str, params: str):
        """
        函数参数就是从节点发来的信息, 格式是个三元组: node_name, command, command_arg, 分别代表
        节点名(谁发来的命令)、命令关键字、命令参数。本函数负责判断这些信息, 并转换成某种具体的信号触发。

        当然可以不仅仅触发Qt信号, 还可以调用self.demo_manager的其他接口, 实现任何需要做的动作。
        """
        ret = ''
        print(f"signal_emit_logic >>> ... {service_name}, {action}, {params}")
        self.QtSignals.service_ctrl.emit(service_name, action, params)
        return ret
