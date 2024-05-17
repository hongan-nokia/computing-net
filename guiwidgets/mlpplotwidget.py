# -*- coding: utf-8 -*-
"""
@Time: 5/17/2024 9:32 AM
@Author: Honggang Yuan
@Email: honggang.yuan@nokia-sbell.com
Description: 
"""
import matplotlib.style as mplstyle

mplstyle.use('ggplot')
# mplstyle.use('fast')
import matplotlib.pyplot as plt

plt.style.use('ggplot')
# plt.style.use('fast')

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.widgets import CheckButtons
from PyQt5.QtWidgets import QSizePolicy, QWidget, QVBoxLayout, QGraphicsOpacityEffect, QLabel
from PyQt5.QtCore import (pyqtSignal, pyqtSlot, QObject, QLineF, QPointF, QRectF, Qt, QTimer, QSize, QRect,
                          QPropertyAnimation, QEvent)
from PyQt5.QtGui import (QBrush, QColor, QPainter, QFont, QPalette)
import numpy as np
from collections import deque
import pyqtgraph as pg
import types
from multiprocessing import Queue
from typing import Tuple
from random import randint


def extract_samples_int(bin_data):
    mview = memoryview(bin_data)
    mview_int8 = mview.cast('b')
    samples_int = mview_int8.tolist()
    return samples_int


def extract_samples_float(bin_data):
    return list(memoryview(bin_data).cast('f').tolist())


def channel_filter(raw_iq, start, stop):
    """ select the subcarriers to draw """
    clean_iq = raw_iq[start: stop]
    (N, L) = np.shape(clean_iq)
    return np.reshape(clean_iq, (N * L,), order='F')


class MplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.).
       Subclass this and reimplement compute_initial_figure() and update_figure()
       methods, like the `simpleSinePlot` example below.

       Typically, the update_figure() method will be connected to a GUI signal
       (e.g. a repeative timer) and called automatically.

       self.datadevice could be an device where data is acquired.
    """

    def __init__(self, parent=None, width=4, height=4, dpi=100,
                 datadevice=None, tight_layout=False):
        fig = Figure(figsize=(width, height), dpi=dpi, tight_layout=tight_layout)
        self.axes = fig.add_subplot(111)
        self.datadevice = datadevice  #
        # self.compute_initial_figure()

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.fig = fig

    def compute_initial_figure(self):
        pass

    def update_figure(self):
        pass


class simpleSinePlot(MplCanvas):
    """Simple canvas with a sine plot."""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.compute_initial_figure()
        # self.datadevice.query('IDN?')

    def compute_initial_figure(self):
        self.phi = 0  # init phase
        self.t = np.arange(0.0, 3.0, 0.01)
        s = np.sin(2 * np.pi * self.t)
        self.axes.plot(self.t, s)
        self.axes.set_ylim(-1.2, 1.2)
        self.draw()

    def update_figure(self):
        self.axes.cla()
        self.phi += 0.2
        s = np.sin(self.t + self.phi)
        self.axes.plot(self.t, s)
        self.axes.set_ylim(-1.2, 1.2)
        self.draw()


class zoomableDynamicPlot_example(pg.PlotWidget):
    def __init__(self, parent=None, zoom_large=(0, 0, 600, 400), zoom_small=(0, 0, 150, 100), init_mode='large',
                 **kwargs):
        super().__init__(parent=parent, **kwargs)
        self.geo_large = QRect(*zoom_large)
        self.geo_small = QRect(*zoom_small)
        init_geo = zoom_small if init_mode == 'small' else zoom_large
        self.setGeometry(*init_geo)
        self.zoom_mode = init_mode  # 'large' or 'small'
        self.zoom_large_animation = self._init_zoom_large_anim()
        self.zoom_small_animation = self._init_zoom_small_anim()
        self.data_line = self.compute_initial_figure()  # this should be a pyqtgraph.PlotDataItem object

        # connect the sigClicked signal to self.switch_mode slot.
        self.data_line.sigClicked.connect(self.switch_mode)

        # use the following function to override plot_widget's mouse_click behavior, because it's default
        # behavior is not responding to mouse click on abitrary position but only responds to the pixles around the curve.
        def mouseClickEvent_override(curve_obj, ev):
            # print(f'overieded func: args={args}, kwargs={kwargs}')
            ev.accept()
            curve_obj.sigClicked.emit(curve_obj)

        self.data_line.curve.mouseClickEvent = types.MethodType(mouseClickEvent_override, self.data_line.curve)

    def _init_zoom_large_anim(self):
        anim = QPropertyAnimation(self, b"geometry")
        anim.setDuration(300)
        anim.setStartValue(self.geo_small)
        anim.setEndValue(self.geo_large)
        return anim

    def _init_zoom_small_anim(self):
        anim = QPropertyAnimation(self, b"geometry")
        anim.setDuration(300)
        anim.setStartValue(self.geo_large)
        anim.setEndValue(self.geo_small)
        return anim

    def compute_initial_figure(self):
        pen_line = pg.mkPen(color=(255, 0, 0))
        brush_fill = pg.mkBrush(QBrush(QColor(0, 255, 255, 200)))  # style = QtCore.Qt.LinearGradientPattern
        self.x = list(range(100))  # 100 time points
        self.y = [randint(0, 100) for _ in range(100)]  # 100 data points
        self.setBackground('w')
        data_line = self.plot(self.x, self.y, pen=pen_line, fillBrush=brush_fill, fillLevel=0)
        return data_line

    def update_figure(self):
        self.x = self.x[1:]  # Remove the first y element.
        self.x.append(self.x[-1] + 1)  # Add a new value 1 higher than the last.
        self.y = self.y[1:]  # Remove the first
        self.y.append(randint(0, 100))  # Add a new random value.
        self.data_line.setData(self.x, self.y)  # Update the data.

    def switch_mode(self):
        ''' switch between large figuer and small figure. '''
        current_size = self.size()
        # print(f'current size = {current_size}')
        if self.zoom_mode == 'small':
            self.zoom_large_animation.start()
            self.zoom_mode = 'large'
        else:
            self.zoom_small_animation.start()
            self.zoom_mode = 'small'


class ZoomableNetMonitor(QWidget):
    """ This is specifically used for fogdemo's cloud node traffic monitoring. """

    def __init__(self, parent=None, zoom_large=(0, 0, 600, 400), zoom_small=(0, 0, 150, 100), init_mode='large',
                 dataq: Queue = None, n_timepoint=15, yrange: Tuple[float, float] = (0, 1),
                 ylabel: str = '', title: str = 'Total Traffic (MB/s)', **kwargs):
        title_geo = kwargs.pop('title_geo', (0, 0, 250, 40))
        super().__init__(parent=parent, **kwargs)
        self.geo_large = QRect(*zoom_large)
        self.geo_small = QRect(*zoom_small)
        self.n_points = n_timepoint
        self.q = dataq
        self.ymin, self.ymax = yrange
        self.ylabel_str = ylabel  # Traffic (MB/s)
        init_geo = zoom_small if init_mode == 'small' else zoom_large
        self.setGeometry(*init_geo)
        self.zoom_mode = init_mode  # 'large' or 'small'
        self.zoom_large_animation = self._init_zoom_large_anim()
        self.zoom_small_animation = self._init_zoom_small_anim()
        # self.opacityeffect = QGraphicsOpacityEffect()
        # self.setGraphicsEffect(self.opacityeffect)
        self.init_fig()
        self.init_title(title, title_geo)
        if init_mode == 'small':
            self.title.setVisible(False)
        self.mousePressEvent = self.switch_mode

    def init_fig(self):
        self.qplot, self.data_line = self.compute_initial_figure()  # this should be a pyqtgraph.PlotDataItem object
        self.qplot.setMouseEnabled(False, False)
        layout = QVBoxLayout()
        layout.addWidget(self.qplot)
        self.setLayout(layout)
        self.setAutoFillBackground(True)

    def init_title(self, title_str: str, geo: Tuple[int, int, int, int]):
        self.title = QLabel(title_str, parent=self)
        font = QFont("Nokia Pure Text", 12, QFont.Bold)  #
        self.title.setGeometry(*geo)
        self.title.setFont(font)
        palette = self.palette()
        palette.setColor(self.foregroundRole(), QColor(18, 65, 145))
        self.title.setPalette(palette)
        self.title.setAlignment(Qt.AlignHCenter | Qt.AlignCenter)

    def _init_zoom_large_anim(self):
        anim = QPropertyAnimation(self, b"geometry")
        anim.setDuration(300)
        anim.setStartValue(self.geo_small)
        anim.setEndValue(self.geo_large)
        return anim

    def _init_zoom_small_anim(self):
        anim = QPropertyAnimation(self, b"geometry")
        anim.setDuration(300)
        anim.setStartValue(self.geo_large)
        anim.setEndValue(self.geo_small)
        return anim

    def compute_initial_figure(self):
        pen_line = pg.mkPen(color=(255, 0, 0))
        brush_fill = pg.mkBrush(QBrush(QColor(0, 255, 255, 200)))  # style = QtCore.Qt.LinearGradientPattern
        qplot = pg.PlotWidget()
        qplot.setYRange(min=self.ymin, max=self.ymax)
        self.x = list(range(self.n_points))  # time points
        self.y = [0] * self.n_points  # data points
        qplot.setBackground('w')
        if self.ylabel_str:
            qplot.setLabel('left', text=self.ylabel_str)
        data_line = qplot.plot(self.x, self.y, pen=pen_line, fillBrush=brush_fill, fillLevel=0)
        if self.zoom_mode == 'small':
            qplot.hideAxis('left')
            qplot.hideAxis('bottom')
        return qplot, data_line

    def update_figure(self):
        # 对于网络流量，queue里每一个数据是一个list，list第一个元素是rxrate, 第二个元素是txrate.
        # 可以加起来或者画两条线。
        templist = []
        ymax_unchange_cnt = 0  # this is for dynamic ymax dajustment
        while not self.q.empty():
            tmp_data = self.q.get()
            # if isinstance(tmp_data, list):
            #     for item in tmp_data:
            #         templist.append(item)
            # else:
            templist.append(tmp_data)
        if len(templist) > 0:
            traffic_samples = [sum(item) / 2 for item in templist]  # MBytes/s
            self.y.append(np.mean(traffic_samples))
            if (max(traffic_samples) > self.ymax) or (ymax_unchange_cnt > (self.n_points + 1)):
                self.ymax = max(traffic_samples) + 1
                self.qplot.setYRange(min=0, max=self.ymax)
            else:
                ymax_unchange_cnt += 1
        else:
            self.y.append(0)
        self.y = self.y[1:]  # Remove the first
        self.data_line.setData(self.x, self.y)  # Update the data.

    def switch_mode(self, event):
        ''' switch between large figuer and small figure. '''
        if self.zoom_mode == 'small':
            self.switch_axis('show')
            # self.opacityeffect.setOpacity(1)
            self.zoom_large_animation.start()
            self.zoom_mode = 'large'
            self.title.setVisible(True)
        else:
            self.switch_axis('hide')
            # self.opacityeffect.setOpacity(0.3)
            self.title.setVisible(False)
            self.zoom_small_animation.start()
            self.zoom_mode = 'small'

    def switch_axis(self, mode: str = 'show'):  # 'hide'
        if mode == 'show':
            self.qplot.showAxis('left')
            self.qplot.showAxis('bottom')
        else:
            self.qplot.hideAxis('left')
            self.qplot.hideAxis('bottom')


