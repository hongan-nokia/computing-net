# -*- coding: utf-8 -*-
"""
@Time: 5/23/2024 2:10 PM
@Author: Honggang Yuan
@Email: honggang.yuan@nokia-sbell.com
Description: 
"""
import os
from multiprocessing.connection import Client
from os import path, getpid
import subprocess
import sys
from copy import deepcopy
from multiprocessing import Event, SimpleQueue, Value
from multiprocessing.managers import BaseManager
from pathlib import Path
from time import sleep
import cv2 as cv
import httpx
import numpy as np
import requests
import yaml
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QWidget, QMainWindow, QApplication, QGroupBox, QHBoxLayout
from PyCameraList.camera_device import test_list_cameras, list_video_devices, list_audio_devices

from utils.StreamPlayer import StreamerPlayer

os.environ['PYTHON_VLC_MODULE_PATH'] = "./vlc"
import vlc
from typing import Tuple

FRAME_W = 640
FRAME_H = 480
# define the frame area that is used by the extract_heart_rate algorithm
# i.e. facearea = frame[cut_y0:cut_y1, cut_x0:cut_x1,:]
cut_x0, cut_y0 = (170, 80)
cut_x1, cut_y1 = (470, 430)
eye_top = 190
eye_bottom = 270
face_area_w = cut_x1 - cut_x0
face_area_h = cut_y1 - cut_y0
# heart rate filter range
HEART_LOW = 66
HEART_HIGH = 90

# load dnn model and weights
if not (os.path.exists('./algorithmDev/deploy.prototxt.txt') and path.exists(
        'algorithmDev/res10_300x300_ssd_iter_140000.caffemodel')):
    raise ValueError('DNN model files does not exist.')
else:
    DNNmodel = path.abspath('./algorithmDev/deploy.prototxt.txt')
    DNNwt = path.abspath('./algorithmDev/res10_300x300_ssd_iter_140000.caffemodel')
inputsize = (300, 300)
inputmean = (104.0, 177.0, 123.0)
FogFaceDetector = (DNNmodel, DNNwt, inputsize, inputmean)


# faceDetector class which will be used by the 'show' process
class faceDetector:
    """
        To use the detector:
            detections = faceDetector.detect(img)
        where detections is 4-dim array returned by cv2.net.forward()
    """

    def __init__(self, dnnModel, dnnWeight, inputsize, inputmean):
        self.net = cv.dnn.readNetFromCaffe(dnnModel, dnnWeight)
        self.w, self.h = inputsize
        self.inputmean = inputmean

    def detect(self, img):
        """
        Parameters
        ----------
        img : numpy array, shape = (nrow, ncol, 3), color format is BGR

        Returns
        -------
        detections : 4-dimension array

        """
        blob = cv.dnn.blobFromImage(cv.resize(img, (self.w, self.h)), 1.0,
                                    (self.w, self.h), self.inputmean)  # 4-dim array (N,C,W,H) of the blobed image
        self.net.setInput(blob)
        detections = self.net.forward()
        return detections


def find_freq_method2(allFrames, nchannel, fps):
    # FFT conversion into frequency
    (eye_start, eye_stop) = tuple(map(lambda y: int((y / FRAME_H) * allFrames[0].shape[0]), [eye_top, eye_bottom]))
    frames_exclude_eye = np.concatenate((allFrames[:, :eye_start, ...], allFrames[:, eye_stop:, ...]), axis=1)
    F_vid = np.fft.rfft(frames_exclude_eye, axis=0)  # note that scipy's rfft return format is
    # different with numpy's rfft
    if nchannel == 1:
        F_vid = np.expand_dims(F_vid, -1)

    # extract frequency power between 0.8 to 2 Hz
    # idx_start, idx_stop = tuple(map(lambda f:1+int(f/(fps/2) * int(nframe/2)) * 2, [0.8, 2])) #for scipy.fftpack.rfft
    # idx_start, idx_stop = tuple(map(lambda f: int((f/(fps/2))*F_vid.shape[0]), [0.9, 2]))
    idx_start, idx_stop = tuple(map(lambda f: int((f / (fps / 2)) * F_vid.shape[0]), [HEART_LOW / 60, HEART_HIGH / 60]))
    Fr = np.abs(F_vid[idx_start:idx_stop, ...])
    nf, nrow, ncol, nch = Fr.shape
    max_f_list = []
    for r in range(nrow):
        for c in range(ncol):
            for ch in range(nch):
                fr_list = Fr[:, r, c, ch]
                current_max = 0
                max_idx = 0
                for i, fvalue in enumerate(fr_list):
                    if fvalue > current_max:
                        max_idx = i
                        current_max = fvalue
                f_max = (max_idx + idx_start) / (len(F_vid)) * (fps / 2)  # Hz
                max_f_list.append(f_max)
    n = len(max_f_list)
    max_f_list = sorted(max_f_list)[int(n / 6):-1 * int(n / 10)]
    return np.mean(max_f_list)


