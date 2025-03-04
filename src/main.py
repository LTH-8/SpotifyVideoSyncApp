import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt6.QtGui import QIcon

#opening window class
class Window(QWidget):
    def __init__(self):
        super().__init__()

        #rename opening window title and set app logo
        self.setWindowTitle("Spotify Video Sync")
        self.setWindowIcon(QIcon("resources/logo_large.png"))

    #function to resize and center the opening window
    def center_window(self):
        screen = QApplication.primaryScreen()
        self.move(self.frameGeometry().moveCenter(screen.availableGeometry.center()))


app = QApplication(sys.argv)
window = Window()
window.show()
sys.exit(app.exec())