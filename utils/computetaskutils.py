# -*- coding: utf-8 -*-
"""
@Time: 5/23/2024 2:10 PM
@Author: Honggang Yuan
@Email: honggang.yuan@nokia-sbell.com
Description: 
"""
import os
import subprocess
import sys
from multiprocessing import Event, SimpleQueue, Value
from pathlib import Path
from time import sleep

import httpx
import numpy as np
import requests
import yaml
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QWidget, QMainWindow, QApplication, QGroupBox, QHBoxLayout

from util.computeResHandler import get_custom_resource

import vlc

from util.matrix import bk_computing
from util.sdn import SDNController


class VideoPlayerWindow(QMainWindow):
    def __init__(self, path=None, miface=None):
        super().__init__()
        self.setWindowTitle("Video Player")
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        self.vlc_instance = vlc.Instance("--no-xlib")  # "--no-xlib" is required for running on Linux without X11
        self.media_player = self.vlc_instance.media_player_new()
        self.media_player.set_fullscreen(False)

        self.media = self.vlc_instance.media_new(path, miface)
        self.media_player.set_media(self.media)

        self.vlc_frame = QFrame(self)
        self.layout.addWidget(self.vlc_frame)

        if sys.platform.startswith("linux"):  # for Linux using the X Server
            self.media_player.set_xwindow(self.vlc_frame.winId())
        elif sys.platform == "win32":  # for Windows
            self.media_player.set_hwnd(self.vlc_frame.winId())
        elif sys.platform == "darwin":  # for macOS
            self.media_player.set_nsobject(self.vlc_frame.winId())


def vlc_receiver(video_uri: str, eth: str, cmd_q: SimpleQueue,
                 cancel_task_id: Value, terminate_event: Event) -> float:
    pid = os.getpid()
    cmd_q.put(("_PID", ('mvlc ' + video_uri + '#' + eth, pid)))
    interface = "miface=" + eth
    app = QApplication(sys.argv)
    playWindow = VideoPlayerWindow(path=video_uri, miface=interface)
    playWindow.media_player.play()
    playWindow.resize(800, 600)
    playWindow.show()
    sleep(2)
    while not terminate_event.is_set():
        try:
            if cancel_task_id.value == pid:
                print(f"(PID-{pid}) Received task_cancel signal!")
                cancel_task_id.value = 0
                playWindow.media_player.stop()
                playWindow.close()
                sleep(1)
                cmd_q.put(('vlc_receiver', 'stop'))
                sys.exit(app.exec_())
                break
            else:
                continue
        except Exception as err:  # 运行中出现连接断开之类错误
            s = f"Error encountered with vlc_receiver: {err}. Aborting task."
            print(f'(PID-{pid})' + s)
            cmd_q.put(('_abort', pid, s))
            return


def cfn_bk_service(task_name, pig_args: str, cmd_q: SimpleQueue,
                   cancel_task_id: Value, terminate_event: Event) -> float:
    pid = os.getpid()
    cmd_q.put(("_PID", (f'{task_name} {pig_args}', pid)))
    while not terminate_event.is_set():
        try:
            if cancel_task_id.value == pid:
                print(f"(PID-{pid}) Received task_cancel signal!")
                cancel_task_id.value = 0
                cmd_q.put(('cfn_bk_service', 'stop'))
                break
            else:
                X = np.random.randn(70, 70)
                Y = np.random.randn(70, 70)
                Z = X.dot(Y)
        except Exception as err:  # 运行中出现连接断开之类错误
            s = f"Error encountered with vlc_receiver: {err}. Aborting task."
            print(f'(PID-{pid})' + s)
            cmd_q.put(('_abort', pid, s))
            return


def vlc_streamer(addr: str, port: int, file_path: str, start_pos: float):
    ad = "sout=#duplicate{dst=udp{mux=ts,dst=" + addr + ":" + str(port) + "},dst=display}"
    params = [ad, "sout-all", "sout-keep"]
    inst = vlc.Instance()
    media = inst.media_new(f'{file_path}', *params)
    media_player = media.player_new_from_media()
    media_player.play()
    media_player.set_position(float(start_pos))  # 从所设定的位置开始播放
    sleep(2)


