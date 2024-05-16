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
        print(f"@@@@@@@@@@@@@ server_url is: {server_url}")
        # timeout = httpx.Timeout(100.0, connect=100.0)  # global time out for get()/post() is 3s. Connect timeout 15s.
        timeout = httpx.Timeout(100.0)  # global time out for get()/post() is 3s. Connect timeout 15s.
        self.client = httpx.Client(timeout=timeout)
        self._lock = Lock()  # to safely operate on self.client
        self._netif = kwargs.get('net_ifname', 'lo')
        self.retry_times = kwargs.get('retry_times', 300)
        autostart = kwargs.get('autostart', False)

        self.plugin, self.metrics = self._infer_metrics_from_url() if server_url else ('', [])
        self.q = result_q  # message queue
        self.period_s = get_period / 1000  # ms
        self.err_times = 0
        self.get_data_thread = repeatTimer(self.period_s, self._get_data, args=[], autostart=autostart)  # data collect
        self.close = self.stop  # add an alias for stop()
        self.restart = self.start  # add an alias for start()

    def set_server_url(self, url: str):
        self.url = url
        self.plugin, self.metrics = self._infer_metrics_from_url()

    def _infer_metrics_from_url(self):
        url_items = self.url.split('/')
        plugin = url_items[-2] if self.url[-1] == '/' else url_items[-1]
        if plugin == 'cpu':
            metrics = ['total']
        elif plugin == 'mem':
            metrics = ['percent']
        elif plugin == 'network':
            if self._netif == 'lo':
                print(f"WARNING: Monitoring 'lo' statistics ({self.url})")
            metrics = ['tx', 'rx']
        else:
            raise ValueError('GlancesHandler: unsupported API')
        return plugin, metrics  # network, ['tx', 'rx']

    def set_netifname(self, ifname: str):
        """ Change the network interface name in the url. Only valid if the metrics is network. """
        if self.plugin == 'network':
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
                # print(f"{'-' * 50}\n{self.url} responding {result}\n{'-' * 50}")
                self.err_times += 1
            else:
                r_dict = {}
                if self.plugin == 'network':
                    for item in result.json():
                        if item['interface_name'] == self._netif:
                            r_dict = item
                    if r_dict == {}:
                        r_dict.update({'tx': 0, 'rx': 0})
                        raise ValueError(f"network interface '{self._netif}' not found")
                else:
                    r_dict = result.json()
                for i in self.metrics:
                    if i != 'total':
                        r_dict[i] /= 1000
                if not self.q.full():
                    self.q.put([float(r_dict.get(item)) for item in self.metrics])  # 将收集到的数据放入队列 self.q 中  [0.0,0.0 ]

        except Exception as err:
            self.err_times += 1
            if (self.err_times % 4) == 1:
                print(f"{'-' * 50}\nERROR: glances handler {self.url} fails {self.err_times} times:\n{err}\n{'-' * 50}")

        if self.err_times == self.retry_times:
            print(f"Glances handler for {self.url} aborting. Check server status.")
            self.pause()

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
