# -*- coding: utf-8 -*-
"""
@Time: 5/25/2024 8:53 PM
@Author: Honggang Yuan
@Email: honggang.yuan@nokia-sbell.com
Description: 
"""
from PyQt5 import QtWidgets, QtCore

from resourcevisiualize.resvisualize import data_visualize

if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    data_visual = data_visualize()
    data_visual.show()
    computingNetResMonTimer = QtCore.QTimer()
    computingNetResMonTimer.setInterval(3000)
    computingNetResMonTimer.timeout.connect(data_visual.updateNodesInfo)
    computingNetResMonTimer.start()
    # data_mon = repeatTimer(3, data_visual.updateNodesInfo, autostart=True)
    # data_mon.start()
    sys.exit(app.exec_())
