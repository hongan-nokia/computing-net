# -*- coding: utf-8 -*-
"""
@Time: 5/17/2024 9:59 AM
@Author: Honggang Yuan
@Email: honggang.yuan@nokia-sbell.com
Description: 
"""
from multiprocessing import Queue


def reverseQueue(queue: Queue):
    stack = []
    while not queue.empty():
        stack.append(queue.get())
    while stack:
        queue.put(stack.pop())
    return queue