class ZoomableDualMonitor(QWidget):
    def __init__(self, parent=None, zoom_large=(0, 0, 600, 400), zoom_small=(0, 0, 150, 100), init_mode='large',
                 dataq_cpu: Queue = None, dataq_net: Queue = None, n_timepoint=15, **kwargs):
        title_cpu = kwargs.pop('title_cpu', 'CPU load (%)')
        title_net = kwargs.pop('title_net', 'Traffic load (MB/s)')
        title_geo_cpu = kwargs.pop('title_geo_cpu', (0, 0, 250, 40))
        title_geo_net = kwargs.pop('title_geo_net', (0, 200, 250, 40))
        self.net_direction = kwargs.pop('net_direction', 'both')  # tx, rx, or both
        self.y_net_max = kwargs.pop('y_net_max', 7000000)  # y axis range
        # print(f'GGGGGGGGGGGGDEG: direction = {self.net_direction}')
        self.hist_avrglen = kwargs.pop('hist_avrglen', 4)  # length for history average
        self.demo_fix = kwargs.pop('demo_fix',
                                   False)  # a special fix for demo experience, to eleminate glances's glitches
        super().__init__(parent=parent, **kwargs)
        self.geo_large = QRect(*zoom_large)
        self.geo_small = QRect(*zoom_small)
        self.n_points = n_timepoint
        self.q_cpu = dataq_cpu
        self.q_net = dataq_net
        init_geo = zoom_small if init_mode == 'small' else zoom_large
        self.setGeometry(*init_geo)
        self.zoom_mode = init_mode  # 'large' or 'small'
        self.zoom_large_animation = self._init_zoom_large_anim()
        self.zoom_small_animation = self._init_zoom_small_anim()
        # self.opacityeffect = QGraphicsOpacityEffect()
        # self.setGraphicsEffect(self.opacityeffect)
        self.init_dual_monitor()
        self.init_title(title_cpu, title_net, title_geo_cpu, title_geo_net)
        if init_mode == 'small':
            self.title_cpu.setVisible(False)
            self.title_net.setVisible(False)
        self.mousePressEvent = self.switch_mode
        self.setWindowOpacity(10)

    def init_dual_monitor(self):
        self.qplot_cpu, self.data_line_cpu = self.compute_initial_figure_cpu()  # this should be a pyqtgraph.PlotDataItem object
        self.qplot_net, self.data_line_net = self.compute_initial_figure_net()
        self.qplot_cpu.setMouseEnabled(False, False)
        self.qplot_net.setMouseEnabled(False, False)
        layout = QVBoxLayout()
        layout.addWidget(self.qplot_cpu)
        layout.addWidget(self.qplot_net)
        self.setLayout(layout)
        self.setAutoFillBackground(True)

    def init_title(self, title_cpu: str, title_net: str, title_geo_cpu: Tuple[int, int, int, int],
                   title_geo_net: Tuple[int, int, int, int]):
        font = QFont("Nokia Pure Text", 12, QFont.Bold)  #
        palette = self.palette()
        palette.setColor(self.foregroundRole(), QColor(18, 65, 145))
        self.title_cpu = QLabel(title_cpu, parent=self)
        self.title_cpu.setGeometry(*title_geo_cpu)
        self.title_net = QLabel(title_net, parent=self)
        self.title_net.setGeometry(*title_geo_net)

        self.title_cpu.setFont(font)
        self.title_cpu.setPalette(palette)
        self.title_cpu.setAlignment(Qt.AlignHCenter | Qt.AlignCenter)
        self.title_net.setFont(font)
        self.title_net.setPalette(palette)
        self.title_net.setAlignment(Qt.AlignHCenter | Qt.AlignCenter)

    def _init_zoom_large_anim(self):
        anim = QPropertyAnimation(self, b"geometry")
        anim.setDuration(300)
        anim.setStartValue(self.geo_small)
        anim.setEndValue(self.geo_large)
        return anim

    def _init_zoom_small_anim(self):
        anim = QPropertyAnimation(self, b"geometry")
        anim.setDuration(300)
        anim.setStartValue(self.geo_large)
        anim.setEndValue(self.geo_small)
        return anim

    def compute_initial_figure_cpu(self):
        pen_line = pg.mkPen(color=(0, 0, 255))
        brush_fill = pg.mkBrush(QBrush(QColor(180, 0, 0, 200)))  # style = QtCore.Qt.LinearGradientPattern
        qplot_cpu = pg.PlotWidget()
        qplot_cpu.setYRange(min=0, max=100)
        self.x_cpu = list(range(self.n_points))  # time points
        self.y_cpu = [0] * self.n_points  # data points
        qplot_cpu.setBackground('w')
        # qplot_cpu.setLabel('left', text='CPU usage (%)')
        data_line_cpu = qplot_cpu.plot(self.x_cpu, self.y_cpu, pen=pen_line, fillBrush=brush_fill, fillLevel=0)
        if self.zoom_mode == 'small':
            qplot_cpu.hideAxis('left')
            qplot_cpu.hideAxis('bottom')

        return (qplot_cpu, data_line_cpu)

    def compute_initial_figure_net(self):
        pen_line = pg.mkPen(color=(255, 0, 0))
        brush_fill = pg.mkBrush(QBrush(QColor(0, 255, 255, 200)))  # style = QtCore.Qt.LinearGradientPattern
        qplot_net = pg.PlotWidget()
        self.x_net = list(range(self.n_points))  # 100 time points
        self.y_net = [0] * self.n_points  # 100 data points
        # self.y_net_max = 100 # y axis range
        qplot_net.setBackground('w')
        qplot_net.setYRange(min=0, max=self.y_net_max)
        # qplot_net.setLabel('left', text='Network Traffic')
        data_line_net = qplot_net.plot(self.x_net, self.y_net, pen=pen_line, fillBrush=brush_fill, fillLevel=0)
        if self.zoom_mode == 'small':
            qplot_net.hideAxis('left')
            qplot_net.hideAxis('bottom')
        return (qplot_net, data_line_net)

    def update_figure(self):
        # print("###########ZoomableDualMonitor update_figure############")
        templist = []
        ymax_unchange_cnt = 0  # this is for dynamic ymax dajustment
        while not self.q_cpu.empty():
            templist.append(self.q_cpu.get())
        if templist:
            self.y_cpu.append(sum([item[0] for item in templist]) / len(templist))
        else:
            hist_mean = 0.7 * np.mean(self.y_cpu[-1 * self.hist_avrglen:])
            self.y_cpu.append(hist_mean)
        self.y_cpu = self.y_cpu[1:]  # Remove the first
        self.data_line_cpu.setData(self.x_cpu, self.y_cpu)  # Update the data.

        # 对于网络流量，queue里每一个数据是一个list，list第一个元素是txrate, 第二个元素是rxrate.
        # net_direction parameter determins which is drawn。
        templist = []
        while not self.q_net.empty():
            templist.append(self.q_net.get())
        if templist:
            if self.net_direction == 'tx':
                traffic_samples = [item[0] for item in templist]
            elif self.net_direction == 'rx':
                traffic_samples = [item[1] for item in templist]
            else:  # 'both'
                traffic_samples = [sum(item) for item in templist]
            self.y_net.append(np.mean(traffic_samples))
            if (max(traffic_samples) > self.y_net_max) or (ymax_unchange_cnt > (self.n_points + 1)):
                self.y_net_max = max(traffic_samples) + 1
                # self.qplot_net.setYRange(min=0, max=self.y_net_max)
                ymax_unchange_cnt = 0
            else:
                ymax_unchange_cnt += 1
        else:
            hist_mean = 0.9 * np.mean(self.y_net[-1 * self.hist_avrglen:])
            self.y_net.append(hist_mean)
        ##################################################################################
        # the following is a temporary fix for demo experience. should modify in the future
        if self.demo_fix:
            if self.y_net[-1] > 5000000:
                self.y_net[-1] = 5000000 + randint(-500000, 10000)
        self.y_net = self.y_net[1:]  # Remove the first
        self.data_line_net.setData(self.x_net, self.y_net)  # Update the data.

    def switch_mode(self, event):
        ''' switch between large figuer and small figure. '''
        if self.zoom_mode == 'small':
            self.switch_axis('show')
            # self.opacityeffect.setOpacity(1)
            self.zoom_large_animation.start()
            self.zoom_mode = 'large'
            self.title_cpu.setVisible(True)
            self.title_net.setVisible(True)
        else:
            self.switch_axis('hide')
            self.title_cpu.setVisible(False)
            self.title_net.setVisible(False)
            # self.opacityeffect.setOpacity(0.3)
            self.zoom_small_animation.start()
            self.zoom_mode = 'small'

    def switch_axis(self, mode: str = 'show'):  # 'hide'
        if mode == 'show':
            self.qplot_cpu.showAxis('left')
            self.qplot_net.showAxis('left')
            self.qplot_cpu.showAxis('bottom')
            self.qplot_net.showAxis('bottom')
        else:
            self.qplot_cpu.hideAxis('left')
            self.qplot_net.hideAxis('left')
            self.qplot_cpu.hideAxis('bottom')
            self.qplot_net.hideAxis('bottom')


