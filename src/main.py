import sys
import os
import spotipy

from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtGui import QIcon
from PyQt6.uic import loadUi
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

load_dotenv
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

# Window class
class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        # Load the UI file, Center window, Rename window, Set window logo
        loadUi("src/ui/main_window.ui", self)
        self.setCentralWidget(self.centralwidget)
        self.setWindowTitle("Spotify Video Sync")
        self.setWindowIcon(QIcon("resources/logo_large.png"))

        # Connect button to function
        self.fetchButton.clicked.connect(self.fetch_spotify_data)

        self.sp_oauth = SpotifyOAuth(
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
            redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
            scope="user-read-currently-playing"
        )

    # Function for button click
    def fetch_spotify_data(self):
        print("Fetching Spotify data . . .")

# Start application
app = QApplication(sys.argv)
window = Window()
window.show()
sys.exit(app.exec())