def extract_heart_rate(allFrames_b, nchannel=3, fps=30) -> float:
    """
    Parameters
    ----------
    allFrames_b : list of bytearray (each item is a video frame)
    nchannel : either be 3 (color format BGR) or 1 (grayscale)

    Returns
    -------
    a floating number indicating heart rate (beats/second).

    """
    assert ((nchannel == 1) or (nchannel == 3))
    if len(allFrames_b) == 0:
        return -1
    else:
        assert (len(allFrames_b[0]) == face_area_h * face_area_w * nchannel)
        # print(face_area_h*face_area_w*nchannel)
        allFrames = []
        for frame_bytes in allFrames_b:
            frame = np.array(bytearray(frame_bytes), dtype=np.uint8)
            if nchannel == 3:
                frame = frame.reshape((face_area_h, face_area_w, 3))
            else:
                frame.reshape((face_area_h, face_area_w))
            frame_f32 = (frame / 255.0).astype('float32')
            frame = cv.pyrDown(frame_f32)  # Gaussian blur x1
            frame = cv.pyrDown(frame)  # Gaussian blur x2
            if (nchannel == 3):
                frame = cv.cvtColor(frame, cv.COLOR_BGR2YCrCb)
            allFrames.append(frame)
        fmax = find_freq_method2(np.array(allFrames), nchannel, fps)
        return float(fmax * 60)


def task_camera_based_pulse(cam_name: str, cam_addr: str, cam_port: int, cmd_q: SimpleQueue,
                            cancel_task_id: Value, terminate_evnt: Event, t_interval: float = 0.5) -> float:
    """
    Handler function for `cam_health` task.
    put进cmd_q中的消息，除了特殊的 _PID 消息，都会被直接转发给GUI主界面。
    """
    # !!!! 注意，一上来先注册自己这个task, 后面cancel的时候是根据cancel_task_id.value == pid来实现的。
    pid = os.getpid()
    print(f"(PID-{pid}) Starting a new camera pulse task!")
    cmd_q.put(("_PID", (f'cam_health {cam_name}', pid)))

    class CamManager(BaseManager):
        pass

    CamManager.register('get_data_deq')
    CamManager.register('get_pulse_q', )
    CamManager.register('get_person_valid', )

    print(f"(PID-{pid}) trying to connect to camera resource manager@{cam_addr, cam_port}")
    m = CamManager(address=(cam_addr, cam_port), authkey=b'cpn')
    try:
        m.connect()
    except:
        s = f"Data source connection fail. Check if {cam_name} is running! Aborting task."
        print(f'(PID-{pid})' + s)
        cmd_q.put(('_abort', pid, s))
        return
    data_deq = m.get_data_deq()
    if not data_deq:
        # 如果manager连上但没正常工作，读queue返回的东西都是None
        s = f"Data source got None. Check if {cam_name} is running correctly! Aborting task."
        print(f'(PID-{pid})' + s)
        cmd_q.put(('_abort', pid, s))
        return
    pulse_q = m.get_pulse_q()
    person_valid = m.get_person_valid()
    print(f"(PID-{pid}) Connected!")

    p_v_lasttime = False
    while not terminate_evnt.is_set():
        try:
            if cancel_task_id.value == pid:
                print(f"(PID-{pid}) Received task_cancel signal!")
                cancel_task_id.value = 0
                break
            else:
                pulse_freq = extract_heart_rate(deepcopy(data_deq))
                if person_valid.get_value() == 1:
                    if not pulse_q.full():
                        pulse_q.put(float(pulse_freq))
                    cmd_q.put(('pulserate', float(pulse_freq)))
                    if not p_v_lasttime:
                        # cmd_q.put(('personcome', cam_name))
                        cmd_q.put(('personstate', 'come'))
                        p_v_lasttime = True
                else:
                    if p_v_lasttime:
                        # cmd_q.put(('persongone', cam_name))
                        cmd_q.put(('personstate', 'gone'))
                        p_v_lasttime = False
            sleep(t_interval)  # 每半秒钟更新一次心跳
        except Exception as err:  # 运行中出现连接断开之类错误
            s = f"Error encountered with {cam_name}: {err}. Aborting task."
            print(f'(PID-{pid})' + s)
            cmd_q.put(('_abort', pid, s))
            return

    print(f"(PID-{pid}) Finish camera task processing for {cam_name}. Subprocess exits.")


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
                X = np.random.randn(700, 700)
                Y = np.random.randn(700, 700)
                Z = X.dot(Y)
                sleep(0.1)
        except Exception as err:  # 运行中出现连接断开之类错误
            s = f"Error encountered with vlc_receiver: {err}. Aborting task."
            print(f'(PID-{pid})' + s)
            cmd_q.put(('_abort', pid, s))
            return


