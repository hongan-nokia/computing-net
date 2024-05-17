# -*- coding: utf-8 -*-
"""
@Time: 5/17/2024 9:30 AM
@Author: Honggang Yuan
@Email: honggang.yuan@nokia-sbell.com
Description: 
"""
from PyQt5.QtWidgets import QDialog, QLabel, QPushButton, QHBoxLayout, QVBoxLayout


class ExitDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        msg = QLabel('Are you sure?')
        self.setWindowTitle("Exit CPN")
        self.okButton = QPushButton("OK")
        self.cancelButton = QPushButton("Cancel")
        hbox = QHBoxLayout()
        hbox.addWidget(self.okButton)
        hbox.addWidget(self.cancelButton)
        vbox = QVBoxLayout()
        vbox.addWidget(msg)
        vbox.addStretch(1)
        vbox.addLayout(hbox)
        self.setLayout(vbox)
        self.okButton.clicked.connect(self.close)
        self.cancelButton.clicked.connect(self.close)