class fogContainerTrfcStat(MplCanvas):
    """ plot container traffic statistics for FOG demo"""
    colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'w']

    def __init__(self, trfc_stats, n_points=15, parent=None):
        '''
        trfc_stats: a list of multiprocessing.Value, in which each
        element coresponds to a container's current traffic bandwidth.
        '''
        super().__init__(parent=parent)
        self.trfc_stats = trfc_stats
        self.n_points = n_points
        self.n_lines = len(trfc_stats)
        self.fig.subplots_adjust(left=0.35)
        self.ax_checkbuttom = self.fig.add_axes([0.04, 0.2, 0.17, 0.5])
        self.compute_initial_figure()

    def compute_initial_figure(self):
        self.t = np.arange(0, self.n_points)
        self.alldata = []
        self.lines = []
        for i in range(self.n_lines):
            data = deque([0] * self.n_points, maxlen=self.n_points)
            ls = self.axes.plot(self.t, data, lw=1,
                                color=fogContainerTrfcStat.colors[i],
                                label=f'Container {i}')
            self.alldata.append(data)
            self.lines.append(ls[0])
        self.labels = [str(line.get_label()) for line in self.lines]
        self.visibility = [line.get_visible() for line in self.lines]
        self.checkbuttom = CheckButtons(self.ax_checkbuttom, self.labels, self.visibility)
        self.checkbuttom.on_clicked(self.checkbutton_func)
        self.axes.set_ylim(0, 810000)
        self.axes.legend(loc='upper right')  # 'lower right'
        self.axes.get_xaxis().set_ticks([])
        self.draw()

    def checkbutton_func(self, label):
        idx = self.labels.index(label)
        self.lines[idx].set_visible(not self.lines[idx].get_visible())
        self.draw()

    def update_figure(self):
        # self.axes.cla()
        for i in range(self.n_lines):
            self.alldata[i].append(self.trfc_stats[i].value)
            self.lines[i].set_ydata(self.alldata[i])
            # print(self.alldata[i])
        self.draw()


