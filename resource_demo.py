# -*- coding: utf-8 -*-
"""
@Time: 5/16/2024 11:08 AM
@Author: Honggang Yuan
@Email: honggang.yuan@nokia-sbell.com
Description: 
"""
from multiprocessing import Pipe
from queue import Queue

from utils.cfndemomanager import CfnDemoManager
from utils.configparser import DemoConfigParser

if __name__ == '__main__':
    configuration = DemoConfigParser("cfn_config.json")
    inter_process_resource_NodeMan = [(i['node_name'], Pipe()) for i in
                                      configuration.nodes]
    inter_process_resource_StatMon = [(i['monitoring_source_name'], Queue(15)) for i in
                                      configuration.monitoring_sources]  # for state_monitor_process. new Queue()
    process_manager = CfnDemoManager(configuration, inter_process_resource_NodeMan, inter_process_resource_StatMon)
