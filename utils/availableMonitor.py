# -*- coding: utf-8 -*-
"""
@Time: 5/28/2024 8:23 PM
@Author: Honggang Yuan
@Email: honggang.yuan@nokia-sbell.com
Description: 
"""
import cv2
from PyCameraList.camera_device import test_list_cameras, list_video_devices, list_audio_devices

def get_camera_names():
    # 获取本机所有可用的摄像头
    camera_names = []
    for i in range(10):  # 假设最多检查10个摄像头
        cap = cv2.VideoCapture(i)
        if not cap.isOpened():
            break
        _, _ = cap.read()  # 尝试读取一帧
        print(cap.getBackendName())
        cap.release()
        camera_names.append(f"Camera {i}")
    return camera_names


if __name__ == "__main__":
    # camera_names = get_camera_names()
    # if camera_names:
    #     print("可用摄像头：")
    #     for name in camera_names:
    #         print(name)
    # else:
    #     print("未找到可用摄像头。")
    cameras = list_video_devices()
    print(cameras)
