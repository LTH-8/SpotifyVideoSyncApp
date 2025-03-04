import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt6.QtGui import QIcon

class Window(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Spotify Video Sync")
        self.setWindowIcon(QIcon("resources/logo.png"))


    def center_window(self):
        screen = QApplication.primaryScreen()
        self.move(self.frameGeometry().moveCenter(screen.availableGeometry.center()))


app = QApplication(sys.argv)
window = Window()
window.show()
sys.exit(app.exec())