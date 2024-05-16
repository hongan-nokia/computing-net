# -*- coding: utf-8 -*-
"""
@Time: 5/16/2024 10:50 AM
@Author: Honggang Yuan
@Email: honggang.yuan@nokia-sbell.com
Description: 
"""

from typing import Union
import json


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

    def add_attr(self, name: str, val: any):
        self.__dict__[name] = val


class DemoConfigParseError(ValueError):
    pass


class NodeConfig(AttrDict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.add_attr('node_ip', self.node_ip)
        except:
            pass
        try:
            self.add_attr('port', int(self.node_port))
        except:
            pass
        try:
            self.add_attr('conn_type', self.conn_type)
        except:
            pass
        try:
            self.add_attr('node_name', self.node_name)
        except:
            pass


def _config_dict_checker(config_dict: dict):
    """
    检查配置文件内容。
    """
    # 1. node_name 不能重复
    node_names = list(map(lambda x: x['node_name'], config_dict['nodes']))
    if not (len(set(node_names)) == len(node_names)):
        raise DemoConfigParseError("node_name duplication in configuration file.")
    # 3. node_id 从0递增
    for i, n in enumerate(config_dict['nodes']):
        if n['node_id'] != i:
            raise DemoConfigParseError("node_id must increase 1 by 1 starting from 0.")
    for i, m in enumerate(config_dict['monitoring_source']):
        if m['monitoring_source_id'] != i:
            raise DemoConfigParseError("monitoring_source_id must increase 1 by 1 starting from 0.")


class DemoConfigParser:
    """
    Parse the configuration file and provide convenient methods to access the parameters.
    """

    def __init__(self, config: Union[dict, str]):
        """
        `config` may be a dictionary, or a string specifying the path of a json file.
        """
        if type(config) == dict:
            self._config_dict = AttrDict(config)
        elif type(config) == str:
            with open(config, encoding='utf-8') as fp:
                self._config_dict = AttrDict(json.load(fp))
        else:
            raise ValueError("Unrecognized `config` type (should be dict or str).")
        _config_dict_checker(self._config_dict)

        self.n_nodes = len(self._config_dict['nodes'])
        self.n_monitors = len(self._config_dict['monitoring_source'])
        self.nodes = self._config_dict['nodes']

        self.node_names = [i['node_name'] for i in self.nodes]
        self.monitoring_sources = self._config_dict['monitoring_source']  # 1st level title
        self.monitoring_names = [i['monitoring_source_name'] for i in
                                 self.monitoring_sources]  # monitored machine name_metrics
        self.gui_controller_host_ip = self._config_dict['gui_controller']['host_ip']
        self.gui_controller_host_port = int(self._config_dict['gui_controller']['host_port'])

    def __repr__(self) -> str:
        return f'Demo Configuration: GUI@{self.gui_controller_host_ip, self.gui_controller_host_port}, nodes=[{self.node_names}]'

    def get_config_dict(self) -> dict:
        return self._config_dict

    def get_node_interface_type(self, n) -> str:
        n_idx = self.node_names.index(n)
        return self.nodes[n_idx]['conn_type']

    def get_node(self, n: Union[str, int]) -> NodeConfig:
        """
        Return the node's parameters as a dict.
        """
        if type(n) == str:
            n = self.node_names.index(n)
        # print(f"self.nodes[n] is: {self.nodes[n]}")
        return NodeConfig(self.nodes[n])

    def get_monitoring_source(self, m: Union[int, str]) -> dict:
        if type(m) == str:
            m = self.monitoring_names.index(m)
        return self.monitoring_sources[m]

    def _get_monitor_API_id_or_name(self, monitor: Union[int, str, dict]) -> dict:
        if type(monitor) == str:
            if m := self.get_monitoring_source(monitor):
                return m['data_API']
            else:
                raise ValueError(f"Monitor name {monitor} not found!")
        elif type(monitor) == dict:
            return monitor['data_API']
        else:
            raise ValueError("argument type error.")

    def get_monitoring_keyword(self, monitor: Union[int, str, dict]) -> str:
        """
        Return the 'keyword' parameter of the specified monitoring source.
        Argument `monitor` can be an integer (id), a str (name) or a dict.
        """
        return self._get_monitor_API_id_or_name(monitor)['keyword']

    def get_monitoring_url(self, monitor: Union[int, str, dict]) -> str:
        """
        Return the 'url' parameter of the specified monitoring source.
        Argument `monitor` can be an integer (id), a str (name) or a dict.
        """
        return self._get_monitor_API_id_or_name(monitor)['url']

    def get_monitor_sim_conf(self, m: Union[int, str, dict]) -> dict:
        if not type(m) == dict:
            m = self.get_monitoring_source(m)
        return m['simulation']
