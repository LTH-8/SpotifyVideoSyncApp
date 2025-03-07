import sys
import os
import spotipy
import threading
import webbrowser
import requests
import time

from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.uic import loadUi
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings, QWebEngineProfile
from PyQt6.QtCore import QUrl, Qt, QTimer

from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request


# Collect Spotify client info from .env
load_dotenv(dotenv_path="src/.env")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

spotify_token = None

class SpotifyAuthenticateServer:
    def __init__(self, sp_oauth):
        self.sp_oauth = sp_oauth    # Save Spotify OAuth object
        self.app = Flask(__name__)    # Create a Flask web server

        @self.app.route("/callback")
        def callback():
            # Get the 'code' parameter from the URL, and exchange for access tocken
            token_info = self.sp_oauth.get_access_token(request.args.get("code"), as_dict=True)
            if token_info and "access_token" in token_info:
                global spotify_token 
                spotify_token = token_info["access_token"]

                return "Login Successful"
            return "Authentication Failed"
    
    # Function to start the Flask server on port 8888 to prevent UI from stopping
    def run(self):
        threading.Thread(target=self.app.run, kwargs={"host": "127.0.0.1", "port": 8888}).start()


class LoginPrompt(QWidget):
    def __init__(self, auth_url, parent=None):
        super().__init__(parent)
        self.auth_url = auth_url

        self.setWindowTitle("Spotify Login")
        self.setGeometry(400, 250, 350, 200)

        layout = QVBoxLayout()
        label = QLabel("Login to Spotify")
        layout.addWidget(label)

        login_button = QPushButton("Login to Spotify")
        login_button.clicked.connect(self.open_login_window)
        layout.addWidget(login_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.close)
        layout.addWidget(cancel_button)

        self.setLayout(layout)
    
    def open_login_window(self):
        self.spotify_window = SpotifyLoginWindow(self.auth_url)
        self.spotify_window.show()

        while not spotify_token:
            pass

        print("Spotify login successful!")
        self.close()

class SpotifyLoginWindow(QMainWindow):
    def __init__(self, auth_url):
        super().__init__()

        self.setWindowTitle("Login to Spotify")
        self.setGeometry(300, 200, 900, 700) 

        self.browser = QWebEngineView()
        self.setCentralWidget(self.browser)
        self.browser.setUrl(QUrl(auth_url))  

    def closeEvent(self, event):
        global spotify_token
        if spotify_token:
            print("Login successful, closing window.")
        else:
            print("Login failed or canceled.")


class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        # Load the UI file, Center window, Rename window, Set window logo
        loadUi("src/ui/main_window.ui", self)
        self.setWindowTitle("Spotify Video Sync")
        self.setWindowIcon(QIcon("resources/logo_large.png"))

        self.sp_oauth = SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=SPOTIFY_REDIRECT_URI,
            scope="user-read-currently-playing"
        )

        self.current_track = None
        self.running = True

        self.thread = threading.Thread(target=self.track_song_changes, daemon=True)
        self.thread.start()

    def spotify_login(self):
        global spotify_token
        auth_url = self.sp_oauth.get_authorize_url()
        self.login_prompt = LoginPrompt(auth_url)
        self.login_prompt.show()

        self.timer = Qt.QTimer()
        self.timer.timeout.connect(self.check_spotify_token)
        self.timer.start(1000)

    def check_spotify_token(self):
        # Check for successful spotify login
        global spotify_token
        if spotify_token:
            print("Spotify Login Successful!")
            self.timer.stop()

    def track_song_changes(self):
        # Continuously check for song updates on a background thread
        while self.running:
            try:
                track = spotipy.Spotify(auth_manager=self.sp_oauth).current_user_playing_track()

                if track and track.get('item'):
                    track_name = track['item']['name']
                    artist_name = track['item']['artists'][0]['name']
                    album_cover_url = track['item']['album']['images'][0]['url']

                    new_track = f"{track_name} - {artist_name}"

                    if new_track != self.current_track:
                        self.current_track = new_track
                        print(f"Now Playing: {self.current_track}")

                        self.update_ui(track_name, artist_name, album_cover_url)
                        
                else:
                    self.songLabel.setText("No song currently playing")   
                    self.artistLabel.setText("") 

            except spotipy.exceptions.SpotifyException as e:
                print(f"Spotify API error: {e}")
            except Exception as e:
                print(f"Error fetching track: {e}")

                if "429" in str(e):
                    time.sleep(30)
                else:
                    time.sleep(2)
            
            time.sleep(2)

    def update_ui(self, track_name, artist_name, album_cover_url):
        # Updates the song and artist labels
        self.songTitleLabel.setText(track_name)
        self.artistLabel.setText(artist_name)

        if hasattr(self, "albumArtLabel"):
            pixmap = QPixmap()
            pixmap.loadFromData(requests.get(album_cover_url).content)
            self.albumArtLabel.setPixmap(pixmap.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio))     

# Start application
app = QApplication(sys.argv)
window = Window()
window.show()
sys.exit(app.exec())