# 二次开发python-vlc包实现音视频的网络串流
def vlc_sender(addr: str, port: int, file_path: str, start_pos: float, cmd_q: SimpleQueue,
               cancel_task_id: Value, terminate_event: Event) -> float:
    pid = os.getpid()
    cmd_q.put(("_PID", ('vlc', pid)))

    ad = "sout=#duplicate{dst=udp{mux=ts,dst=" + addr + ":" + str(port) + "},dst=display}"
    params = [ad, "sout-all", "sout-keep"]
    inst = vlc.Instance()
    media = inst.media_new(f'{file_path}', *params)
    media_player = media.player_new_from_media()
    print("------vlc_s start_pos:" + str(start_pos))
    media_player.play()
    media_player.set_position(float(start_pos))  # 从所设定的位置开始播放
    sleep(2)

    while not terminate_event.is_set():
        try:
            if cancel_task_id.value == pid:
                print(f"(PID-{pid}) Received task_cancel signal!")
                cancel_task_id.value = 0
                pos_stream = media_player.get_position()  # 获取当前播放位置
                media_player.stop()
                sleep(0.1)
                cmd_q.put(('vlc', str(pos_stream)))
                cmd_q.put(('state', str(pos_stream)))
                print("------当前播放位置::Pos_streaming:" + str(pos_stream))
                break
            elif media_player.is_playing() == 0:
                print("media_player.is_no_playing")
                # print("media_player continue keep playing")
                # media_player.play()
                sleep(0.2)
                break
            else:
                continue
        except Exception as err:  # 运行中出现连接断开之类错误
            s = f"Error encountered with vlc_sender: {err}. Aborting task."
            print(f'(PID-{pid})' + s)
            cmd_q.put(('_abort', pid, s))
            return


def get_resource_from_kube(crd_group, crd_version, crd_plural, custom_resource_name,
                           compute_config_file, net_config_file):
    resource = {'compute': {}, 'network': []}
    while True:
        compute_resource = get_custom_resource(crd_group, crd_version, crd_plural, custom_resource_name,
                                               compute_config_file)
        ocp_resource = get_custom_resource(crd_group, crd_version, crd_plural, custom_resource_name, net_config_file)
        if compute_resource is not None and ocp_resource is not None:
            for c_res in compute_resource['status']['nodes']:
                if c_res['nodeName'] == 'worker1':
                    resource['compute']['worker1'] = c_res
                elif c_res['nodeName'] == 'worker2':
                    resource['compute']['worker2'] = c_res
            resource['compute']['ocp'] = ocp_resource['status']['nodes'][0]
            resource['network'] = ocp_resource['status']['ueRTT']

        else:
            continue
        if resource['compute'] and resource['compute']:
            return resource
        else:
            continue


def cfnResHandler(cmd_q: SimpleQueue, cancel_task_id: Value, terminate_event: Event) -> float:
    pid = os.getpid()
    cmd_q.put(("_PID", ('cfnres report', pid)))
    crd_group = "cfn.nokia.com"
    crd_version = "v1alpha1"  # Replace with your CRD version
    crd_plural = "edgecfns"  # Replace with your CRD plural form
    custom_resource_name = "default"  # Replace with the desired custom resource name
    compute_config_file = os.environ.get('KUBECONFIG', '~/.kube/config')
    net_config_file = os.environ.get('KUBECONFIG', '~/.kube/config_ocp')
    # result = get_resource_from_kube(crd_group, crd_version, crd_plural, custom_resource_name,
    #                                 compute_config_file, net_config_file)
    while not terminate_event.is_set():
        try:
            if cancel_task_id.value == pid:
                cancel_task_id.value = 0
                break
            else:
                # result = get_resource_from_kube(crd_group, crd_version, crd_plural, custom_resource_name,
                #                                 compute_config_file, net_config_file)
                result = glances_handler(crd_group, crd_version, crd_plural, custom_resource_name,
                                         compute_config_file, net_config_file)
                cmd_q.put(('cfnret', result))  # 将获取到的资源送到 Gui_Controller 并显示出来
                sleep(4)
                continue
        except Exception as err:
            s = f"Error encountered with cfnResHandler: {err}. Aborting task."
            print(f'(PID-{pid})' + s)
            cmd_q.put(('_abort', pid, s))
            return


