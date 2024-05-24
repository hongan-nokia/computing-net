from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt5.QtGui import QCursor
from PyQt5.QtCore import QTimer, Qt


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.label = QLabel(self)
        self.label.setGeometry(10, 10, 100, 20)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setStyleSheet("background-color: white;")

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_cursor_position)
        self.timer.start(100)  # update every 100ms

    def update_cursor_position(self):
        cursor_pos = QCursor.pos()
        self.label.setText(f"x: {cursor_pos.x()}, y: {cursor_pos.y()-25}")


if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