def vlc_surveillance(task_name: str, task_args: str, addr: str, port: int, file_path: str, cmd_q: SimpleQueue,
                     cancel_task_id: Value, terminate_event: Event) -> float:
    # print("*****************vlc_streaming*****************")
    pid = os.getpid()
    print("------Process PID======= " + str(pid))
    print(f"(PID-{pid}) Starting a new vlc streaming task!")
    cmd_q.put(("_PID", (f'{task_name}', pid)))
    # camera_name = list_video_devices()[0][1]
    # if "Integrated" not in camera_name:
    #     camera_name = "camera_1"
    # print(f">>>>>>>> vlc_surveillance ... camera's name is: {camera_name}")
    # ad = "sout=#transcode{vcodec=h264,vb=800,acodec=mpga,scale=1,ab=128,channels=2,samplerate=44100}:" \
    #      "duplicate{dst=udp{mux=ts,dst=" + addr + ":" + str(port) + "}}"
    # params = [ad, "no-sout-all", "sout-keep", "file-caching=500"]
    # inst = vlc.Instance()
    # media = inst.media_new(f"dshow://:dshow-vdev='{camera_name}'", *params)
    # media_player = media.player_new_from_media()
    # media_player.play()
    vlc_streamer = StreamerPlayer(parent=None, addr=addr, port=port, local_port="2234",
                                  video_source="dshow://:dshow-vdev='Integrated Camera'")
    vlc_streamer.startStream()
    while not terminate_event.is_set():
        try:
            if cancel_task_id.value == pid:
                print(f"(PID-{pid}) Received task_cancel signal!")
                cancel_task_id.value = 0
                # pos_stream = media_player.get_position()  # 获取当前播放位置
                # media_player.stop()
                vlc_streamer.stopStream()
                sleep(0.1)
                break
            else:
                continue
        except Exception as err:  # 运行中出现连接断开之类错误
            s = f"Error encountered with vlc: {err}. Aborting task."
            print(f'(PID-{pid})' + s)
            cmd_q.put(('_abort', pid, s))
            return