class SigWrapper(QObject):
    sgnl = pyqtSignal(str)
    sgnl_float = pyqtSignal(float)


class fhDemoPlot(MplCanvas):
    """update plots with new data from self.datadevice."""

    def __init__(self, *args, **kwargs):
        MplCanvas.__init__(self, *args, **kwargs)
        self.update_cnt = 0
        self.draw()
        self.sgnlwrapper = SigWrapper()
        self._equ_repeat_period = 1
        self._SUB_START = 20
        self._SUB_STOP = 35
        self._PLOT_INTERVAL = 300  # ms

    def compute_initial_figure(self):
        self.axes.plot([0] * 20, 'ro-')

    def send_evm_value(self, evm):
        self.sgnlwrapper.sgnl_float.emit(evm)

    def send_console_output(self, console_output):
        self.sgnlwrapper.sgnl.emit(console_output)

    def update_figure(self):
        if (self.update_cnt % self._equ_repeat_period) == 0:
            re_clbrt = True
        else:
            re_clbrt = False
        self.update_cnt = self.update_cnt + 1
        print('update figure: {}th time.'.format(self.update_cnt))
        evm = 1
        if (self.datadevice.open_state == 1):
            response = self.datadevice.query_bin('getdata 28000')
            self.send_console_output('getdata 28000')
            alldata = extract_samples_int(response)
            self.datadevice.dmt_demod.update(alldata, re_calibrate=re_clbrt)
            print('!!!!!!!!!!!{}'.format(self.datadevice.dmt_demod.symbols_iq_shaped.shape))
            cleanxy = channel_filter(self.datadevice.dmt_demod.symbols_iq_shaped,
                                     self._SUB_START, self._SUB_STOP)
            evm = self.datadevice.evm_func(cleanxy, self.datadevice.dmt_demod.qam_level)
        else:
            self.send_console_output('ERROR: data device not opend')
            # raise ValueError('data device has not been opend')
        self.axes.cla()
        self.axes.set_xlim(-1.4, 1.4)
        self.axes.set_ylim(-1.4, 1.4)
        scatter_x = cleanxy.real
        scatter_y = cleanxy.imag
        self.axes.scatter(scatter_x, scatter_y, s=5)
        self.send_console_output('EVM = {}%'.format(str(evm * 100)))
        self.send_evm_value(evm)
        self.draw()


