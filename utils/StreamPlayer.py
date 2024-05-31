# -*- coding: utf-8 -*-
"""
@Time: 5/31/2024 3:59 PM
@Author: Honggang Yuan
@Email: honggang.yuan@nokia-sbell.com
Description: 
"""
import sys
from time import sleep
import socket
import vlc
from PyQt5.QtWidgets import QWidget


# :sout=#transcode{vcodec=h264,vb=800,acodec=mpga,ab=128,channels=2,samplerate=44100,scodec=none}:udp{mux=ts,
# dst=111.111.1.1:1234} :no-sout-all :sout-keep
class StreamerPlayer():
    def __init__(self, parent=None, addr=None, port=None, local_port=None, video_source=None):
        self.addr = addr
        self.port = port
        self.video_uri = video_source

        self.vlc_instance = vlc.Instance("--no-xlib",
                                         "--input-repeat=99999")  # "--no-xlib" is required for running on Linux without X11
        self.video_streamer = self.vlc_instance.media_player_new()

        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        print(ip_address)

        ad = "sout=#transcode{vcodec=h264,vb=800,acodec=mpga,scale=1,ab=128,channels=2,samplerate=44100}:" \
             "duplicate{dst=udp{mux=ts,dst=" + addr + ":" + port + "},dst=udp{mux=ts,dst=" + ip_address + ":" + local_port + "}}"
        self.params = [ad, "no-sout-all", "sout-keep", "file-caching=500"]

        if parent is not None:
            if sys.platform.startswith("linux"):  # for Linux using the X Server
                self.video_streamer.set_xwindow(parent.winId())
            elif sys.platform == "win32":  # for Windows
                self.video_streamer.set_hwnd(parent.winId())
            elif sys.platform == "darwin":  # for macOS
                self.video_streamer.set_nsobject(parent.winId())

        self.media = self.vlc_instance.media_new(self.video_uri, *self.params)
        self.video_streamer = self.media.player_new_from_media()

    def setMute(self, flag):
        self.video_streamer.audio_set_mute(flag)

    def startStream(self):
        while True:
            if not self.video_streamer.is_playing():
                self.video_streamer.play()
                # self.video_streamer.set_position(0.4)
            else:
                break
        print(f"self.video_streamer.is_Streaming() >>>> {self.video_streamer.is_playing()}")

    def stopStream(self):
        self.video_streamer.stop()
        while True:
            if self.video_streamer.is_playing():
                self.video_streamer.stop()
            else:
                break
        print(f"self.video_streamer.is_Streaming() >>>> {self.video_streamer.is_playing()}")

    def resumeStream(self):
        if not self.video_streamer.is_playing():
            self.video_streamer.play()
        print(f"self.video_streamer continue_Streaming() >>>> {self.video_streamer.is_playing()}")

    def pauseStream(self):
        if self.video_streamer.is_playing():
            self.video_streamer.pause()

    def switch_video_source(self, video_source):
        self.media = self.vlc_instance.media_new(video_source, *self.params)
        self.video_streamer.set_media(self.media)
