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

import vlc


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
