import sys
import os
import spotipy
import threading
import webbrowser

from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtGui import QIcon
from PyQt6.uic import loadUi
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
        threading.Thread(target=self.app.run, kwargs={"port": 8888}).start()

    def spotify_login(self):
        self.run()    
        webbrowser.open(self.sp_oauth.get_authorize_url())    # Get Spotify's login URL and opens

        global spotify_token
        while not spotify_token:
            pass

        self.sp = spotipy.Spotify(auth=spotify_token)
        self.fetch_spotify_data()

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

    def fetch_spotify_data(self):
        try:
            track = spotipy.Spotify(auth_manager=self.sp_oauth).current_user_playing_track()

            if track and track.get('item'):
                track_name = track['item']['name']
                artist_name = track['item']['artists'][0]['name']
                print(f"Now playing: {track_name} - {artist_name}")
            else:
                print("No song currently playing")    
                
        except spotipy.exceptions.SpotifyException as e:
            print(f"Spotify Api error: {e}")
        except Exception as e:
            print(f"Error fetching track: {e}")

# Start application
app = QApplication(sys.argv)
window = Window()
window.show()
sys.exit(app.exec())
