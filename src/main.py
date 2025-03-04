import sys
import os

from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtGui import QIcon
from PyQt6.uic import loadUi
from dotenv import load_dotenv

load_dotenv
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

# Window class
class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        # Load the UI file
        loadUi("src/ui/main_window.ui", self)

        # Ensure central widget is set (needed for QMainWindow UIs)
        self.setCentralWidget(self.centralwidget)

        # Rename window title and set app logo
        self.setWindowTitle("Spotify Video Sync")
        self.setWindowIcon(QIcon("resources/logo_large.png"))

        # Connect button to function
        self.fetchButton.clicked.connect(self.fetch_spotify_data)

    # Function for button click
    def fetch_spotify_data(self):
        print("Fetching Spotify data . . .")

# Start application
app = QApplication(sys.argv)
window = Window()
window.show()
sys.exit(app.exec())