def vlc_streaming(task_name: str, task_args: str, addr: str, port: int, file_path: str, start_pos: float, cmd_q: SimpleQueue,
                  cancel_task_id: Value, terminate_event: Event) -> float:
    # print("*****************vlc_streaming*****************")
    pid = os.getpid()
    print("------Process PID======= " + str(pid))
    print(f"(PID-{pid}) Starting a new vlc streaming task!")
    cmd_q.put(("_PID", (f'{task_name}', pid)))

    if 'GAME' in file_path:
        ad = "sout=#duplicate{dst=udp{mux=ts,dst=" + addr + ":" + str(port) + "}}"
        params = [ad, "sout-all", "sout-keep", "repeat"]
        inst = vlc.Instance()
        file_path = file_path.lower()
        media = inst.media_new(f'{file_path}', *params)
        media_player = media.player_new_from_media()
        print("------vlc_s start_pos:" + str(start_pos))
        media_player.play()
        media_player.set_position(float(start_pos))  # 从所设定的位置开始播放
        sleep(2)
        while not media_player.is_playing():
            media_player.play()
            media_player.set_position(float(start_pos))
            sleep(1)
    elif 'fake1' in file_path:
        # ad = "sout=#duplicate{dst=udp{mux=ts,dst=" + addr + ":" + "10045" + "},dst=display}"
        ad = "sout=#duplicate{dst=udp{mux=ts,dst=" + addr + ":" + "1234" + "},dst=display}"
        params = [ad, "sout-all", "sout-keep", "repeat"]
        inst = vlc.Instance()
        media = inst.media_new('./worldCup.mp4', *params)
        media_player = media.player_new_from_media()
        print("------vlc_s start_pos:" + str(start_pos))
        media_player.play()
        media_player.set_position(float(start_pos))  # 从所设定的位置开始播放
        sleep(2)
        while not media_player.is_playing():
            media_player.play()
            media_player.set_position(float(start_pos))
            sleep(1)
    elif 'fake2' in file_path:
        # ad = "sout=#duplicate{dst=udp{mux=ts,dst=" + addr + ":" + "10046" + "},dst=display}"
        ad = "sout=#duplicate{dst=udp{mux=ts,dst=" + addr + ":" + "1235" + "},dst=display}"
        params = [ad, "sout-all", "sout-keep", "repeat"]
        inst = vlc.Instance()
        media = inst.media_new('./worldCup.mp4', *params)
        media_player = media.player_new_from_media()
        print("------vlc_s start_pos:" + str(start_pos))
        media_player.play()
        media_player.set_position(float(start_pos))  # 从所设定的位置开始播放
        sleep(2)
        while not media_player.is_playing():
            media_player.play()
            media_player.set_position(float(start_pos))
            sleep(1)
    else:
        ad = "sout=#duplicate{dst=udp{mux=ts,dst=" + addr + ":" + str(port) + "},dst=display}"
        params = [ad, "sout-all", "sout-keep", "repeat"]
        inst = vlc.Instance()
        media = inst.media_new(f'{file_path}', *params)
        media_player = media.player_new_from_media()
        print("------vlc_s start_pos:" + str(start_pos))
        media_player.play()
        media_player.set_position(float(start_pos))  # 从所设定的位置开始播放
        sleep(2)
        while not media_player.is_playing():
            media_player.play()
            media_player.set_position(float(start_pos))
            sleep(1)
    while not terminate_event.is_set():
        try:
            if cancel_task_id.value == pid:
                print(f"(PID-{pid}) Received task_cancel signal!")
                cancel_task_id.value = 0
                pos_stream = media_player.get_position()  # 获取当前播放位置
                media_player.stop()
                sleep(0.1)
                cmd_q.put(('vlc_state', str(pos_stream)))
                print("------当前播放位置::Pos_streaming:" + str(pos_stream))
                break
            elif media_player.is_playing() == 0:
                print("media_player.is_no_playing")
                sleep(0.2)
                break
            else:
                continue
        except Exception as err:  # 运行中出现连接断开之类错误
            s = f"Error encountered with vlc: {err}. Aborting task."
            print(f'(PID-{pid})' + s)
            cmd_q.put(('_abort', pid, s))
            return


def vlcc_streaming(addr: str, port: int, file_path: str, start_pos: float, cmd_q: SimpleQueue,
                   cancel_task_id: Value, terminate_event: Event) -> float:
    pid = os.getpid()
    print("------Process PID======= " + str(pid))
    print(f"(PID-{pid}) Starting a new vlcc streaming task!")
    cmd_q.put(("_PID", ('vlcc', pid)))

    if 'GAME' in file_path:
        ad = "sout=#duplicate{dst=udp{mux=ts,dst=" + addr + ":" + str(port) + "}}"
        params = [ad, "sout-all", "sout-keep", "repeat"]
        inst = vlc.Instance()
        file_path = file_path.lower()
        media = inst.media_new(f'{file_path}', *params)
        media_player = media.player_new_from_media()
        print("------vlc_s start_pos:" + str(start_pos))
        media_player.play()
        media_player.set_position(float(start_pos))  # 从所设定的位置开始播放
        sleep(2)
        while not media_player.is_playing():
            media_player.play()
            media_player.set_position(float(start_pos))
            sleep(1)
    elif 'fake1' in file_path:
        ad = "sout=#duplicate{dst=udp{mux=ts,dst=" + addr + ":" + "10045" + "},dst=display}"
        params = [ad, "sout-all", "sout-keep", "repeat"]
        inst = vlc.Instance()
        media = inst.media_new('./worldCup.mp4', *params)
        media_player = media.player_new_from_media()
        print("------vlc_s start_pos:" + str(start_pos))
        media_player.play()
        media_player.set_position(float(start_pos))  # 从所设定的位置开始播放
        sleep(2)
        while not media_player.is_playing():
            media_player.play()
            media_player.set_position(float(start_pos))
            sleep(1)
    elif 'fake2' in file_path:
        ad = "sout=#duplicate{dst=udp{mux=ts,dst=" + addr + ":" + "10046" + "},dst=display}"
        params = [ad, "sout-all", "sout-keep", "repeat"]
        inst = vlc.Instance()
        media = inst.media_new('./worldCup.mp4', *params)
        media_player = media.player_new_from_media()
        print("------vlc_s start_pos:" + str(start_pos))
        media_player.play()
        media_player.set_position(float(start_pos))  # 从所设定的位置开始播放
        sleep(2)
        while not media_player.is_playing():
            media_player.play()
            media_player.set_position(float(start_pos))
            sleep(1)
    else:
        ad = "sout=#duplicate{dst=udp{mux=ts,dst=" + addr + ":" + str(port) + "},dst=display}"
        params = [ad, "sout-all", "sout-keep", "repeat"]
        inst = vlc.Instance()
        media = inst.media_new(f'{file_path}', *params)
        media_player = media.player_new_from_media()
        print("------vlc_s start_pos:" + str(start_pos))
        media_player.play()
        media_player.set_position(float(start_pos))  # 从所设定的位置开始播放
        sleep(2)
        while not media_player.is_playing():
            media_player.play()
            media_player.set_position(float(start_pos))
            sleep(1)
    while not terminate_event.is_set():
        try:
            if cancel_task_id.value == pid:
                print(f"(PID-{pid}) Received task_cancel signal!")
                cancel_task_id.value = 0
                media_player.stop()
                sleep(0.1)
                break
            elif media_player.is_playing() == 0:
                print("media_player.is_no_playing")
                sleep(0.2)
                break
            else:
                continue
        except Exception as err:  # 运行中出现连接断开之类错误
            s = f"Error encountered with vlc: {err}. Aborting task."
            print(f'(PID-{pid})' + s)
            cmd_q.put(('_abort', pid, s))
            return


