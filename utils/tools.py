# -*- coding: utf-8 -*-
"""
@Time: 5/25/2024 8:33 PM
@Author: Honggang Yuan
@Email: honggang.yuan@nokia-sbell.com
Description: 
"""
import socket

import psutil


def check_port(port):
    # 创建socket对象
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # 尝试连接指定端口
        s.bind(("127.0.0.1", port))
        # 如果可以绑定成功，则端口未被占用
        print(f"Port {port} is available.")
    except OSError:
        # 如果绑定失败，则端口已被占用
        print(f"Port {port} is already in use.")
        # 获取占用该端口的进程信息
        for proc in psutil.process_iter():
            try:
                # 获取进程的监听端口
                proc_ports = proc.connections()
                for p in proc_ports:
                    if p.laddr.port == port:
                        print(f"Process {proc.pid} is using port {port}. Terminating...")
                        # 终止进程
                        proc.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
