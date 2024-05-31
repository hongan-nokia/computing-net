import sys
from time import sleep

import vlc
from PyQt5.QtWidgets import QWidget


# :sout=#transcode{vcodec=h264,vb=800,acodec=mpga,ab=128,channels=2,samplerate=44100,scodec=none}:udp{mux=ts,
# dst=111.111.1.1:1234} :no-sout-all :sout-keep
class VideoPlayer(QWidget):
    def __init__(self, frame=None, videoPath="../videos/nokiaLogo.mp4", miface=None):
        super().__init__()

        self.vlc_instance = vlc.Instance("--no-xlib",
                                         "--input-repeat=99999")  # "--no-xlib" is required for running on Linux without X11
        self.media_player = self.vlc_instance.media_player_new()
        self.media_player.set_fullscreen(False)
        self.miface = f"miface={miface}"  # miface=eth0
        self.media = self.vlc_instance.media_new(videoPath, self.miface)
        self.media_player.set_media(self.media)

        if sys.platform.startswith("linux"):  # for Linux using the X Server
            self.media_player.set_xwindow(frame.winId())
        elif sys.platform == "win32":  # for Windows
            self.media_player.set_hwnd(frame.winId())
        elif sys.platform == "darwin":  # for macOS
            self.media_player.set_nsobject(frame.winId())

    def change_video(self, new_video_path):
        self.media_player.stop()  # 停止当前视频的播放

        new_media = self.vlc_instance.media_new(new_video_path, self.miface)
        self.media_player.set_media(new_media)

        self.media_player.play()

    def setMute(self, flag):
        self.media_player.audio_set_mute(flag)

    def startPlayer(self):
        start_cnt = 0
        while start_cnt < 20:
            if not self.media_player.is_playing():
                self.media_player.play()
                sleep(0.5)
                start_cnt += 1
            else:
                break
        print(f"self.media_player.is_playing() >>>> {self.media_player.is_playing()}")
        return self.media_player.is_playing()

    def stopPlayer(self):
        while True:
            if self.media_player.is_playing():
                self.media_player.stop()
                sleep(0.1)
            else:
                break
        print(f"self.media_player.is_playing() >>>> {self.media_player.is_playing()}")
