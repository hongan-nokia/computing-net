# -*- coding: utf-8 -*-
"""
@Time: 5/16/2024 2:32 PM
@Author: Honggang Yuan
@Email: honggang.yuan@nokia-sbell.com
Description: 
"""
from time import sleep

import psutil


def getCPU():
    cpu_list = psutil.cpu_percent(percpu=True, interval=0.5)
    average_cpu = round(sum(cpu_list) / 2, 2)
    cpu = str(average_cpu) + "%"
    return cpu


def getMemory():
    data = psutil.virtual_memory()
    memory = str(int(round(data.percent)))
    return memory


if __name__ == '__main__':
    # getTotalCPU()
    while 1:
        print(getCPU())
        sleep(1)
