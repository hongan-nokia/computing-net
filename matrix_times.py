# -*- coding: utf-8 -*-
"""
@Time: 5/31/2024 1:56 PM
@Author: Honggang Yuan
@Email: honggang.yuan@nokia-sbell.com
Description: 
"""
from time import sleep

import numpy as np


def matrix_util(dim):
    X = np.random.randn(dim, dim)
    Y = np.random.randn(dim, dim)
    Z = X.dot(Y)
    print(Z)


if __name__ == '__main__':
    while True:
        matrix_util(700)
        sleep(0.1)