def onos_handler(pid_args):
    post_tag = False
    params = pid_args.split("#")
    outPorts = ['6', '8', '10']
    multicast_ip, in_port, cur_out_port, tar_out_port, flow_priority = \
        str(params[0]), str(params[1]), str(params[2]), str(params[3]), int(params[4])

    multicast_ip += '/24'
    cur_src_ip = "192.168.68.0/24"  # Stream Server sender IP

    sdn_ctrl = SDNController(username='onos', password='rocks', controller_IP='192.168.1.38')
    cur_device = sdn_ctrl.getAllDevices()[0]
    cur_device_id = cur_device['id']

    post_tag = sdn_ctrl.postDeviceFlows(
        priority=flow_priority, device_id=cur_device_id, tar_addr=multicast_ip, src_addr=cur_src_ip,
        source_port=in_port, target_port=tar_out_port)
    print(f">> ... onos_handler post flow inport is: {in_port} , outport is: {tar_out_port}")

    if (cur_out_port in outPorts) and (cur_out_port != tar_out_port):  # avoid delete the same flow rules
        print(f">> ... onos_handler delete outport from {cur_out_port} , to {tar_out_port}")
        del_flow_id = sdn_ctrl.getFlowIDByIPAndPort(
            device_id=cur_device_id, src_port=in_port, tar_port=cur_out_port, addr=cur_src_ip[:-3])

        if del_flow_id:
            sdn_ctrl.deleteDeviceFlows(device_id=cur_device_id, flow_id=del_flow_id)
    print(f"<< ... onos_handler delete outport from {cur_out_port} , to {tar_out_port}")
    return post_tag


# scenario-3
# 1. delete all flows
# 2.
def onos_del_all_flow(pid_args):
    del_tag = False
    params = pid_args.split("#")
    m1_ip, m2_ip, m3_ip = str(params[0]), str(params[1]), str(params[2])
    sdn_ctrl = SDNController(username='onos', password='rocks', controller_IP='192.168.1.38')
    cur_device = sdn_ctrl.getAllDevices()[0]
    cur_device_id = cur_device['id']
    m1_ip_flowId = sdn_ctrl.getFlowIDByMulticastIP(device_id=cur_device_id, multicast_ip=m1_ip)
    m2_ip_flowId = sdn_ctrl.getFlowIDByMulticastIP(device_id=cur_device_id, multicast_ip=m2_ip)
    m3_ip_flowId = sdn_ctrl.getFlowIDByMulticastIP(device_id=cur_device_id, multicast_ip=m3_ip)
    print(f"\nm1_ip_flowId is:{m1_ip_flowId}"
          f"m2_ip_flowId is:{m2_ip_flowId}"
          f"m3_ip_flowId is:{m3_ip_flowId}\n")
    if m1_ip_flowId:
        del_tag = sdn_ctrl.deleteDeviceFlows(device_id=cur_device_id, flow_id=m1_ip_flowId)
    if m2_ip_flowId:
        del_tag = sdn_ctrl.deleteDeviceFlows(device_id=cur_device_id, flow_id=m2_ip_flowId)
    if m3_ip_flowId:
        del_tag = sdn_ctrl.deleteDeviceFlows(device_id=cur_device_id, flow_id=m3_ip_flowId)

    return del_tag


def onos_post_all_flow(pid_args):
    inPort = '12'
    outPorts = ['6', '8', '10']
    onos_del_all_flow(pid_args)
    params = pid_args.split("#")
    source_ip = '192.168.68.0/24'
    m1_ip, m2_ip, m3_ip, m4_ip = \
        str(params[0]) + '/24', str(params[1]) + '/24', str(params[2]) + '/24', str(params[3]) + '/24'
    multicast_ip = [m1_ip, m2_ip, m3_ip, m4_ip]

    sdn_ctrl = SDNController(username='onos', password='rocks', controller_IP='192.168.1.38')
    cur_device = sdn_ctrl.getAllDevices()[0]
    cur_device_id = cur_device['id']

    for m_ip in multicast_ip:
        sdn_ctrl.deleteAllMulticastIPFlows(device_id=cur_device_id, multicast_IP=m_ip[:-3])

    pos_tag = sdn_ctrl.postDeviceMultiFlows(priority=30000, device_id=cur_device_id, tar_addr=m1_ip, src_addr=source_ip)
    pos_tag = sdn_ctrl.postDeviceMultiFlows(priority=30000, device_id=cur_device_id, tar_addr=m2_ip, src_addr=source_ip)
    pos_tag = sdn_ctrl.postDeviceMultiFlows(priority=30000, device_id=cur_device_id, tar_addr=m3_ip, src_addr=source_ip)
    pos_tag = sdn_ctrl.postDeviceMultiFlows(priority=30000, device_id=cur_device_id, tar_addr=m4_ip, src_addr=source_ip)
    return pos_tag