class pon56gDemoMsePlot(MplCanvas):
    """ Plot MSE (mean square error) changing curve during NN training."""

    def __init__(self, *args, **kwargs):
        MplCanvas.__init__(self, *args, **kwargs)
        self.mse_hist = []
        self.axes.plot([], label='Mean Square Error')
        self.axes.legend(loc='upper center', shadow=True)  # fontsize='x-large'
        self.draw()

    def compute_initial_figure(self):
        self.axes.semilogy([0] * 20, 'ro-')

    def reset(self):
        self.mse_hist = []
        self.axes.cla()
        self.draw()

    def update_figure(self, mse):
        self.mse_hist.append(mse)
        self.axes.cla()
        self.axes.set_xlim(0, len(self.mse_hist))
        # self.axes.set_ylim(bottom=0.001)
        self.axes.grid(True, which='both')
        self.axes.fill_between(np.arange(len(self.mse_hist)), self.mse_hist,
                               facecolor='blue', alpha=0.7, label='Learning process (MSE)')
        self.axes.legend(loc='upper center', shadow=True)  # fontsize='x-large'
        self.axes.set_yscale('log')
        self.draw()


class pon56gDemoBerPlot(MplCanvas):
    """update BER plot, with new data from self.datadevice."""

    def __init__(self, *args, **kwargs):
        MplCanvas.__init__(self, *args, **kwargs)
        # self.datadevice.open_device()
        # timer = QtCore.QTimer(self)
        # timer.timeout.connect(self.update_figure)
        # timer.start(_PLOT_INTERVAL)
        self.update_cnt = 0
        self.ber_hist = []
        self.draw()
        self.sgnlwrapper = SigWrapper()
        self.plot2Console = self.sgnlwrapper.sgnl
        self.plot2Meter = self.sgnlwrapper.sgnl_float

    def reset(self):
        self.ber_hist = []
        self.axes.cla()
        self.draw()

    def compute_initial_figure(self):
        self.axes.plot([0] * 20, 'ro-')

    def send_meter_value(self, evm):
        self.sgnlwrapper.sgnl_float.emit(evm)

    def send_console_output(self, console_output):
        self.sgnlwrapper.sgnl.emit(console_output)

    def plotDraw(self, ber_base, ber_jitter):
        ber = ber_base + ber_jitter
        self.ber_hist.append(ber)
        if len(self.ber_hist) > 15:
            self.ber_hist.pop(0)
        self.axes.cla()
        # self.axes.set_xlim(0, 15)
        self.axes.set_ylim(top=1, bottom=0.000006)
        self.axes.grid(True, which='major')
        self.axes.semilogy(np.arange(len(self.ber_hist)), self.ber_hist,
                           linewidth=1, marker='o', linestyle='-', color='r',
                           markersize=3, label='Bit Error Rate')
        self.axes.legend(shadow=True)  # loc='upper center', fontsize='x-large'
        self.draw()

        self.update_cnt = self.update_cnt + 1
        print('update figure: {}th time.'.format(self.update_cnt))
        if (self.datadevice.open_state == 1):
            # response = self.datadevice.query_bin('getFrame 786432')
            # alldata = extract_samples_float(response)
            if (self.update_cnt % 2) == 0:
                pad = '..................'
            else:
                pad = ''
            self.send_console_output(
                'update figure: {}th time. BER={:.2E}{}\ngetFrame 786432'.format(self.update_cnt, ber, pad))
        else:
            self.send_console_output('ERROR: data device not opend')
            # raise ValueError('data device has not been opend')

        expectedGbps = self.datadevice.calcEexpectedGbps(ber)
        # print('algo state:{}'.format(self.datadevice.algo_state))
        if self.datadevice.algo_state == self.datadevice.TranSit:
            pass
        else:
            self.send_meter_value(expectedGbps)

    def update_figure(self):
        response = self.datadevice.query_bin('getSigP 1')
        if (len(response) != 1):
            sig_p = 0
        else:
            sig_p = int(np.array(response, dtype='int8')[0])
            print('mean signal amplitude: {}'.format(sig_p))

        if self.datadevice.algo_state == self.datadevice.Init:
            pass

        elif self.datadevice.algo_state == self.datadevice.NoNN:
            if sig_p > 2:  # make sure there is optical signal received
                ber_base = 0.25
            else:
                ber_base = 0.5
            ber_jitter = np.random.randn() / 25
            self.plotDraw(ber_base, ber_jitter)

        else:  # algo_state == YesNN or TranSit:
            if sig_p > 2:  # make sure there is optical signal received
                ber_base = 0.00082
            else:
                ber_base = 0.5
            ber_jitter = np.mean(np.random.randn(100) / 1000)
            self.plotDraw(ber_base, ber_jitter)
