import sys
import os
import spotipy
import threading
import webbrowser

from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget
from PyQt6.QtGui import QIcon
from PyQt6.uic import loadUi
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl

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

        # Connect button to function
        self.fetchButton.clicked.connect(self.fetch_spotify_data)
        self.loginButton.clicked.connect(self.spotify_login)
        self.cancelButton.clicked.connect(self.close)

        self.sp_oauth = SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=SPOTIFY_REDIRECT_URI,
            scope="user-read-currently-playing"
        )

    def spotify_login(self):
        global spotify_token
        auth_url = self.sp_oauth.get_authorize_url()

        self.login_prompt = LoginPrompt(auth_url)
        self.login_prompt.show()

        while not spotify_token:
            pass

    def fetch_spotify_data(self):
        try:
            track = spotipy.Spotify(auth_manager=self.sp_oauth).current_user_playing_track()

            if track and track.get('item'):
                print(f"Now playing: {track['item']['name']} - {track['item']['artists'][0]['name']}")
            else:
                print("No song currently playing")    

        except spotipy.exceptions.SpotifyException as e:
            print(f"Spotify API error: {e}")
        except Exception as e:
            print(f"Error fetching track: {e}")

# Start application
app = QApplication(sys.argv)
window = Window()
window.show()
sys.exit(app.exec())
