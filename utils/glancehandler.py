# -*- coding: utf-8 -*-
"""
@Time: 5/16/2024 10:50 AM
@Author: Honggang Yuan
@Email: honggang.yuan@nokia-sbell.com
Description: 
"""
from multiprocessing import Queue
from threading import Lock
import httpx
from time import sleep
import socket

import random

from utils.repeatimer import repeatTimer


class GlancesHandler(object):
    """ A wrapper of functions for interactions with Glances server.1
        When a Glances' server is running somewhere, this class can be instantiated to
        set up a threading based communication interface with the server. Running
            `GlancesHandler.start()`
        will periodically send requests to server and store the returned results into
        a cross-process queue.

        start()/restart()/resume() are identical. Can be called multiple times. But stop()
        can only be called once, after which the thread is dropped. Use pause() to stop the
        repeatTimer temporarily.

        **NOTE**: self.client is not thread-safe, so when you add methods using it or try
        to operate with it directly, always remember to use self._lock.
    """

    def __init__(self, result_q: Queue, server_url: str = '', get_period: int = 400, **kwargs):
        """
        Parameters:
        server_url : the Glances REST API url. E.g. 'http://localhost:61208/api/3/mem'
        result_q: cross-process queue to store results.
        get_period: time interval between GET requests (ms).
        kwargs:
        net_ifname: when requesting network statistics, use this keyword argument to specify an interface.
                    If not given, the default will be 'lo', and a warning message is printed on screen.
                    One can change this setting with ResourceHandler.set_netifname() later.
        autostart: if True, the get_data_thread is started immediately. Or you need to call start() manually.
        """
        self.url = server_url  # E.g. 'http://localhost:61208/api/3/net'
        # print(f"@@@@@@@@@@@@@ server_url is: {server_url}")
        timeout = httpx.Timeout(100.0)  # global time out for get()/post() is 3s. Connect timeout 15s.
        self.client = httpx.Client(timeout=timeout)

        self._lock = Lock()  # to safely operate on self.client

        self.plugin = kwargs.get('key_word', '')
        self._disk_id = kwargs.get('disk_id', '')
        autostart = kwargs.get('autostart', False)
        self._netif = kwargs.get('net_ifname', 'lo')
        self.retry_times = kwargs.get('retry_times', 300)

        self.metrics = self._infer_metrics_from_url() if server_url else ('', [])

        self.q = result_q  # message queue
        self.period_s = get_period
        self.err_times = 0
        print(f"perid_s：{self.period_s}")
        self.get_data_thread = repeatTimer(self.period_s, self._get_data, args=[], autostart=autostart)  # data collect
        self.close = self.stop  # add an alias for stop()
        self.restart = self.start  # add an alias for start()

    def set_server_url(self, url: str):
        self.url = url
        self.plugin, self.metrics = self._infer_metrics_from_url()

    def _infer_metrics_from_url(self):
        if self.plugin == 'cpu':
            metrics = ['total']
        elif self.plugin == 'memory':
            metrics = ['percent']
        elif self.plugin == 'net':
            if self._netif == 'lo':
                print(f"WARNING: Monitoring 'lo' statistics ({self.url})")
            metrics = ['tx', 'rx']
        elif self.plugin == 'disk':
            metrics = ['read_bytes', 'write_bytes']
        else:
            raise ValueError('GlancesHandler: unsupported API')
        return metrics  # network, ['tx', 'rx']

    def _get_data(self):
        result = None
        try:
            temp_err = None
            self._lock.acquire()
            try:
                result = self.client.get(self.url)  # 从这里开始得到通过请求 url:http://localhost:61208/api/3/cpu 获取到的数据
            except Exception as err:
                temp_err = err
            finally:
                self._lock.release()
            if temp_err:
                raise temp_err
            if result.status_code != 200:
                print(f"{'-' * 50}\n{self.url} responding {result}\n{'-' * 50}")
                self.err_times += 1
            else:
                r_dict = {}
                cpu_result = {"total": 11}
                mem_result = {"percent": 87.5}
                net_result = {
                    "Ethernet": [
                        {
                            "interface_name": "Ethernet",
                            "alias": None,
                            "time_since_update": 48.253194093704224,
                            "cumulative_rx": 0,
                            "rx": 0,
                            "cumulative_tx": 0,
                            "tx": 0,
                            "cumulative_cx": 0,
                            "cx": 0,
                            "is_up": True,
                            "speed": 1048576000,
                            "key": "interface_name"
                        }
                    ]
                }
                disk_result = {
                    "PhysicalDrive0": [
                        {
                            "time_since_update": 11.724727153778076,
                            "disk_name": "PhysicalDrive0",
                            "read_count": 893,
                            "write_count": 391,
                            "read_bytes": 39071744,
                            "write_bytes": 3153920,
                            "key": "disk_name"
                        }
                    ]
                }
                if self.plugin in ['cpu', 'memory']:
                    r_dict[self.metrics[0]] = result.json()[self.metrics[0]]

                elif self.plugin == 'net':
                    net_result = result.json()[self._netif][0]
                    for metric in self.metrics:
                        r_dict[metric] = 0
                        r_dict[metric] = net_result[metric]
                elif self.plugin == 'disk':
                    disk_result = result.json()[self._disk_id][0]
                    for metric in self.metrics:
                        r_dict[metric] = [0]
                        r_dict[metric] = disk_result[metric]
                try:
                    if not self.q.full():
                        # print(f"GlancesHandler -> r_dict: {r_dict}")
                        if self.plugin in ['cpu']:
                            random_number = random.randint(3, 5)
                            # print(f"存入队列的值{[float(r_dict.get(item)) for item in self.metrics]}")
                            for i in range(random_number):
                                self.q.put([float(r_dict.get(item)) for item in self.metrics])  # 将收集到的数据放入队列 self.q 中  [0.0, 0.0]
                        else:
                            self.q.put([float(r_dict.get(item)) for item in self.metrics])
                            self.q.put([float(r_dict.get(item)) for item in self.metrics])
                            self.q.put([float(r_dict.get(item)) for item in self.metrics])
                except Exception as exp:
                    print(f"GlancesHandler Put data into Queue ERROR!!! >>> {exp}")
        except Exception as err:
            self.err_times += 1
            if (self.err_times % 4) == 1:
                print(f"{'-' * 50}\nERROR: glances handler {self.url} fails {self.err_times} times:\n{err}\n{'-' * 50}")
        if self.err_times == self.retry_times:
            print(f"Glances handler for {self.url} aborting. Check server status.")
            # self.pause()

    def set_netifname(self, ifname: str):
        """ Change the network interface name in the url. Only valid if the metrics is network. """
        if self.plugin == 'net':
            self._netif = ifname
            print(f"INFO: Changed Glances handler for {self.url} to monitor netif: '{self._netif}'")
        else:
            print(f"WARNING: set_netifname not applicable to plugin '{self.plugin}'")

    def list_netifname(self) -> list:
        ret = []
        if self.plugin == 'network':
            try:
                temp_err = None
                self._lock.acquire()
                try:
                    r = self.client.get(self.url)
                except Exception as err:
                    temp_err = err
                finally:
                    self._lock.release()
                if temp_err:
                    raise temp_err
                if r.status_code != 200:
                    raise ValueError(f"{'-' * 50}\n{self.url} responding {r}\n{'-' * 50}")
                for item in r.json():
                    ret.append(item['interface_name'])
            except Exception as err:
                print(f"{'-' * 50}\nERROR: glances handler {self.url}\n{err}\n{'-' * 50}")
            finally:
                return ret
        else:
            print(f"WARNING: list_netifname not applicable to plugin '{self.plugin}'")
            return ret

    def start(self):
        if self.url == '' or self.metrics == []:
            print(f"{'-' * 50}\nIGNORE: GlancesHandler: No valid url or metrics set yet!\n{'-' * 50}")
            return
        self.get_data_thread.start()  # thread of collect data about running server
        print(f'GlancesHandler for {self.url} started.')

    def pause(self):
        self.get_data_thread.pause()
        self.err_times = 0

    def stop(self):
        self.get_data_thread.stop()
        self.get_data_thread.join()
        sleep(0.2)
        self.client.close()
        while not self.q.empty():
            self.q.get()
        print(f"GlancesHandler for {self.url} stops.")


if __name__ == '__main__':
    q = Queue()
    gh = GlancesHandler(result_q=q, get_period=800, server_url='http://localhost:61208/api/3/network',
                        autostart=True)

    sleep(1)


    def print_result(n):
        for i in range(n):
            result = []
            print(n - i, ':')
            while not q.empty():
                result.append(q.get())
            print(result)
            sleep(1)


    print_result(5)
    print('paused')
    print_result(5)

    print('get netifname list:')
    print(gh.list_netifname())
    sleep(2)

    gh.set_netifname('enp0s25')
    gh.start()
    print_result(5)
    gh.stop()
