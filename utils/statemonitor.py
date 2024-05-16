# -*- coding: utf-8 -*-
"""
@Time: 5/16/2024 10:50 AM
@Author: Honggang Yuan
@Email: honggang.yuan@nokia-sbell.com
Description: 
"""
from multiprocessing import Process, Queue
from threading import Thread

from utils.configparser import DemoConfigParser
from utils.glancehandler import GlancesHandler


class StateMonitor(object):
    """
    This class provides a subprocess that handles KPI monitoring from various sources.
    """

    def __init__(self, resources: dict, demo_config: DemoConfigParser) -> None:
        self.demo_config = demo_config
        self.resources = resources
        self.monitors_to_connect = list(resources.keys())  # 列出要监控的对象（worker节点）
        self.queues = list(resources.values())  # worker节点对应的值, init size:15
        self.proc = Process(target=self._mainfunc,
                            args=(self.monitors_to_connect, self.queues),
                            name='state_monitor')
        self._cmd = Queue(1)
        self._threads = []

    def _read_cmd(self, cmd_q, threads):
        while True:
            cmd, arg = cmd_q.get()
            if cmd == 'stop':
                for t in threads:
                    print(f'status_monitor stopping thread {t}.')
                    t.stop()
                break
            elif cmd == 'sim':  # 仿真行为控制。这种命令的argument格式是: (monitor_id:int, monitor_action:str) (up or down or the others)
                (monitor_id, monitor_action) = arg
                if self.demo_config.get_monitoring_source(monitor_id)['data_API']['backend_tool'] != 'Simulation':
                    print(f"StateMonitor - WARNING - trying to send `sim` command to non-simulated monitor (id {monitor_id}). Ignoring.")
                else:
                    print(f"StateMonitor send command `{monitor_action}` to simulated monitoring source {self.monitors_to_connect[monitor_id]}")
                    self._threads[monitor_id].execute(monitor_action)  # 这里的monitor_action，是配置文件里相应simulation字段支持的str
            else:
                print(f"(StateMonitor) - DEBUG: unknown command {cmd, arg}")

    def _mainfunc(self, monitors: list, queues: list):
        for mi, monitor in enumerate(monitors):
            bknd_tool = self.demo_config.get_monitoring_source(monitor)['data_API']["backend_tool"]
            if bknd_tool == 'Glances':  # decided by config file, 'backend_tool' character
                k = self.demo_config.get_monitoring_keyword(monitor)
                if k == 'cpu':
                    # uri = http://localhost:61208/api/3/cpu
                    print("GlancesHandler CPU Data")
                    t = GlancesHandler(result_q=queues[mi],
                                       get_period=self.demo_config.get_monitoring_source(monitor)['data_API']['refresh_interval'],
                                       server_url=self.demo_config.get_monitoring_url(monitor))

                elif k == 'memory':
                    # uri = http://localhost:61208/api/3/mem/percent
                    print("GlancesHandler memory Data")
                    t = GlancesHandler(result_q=queues[mi],
                                       get_period=self.demo_config.get_monitoring_source(monitor)['data_API']['refresh_interval'],
                                       server_url=self.demo_config.get_monitoring_url(monitor))
                elif k == 'net':
                    # uri = http://localhost:61208/api/3/network/interface_name/
                    print("GlancesHandler network Data")
                    t = GlancesHandler(result_q=queues[mi],
                                       get_period=self.demo_config.get_monitoring_source(monitor)['data_API']['refresh_interval'],
                                       server_url=self.demo_config.get_monitoring_url(monitor),
                                       net_ifname=self.demo_config.get_monitoring_source(monitor)['data_API']['net_interface'])
                    print(f"{monitor}: {t.list_netifname()}")

                elif k == 'disk':
                    print("GlancesHandler Disk Data")
                    t = GlancesHandler(result_q=queues[mi],
                                       get_period=self.demo_config.get_monitoring_source(monitor)['data_API']['refresh_interval'],
                                       server_url=self.demo_config.get_monitoring_url(monitor),
                                       disk_id=self.demo_config.get_monitoring_source(monitor)['data_API']['net_interface'])
                    print(f"{monitor}: {t.list_netifname()}")
                else:
                    t = None
                    print(f"DEBUG: key {k} not supported.")
            else:
                raise ValueError(f"Monitoring interface type {bknd_tool} Not implemented yet!")
            self._threads.append(t)  # 按照id顺序, 每个monitor线程都加入这个list
            t.start()

        cmd_thread = Thread(target=self._read_cmd, args=(self._cmd, self._threads))
        cmd_thread.start()
        cmd_thread.join()
        print("Exiting state_monitor process.")

    def execute_cmd(self, cmd: str, arg=None):
        """
        一个控制接口（2022.03-目前cmd只能是sim, 如有需要，可在_read_cmd()里扩展之）。
        """
        self._cmd.put((cmd, arg))

    def start(self):
        self.proc.start()

    def stop(self):
        """ same as close()."""
        self.close()

    def close(self):
        """ same as stop()."""
        self.execute_cmd('stop')