def kubernetes_pod_handler(task_name, pid_args, cmd_q: SimpleQueue,
                           cancel_task_id: Value, terminate_event: Event) -> float:
    node_names = {'master': 'node1', 'worker1': 'node2', 'worker2': 'node3'}
    pid = os.getpid()
    cmd_q.put(("_PID", (f'{task_name} {pid_args}', pid)))
    args = pid_args.split("#")
    service_name, node = args[0], args[1]
    with open(f'{Path.cwd()}/front_page/utils/service_pod.yaml', "r") as file:
        data = yaml.safe_load(file)

    data['metadata']['labels']['app'] = f'{service_name}-{node_names[node]}'
    data['metadata']['name'] = f'{service_name}-{node_names[node]}'
    data['spec']['nodeSelector']['node_name'] = node
    if node == 'master':
        data['spec']['nodeSelector']['node_name'] = 'worker1'
    data['spec']['containers'][0]['name'] = service_name
    pod_name = f'{service_name}-{node_names[node]}'

    with open(f'{Path.cwd()}/front_page/utils/service_pod.yaml', "w") as file:
        yaml.dump(data, file)

    create_cmd = f"kubectl create -f {Path.cwd()}/front_page/utils/service_pod.yaml"
    del_cmd = f"kubectl delete pods {pod_name} --force"
    _stdout = sys.stdout
    _stderr = sys.stderr
    _stdout = subprocess.DEVNULL
    _stderr = subprocess.DEVNULL
    subprocess.run(create_cmd, shell=True, stdout=_stdout, stderr=_stderr)
    sleep(1)

    while not terminate_event.is_set():
        try:
            if cancel_task_id.value == pid:
                # print(f"\n(PID-{pid})-- kubernetes_pod_handler Received task_cancel signal!\n")
                cancel_task_id.value = 0
                subprocess.run(del_cmd, shell=True, stdout=_stdout, stderr=_stderr)
                sleep(3)
                break
        except Exception as err:  # 运行中出现连接断开之类错误
            s = f"Error encountered with Kubernetes: {err}. Aborting task."
            print(f'(PID-{pid})' + s)
            cmd_q.put(('_abort', pid, s))
            return


def glances_handler(crd_group, crd_version, crd_plural, custom_resource_name,
                    compute_config_file, net_config_file):
    nodes = ['ocp', 'worker1', 'worker2']
    cpu_res = {
        'ocp': "http://10.70.30.163:61208/api/3/cpu",
        'worker1': "http://192.168.67.64:61208/api/3/cpu",
        'worker2': "http://192.168.67.65:61208/api/3/cpu"
    }
    mem_res = {
        'ocp': "http://10.70.30.163:61208/api/3/mem",
        'worker1': "http://192.168.67.64:61208/api/3/mem",
        'worker2': "http://192.168.67.65:61208/api/3/mem"
    }
    ret_resource = get_resource_from_kube(crd_group, crd_version, crd_plural, custom_resource_name,
                                          compute_config_file, net_config_file)
    for node in nodes:
        cpu_response = requests.get(cpu_res[node])
        mem_response = requests.get(mem_res[node])
        if cpu_response.status_code == 200 and mem_response.status_code == 200:
            ret_resource['compute'][node]['cpu'] = cpuResFromJson(node, cpu_response.json())
            ret_resource['compute'][node]['memory'] = memResFromJson(mem_response.json())
    return ret_resource


def cpuResFromJson(node, cpu_json):
    if node == 'ocp':
        res = {'architecture': 'amd64', 'available': str(cpu_json['idle'] - 20), 'total': '100'}
    else:
        res = {'architecture': 'amd64', 'available': str(cpu_json['idle']), 'total': '100'}
    return res


def memResFromJson(mem_json):
    res = {'available': f"{mem_json['available']}Ki", 'total': f"{mem_json['total']}Ki"}
    return res