def dispatch(c, id, methodname, args=(), kwds={}):
    """
    Send a message to manager using connection `c` and return response
    """
    c.send((id, methodname, args, kwds))
    kind, result = c.recv()
    if kind == '#RETURN':
        return result
    raise ValueError(f'{kind, result}')


def shutdown_multiprocessing_manager_server(addr: Tuple, key: str):
    """诡异的关掉server方式。参考 https://stackoverflow.com/a/70649119/19733048
    """
    conn = Client(address=addr, authkey=key)
    dispatch(conn, None, 'shutdown')  # from util import dispatch
    conn.close()


"""
def vlc_streamer(addr: str, port: int, file_path: str, start_pos: float):
    ad = "sout=#duplicate{dst=udp{mux=ts,dst=" + addr + ":" + str(port) + "},dst=display}"
    params = [ad, "sout-all", "sout-keep", "repeat"]
    inst = vlc.Instance()
    media = inst.media_new(f'{file_path}', *params)
    media_player = media.player_new_from_media()
    media_player.play()
    media_player.set_position(float(start_pos))  # 从所设定的位置开始播放
    sleep(2)
    while not media_player.is_playing():
        media_player.play()
        media_player.set_position(float(start_pos))
        sleep(1)


# 二次开发python-vlc包实现音视频的网络串流
def vlc_sender(addr: str, port: int, file_path: str, start_pos: float, cmd_q: SimpleQueue,
               cancel_task_id: Value, terminate_event: Event) -> float:
    pid = os.getpid()
    cmd_q.put(("_PID", ('vlc', pid)))
    ad = "sout=#duplicate{dst=udp{mux=ts,dst=" + addr + ":" + str(port) + "},dst=display}"
    params = [ad, "sout-all", "sout-keep", "repeat"]
    inst = vlc.Instance()
    media = inst.media_new(f'{file_path}', *params)
    media_player = media.player_new_from_media()
    print("------vlc_s start_pos:" + str(start_pos))
    media_player.play()
    media_player.set_position(float(start_pos))  # 从所设定的位置开始播放
    sleep(2)
    while not media_player.is_playing():
        media_player.play()
        media_player.set_position(float(start_pos))
        sleep(1)

    while not terminate_event.is_set():
        try:
            if cancel_task_id.value == pid:
                print(f"(PID-{pid}) Received task_cancel signal!")
                cancel_task_id.value = 0
                pos_stream = media_player.get_position()  # 获取当前播放位置
                media_player.stop()
                sleep(0.1)
                cmd_q.put(('vlc', str(pos_stream)))
                cmd_q.put(('vlc_state', str(pos_stream)))
                print("------当前播放位置::Pos_streaming:" + str(pos_stream))
                break
            elif media_player.is_playing() == 0:
                print("media_player.is_no_playing")
                sleep(0.2)
                break
            else:
                continue
        except Exception as err:  # 运行中出现连接断开之类错误
            s = f"Error encountered with vlc_sender: {err}. Aborting task."
            print(f'(PID-{pid})' + s)
            cmd_q.put(('_abort', pid, s))
            return
"""
