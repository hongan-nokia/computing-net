from multiprocessing import Process, Queue, Event, Value
from collections import deque
from multiprocessing.managers import BaseManager
from time import sleep
from os import path
from threading import Thread
from typing import Union
import cv2 as cv
import numpy as np
from basemodel import BaseNodeModel, GUI_msg_handler, terminate_demo_cmd
from utils import FakeCap, shutdown_multiprocessing_manager_server, \
    RemoteManagerValue, faceDetector, FogFaceDetector


@GUI_msg_handler
def process_GUI_msg(cmd: str, args: tuple, node_obj: 'FogCam'):
    """
    命令执行逻辑，都写在这个函数里。
    msg - 主程序(GUI)发来的命令
    node_obj - 响应命令的节点对象(在后面具体定义的)

    通常这里直接调用node_obj的方法做出节点行为.
    """
    if cmd == terminate_demo_cmd:
        # 这里时有特殊的子进程结束信号先要set()一下再丢给外层GUI_msg_process()
        ESC_pressed.set()
        node_obj.stop_server()
        return cmd, args

    elif cmd == 'fps':  # 询问camera 的FPS值
        node_obj.send2gui(('fps', node_obj.fps))
        return

    elif cmd == 'set_fps':  # 改变camera的frame_per_second参数
        node_obj.print(f"Changing camera FPS to {args[0]}.")
        # to be implemented
        return

    else:
        return cmd, args


# simulation video source
VIDEO_SIM = '.\\guiwidgets\\images\\zdx.bmp'
FPS = 30
# define the frame area that is used by the extract_heart_rate algorithm
# i.e. facearea = frame[cut_y0:cut_y1, cut_x0:cut_x1,:]
cut_x0, cut_y0 = (170, 80)
cut_x1, cut_y1 = (470, 430)

# define inter-process communication utilities
ESC_pressed = Event()  # `show` process set this when ESC pressed and will exit
show_q = Queue(maxsize=2)  # put frame into it, 'show' process get from it.
data_deq = deque(maxlen=14 * FPS)  # put frame into it, remote compute nodes get from it.
pulse_q = Queue(maxsize=4)  # compute nodes put pulse result into it, 'show' process get from it.
face_valid = Value('i', 0)  # 'show' process set this value to inform main process
# whether frame collection should continue or not.
person_valid = RemoteManagerValue(v=-1)  # local 'show' process set this flag to indicate


# whether the specific person (a "registered face") is detected.

class CamManager(BaseManager): pass


CamManager.register('get_data_deq', callable=lambda: data_deq)
CamManager.register('get_pulse_q', callable=lambda: pulse_q)
CamManager.register('get_face_valid', callable=lambda: face_valid)
CamManager.register('get_person_valid', callable=lambda: person_valid)

# load the faceframe
if not (path.exists("algorithmDev/faceframe640x480.bmp")):
    raise ValueError('faceframe640x480.bmp not exist.')
else:
    faceframe = cv.imread(path.abspath('algorithmDev/faceframe640x480.bmp'))
    facemask = cv.bitwise_not(faceframe)
    faceframe_white = facemask.copy()
    faceframe_green = facemask.copy()
    for row in faceframe_green:
        for col in row:
            if col[0] != 0:
                col[0] = 83  # b
                col[1] = 217  # g
                col[2] = 38  # r


def add_faceframe(img, facevalid):
    img_withfaceframe = cv.bitwise_and(img, faceframe)
    if facevalid:
        img_withfaceframe = cv.bitwise_or(img_withfaceframe, faceframe_green)
    else:
        img_withfaceframe = cv.bitwise_or(img_withfaceframe, faceframe_white)
    return img_withfaceframe


def show_video(frame_q, heart_rate_q, facevalidflag, person_valid, detector_metadata, conf_thres=0.5,
               ESC_pressed_event=ESC_pressed):
    """
    Parameters
    ----------
    frame_q : Queue (inter process)
        get one frame from this queue, show on screen and detect face in it.
    heart_rate_q : Queue (inter process)
        get heart rate (a floating number) and add it on the frame.
    facevalidflag : Value (inter process flag)
        fill this value with 1/0 to indicate whether a face is in the right position.
    person_valid : Value (inter process flag)
        fill this value to indicate whether a registered face is present in the frame
    detector_metadata : information for generating a faceDetector object
        (DNNmodel, DNNwt, inputsize, inputmean).
    conf_thres : confidence threshold to filter detection results

    Returns
    -------
    None.

    """
    DNNmodel, DNNwt, inputsize, inputmean = detector_metadata
    detector = faceDetector(DNNmodel, DNNwt, inputsize, inputmean)
    heartrate = 'not detected'
    beats_per_min = 0
    (startX, startY, endX, endY) = (0, 0, 0, 0)
    while True:
        frame = frame_q.get()
        if (len(frame) == 4):
            if (frame == 'stop'):
                cv.destroyAllWindows()
                break
        detections = detector.detect(frame)
        # loop over the detections
        if detections.shape[2] > 0:
            # extract the confidence (i.e., probability) associated with the
            # prediction
            confidence = detections[0, 0, 0, 2]

            # filter out weak detections by ensuring the `confidence` is
            # greater than the minimum confidence
            if confidence < conf_thres:
                person_valid.value = 0
                facevalidflag.value = 0
            else:
                person_valid.value = 1
                # compute the (x, y)-coordinates of the bounding box for the object
                h, w = frame.shape[:2]
                box = detections[0, 0, 0, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype("int")
                if (startX > 177 and startX < 212 and startY > 61 and startY < 132 and endX > 428 and endX < 475):
                    facevalidflag.value = 1
                else:
                    facevalidflag.value = 0
                # draw the bounding box of the face
                # cv.rectangle(frame, (startX, startY), (endX, endY),(0, 0, 255), 2)
                # print(startX, startY, endX, endY, confidence)
        else:
            person_valid.value = 0
            facevalidflag.value = 0

        # print(confidence, person_valid.value, facevalidflag.value)

        if not heart_rate_q.empty():
            beats_per_min = float(heart_rate_q.get())
            heartrate = "%.2f" % beats_per_min
            # heart_rate_copy.put(beats_per_min)

        frame = add_faceframe(frame, facevalid=bool(facevalidflag.value))
        text_color = (0, 255, 0) if (beats_per_min > 65 and beats_per_min < 85) else (180, 0, 255)
        if facevalidflag.value == 1:
            cv.putText(frame, heartrate, (50, 50), cv.FONT_HERSHEY_SIMPLEX, 0.75, text_color, 2)
        else:  # hide heartrate text when face is not detected
            cv.putText(frame, ' ', (50, 50), cv.FONT_HERSHEY_SIMPLEX, 0.75, text_color, 2)

        # show the output frame
        cv.imshow("Frame", frame)
        if ESC_pressed_event.is_set():
            cv.destroyAllWindows()
            break
        ch = cv.waitKey(1)
        if ch == 27:  # ESC
            ESC_pressed_event.set()
            cv.destroyAllWindows()
            break
    print('Show_video() exiting')


def create_sim_video_src(source=VIDEO_SIM, dutycycle=0.3, fps=FPS):
    print('Creating simulation video source')
    cap = FakeCap(source, 300, fps, dutycycle, reverse_img_blank=True)
    return cap


class FogCam(BaseNodeModel):
    def __init__(self, demo_config, node_config, msg_process_fn=process_GUI_msg,
                 video_src: Union[int, str] = 0, sim=False) -> None:
        self.video_src = video_src
        self.fps = 0
        self.sim = sim  # simulation mode: fills fake camera data into queue.
        # 如果程序找不到摄像头，默认fall back 到simulation mode
        super().__init__(demo_config, node_config, msg_process_fn)

    def start(self):
        """
        启动节点, 默认先启动一个与主程序通信的线程, 再启动一个multiprocessing.manager, 作为一个
        其他节点可以来取数据的server。
        """
        # 一个本地的进程间资源manager。本地显示进程，和远端compute node，都会连接过来取数据
        self.m = CamManager(address=(self.node_conf.data_ip, self.node_conf.data_port), authkey=b'cpn')

        # 启动show进程 
        self.p_show = Process(name='show', target=show_video,
                              args=(show_q, pulse_q, face_valid, person_valid, FogFaceDetector, 0.5, ESC_pressed))
        self.p_show.start()

        # 开始往queue里填数据
        self.t_datagen = Thread(name=f'{self.node_conf.node_name}_data_gen', target=self.data_gen, )
        self.t_datagen.start()

        # 开始manager接受远程compute node 访问 
        self.s = self.m.get_server()
        self.s.serve_forever()  # this line runs in blocks mode, must be put at the end
        self.close()

    def data_gen(self):
        if (type(self.video_src) == int) and (not self.sim):
            cap = cv.VideoCapture(self.video_src)
            self.fps = cap.get(cv.CAP_PROP_FPS)  # typically be 30
            if self.fps == 0:
                cap = create_sim_video_src(VIDEO_SIM)
                self.sim = True
        else:  # fall back to a simulation source
            self.fps = FPS
            cap = create_sim_video_src(self.video_src, self.fps)
        self.print('cap source started')

        # first time detection
        n_frame_valid = 0
        while (n_frame_valid < 8 * self.fps) and (not self.terminateDemo):
            _, img = cap.read()
            img = img[:, ::-1, :]
            if not show_q.full():
                show_q.put(img)
            if (face_valid.value == 1):
                n_frame_valid += 1
                data_deq.append(img[cut_y0:cut_y1, cut_x0:cut_x1, ...].tobytes())
            else:
                n_frame_valid = 0

        # loop until explicit exit signal
        while not self.terminateDemo:
            _, img = cap.read()
            img = img[:, ::-1, :]
            data_deq.append(img[cut_y0:cut_y1, cut_x0:cut_x1, ...].tobytes())
            if not show_q.full():
                show_q.put(img)

            if ESC_pressed.is_set():
                print('exiting!')
                self.terminateDemo = True
                break
        cap.release()
        self.print('exiting data_gen()')

    def close(self):
        print('closing.')
        try:
            self.stop_server()
        finally:
            self.print("stop_server() ok")
        self.p_show.join()
        self.t_datagen.join()

    def stop_server(self):
        """
        诡异的关掉server方式。参考 https://stackoverflow.com/a/70649119/19733048
        Note 20220810 - 这个方式也只能保证资源回收，serve_forever()有时候还是无法退出。
                        需要进一步kill掉其启动的所有后台线程，太麻烦，先不管
        """
        if not self.s.stop_event.is_set():
            # address and authkey same as when started the manager
            shutdown_multiprocessing_manager_server(addr=(self.node_conf.data_ip, self.node_conf.data_port), key=b'cpn')
            self.s.stop_event.set()
            sleep(0.1)
            self.print('stop_server() done')
