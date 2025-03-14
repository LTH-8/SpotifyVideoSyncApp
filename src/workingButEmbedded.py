import sys
import os
import spotipy
import threading
import webbrowser
import requests
import time

from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget
from PyQt6.QtGui import QIcon, QPixmap, QDesktopServices
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
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")  # Must be set in your .env file

spotify_token = None

def get_youtube_video_url(track, artist):
    """
    Searches YouTube for an embeddable official music video for the given track and artist.
    Tries multiple results and checks embeddability.
    Returns an embed URL with autoplay and muted parameters.
    """
    query = f"{track} {artist} official music video"
    search_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
         "part": "snippet",
         "q": query,
         "key": YOUTUBE_API_KEY,
         "maxResults": 3,  # Try up to 3 results
         "type": "video",
         "videoEmbeddable": "true",   # Only return videos that can be embedded
         "videoSyndicated": "true"      # Only return videos allowed outside YouTube
    }
    try:
        response = requests.get(search_url, params=params)
        response.raise_for_status()
        data = response.json()
        items = data.get("items", [])
        if not items:
            print("No search results for query:", query)
            return None

        # Iterate over search results and verify embeddability via the videos API.
        for item in items:
            try:
                video_id = item["id"]["videoId"]
                video_check_url = "https://www.googleapis.com/youtube/v3/videos"
                video_params = {
                    "part": "status",
                    "id": video_id,
                    "key": YOUTUBE_API_KEY
                }
                video_response = requests.get(video_check_url, params=video_params)
                video_response.raise_for_status()
                video_data = video_response.json()
                video_items = video_data.get("items", [])
                if video_items and video_items[0]["status"].get("embeddable", False):
                    # Return the embed URL (with autoplay and mute).
                    return f"https://www.youtube.com/embed/{video_id}?autoplay=1&mute=1"
                else:
                    print(f"Video {video_id} is not embeddable. Trying next result...")
            except Exception as e:
                print(f"Error checking status for a video: {e}")
                continue
    except Exception as e:
        print(f"Error fetching YouTube video: {e}")
    return None

class SpotifyAuthenticateServer:
    def __init__(self, sp_oauth):
        self.sp_oauth = sp_oauth    # Save Spotify OAuth object
        self.app = Flask(__name__)   # Create a Flask web server

        @self.app.route("/callback")
        def callback():
            # Get the 'code' parameter from the URL, and exchange for access token
            token_info = self.sp_oauth.get_access_token(request.args.get("code"), as_dict=True)
            if token_info and "access_token" in token_info:
                global spotify_token 
                spotify_token = token_info["access_token"]
                return "Login Successful"
            return "Authentication Failed"
    
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
        # Load UI file; ensure that videoBackgroundView is promoted to QWebEngineView
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
        self.pending_video_url = None
        self.last_video_url = None  # Store last attempted embed URL

        # Connect loadFinished signal to detect if the embed fails.
        self.videoBackgroundView.loadFinished.connect(self.on_video_load_finished)

        # QTimer to update the video safely on the main thread.
        self.video_update_timer = QTimer(self)
        self.video_update_timer.timeout.connect(self.check_video_update)
        self.video_update_timer.start(500)

        # Start a background thread to check for track changes.
        self.thread = threading.Thread(target=self.track_song_changes, daemon=True)
        self.thread.start()

    def spotify_login(self):
        global spotify_token
        auth_url = self.sp_oauth.get_authorize_url()
        self.login_prompt = LoginPrompt(auth_url)
        self.login_prompt.show()
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_spotify_token)
        self.timer.start(1000)

    def check_spotify_token(self):
        global spotify_token
        if spotify_token:
            print("Spotify Login Successful!")
            self.timer.stop()

    def track_song_changes(self):
        # Continuously check for song updates on a background thread.
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
        # Update song title and artist labels.
        try:
            self.songTitleLabel.setText(track_name)
            self.artistLabel.setText(artist_name)
        except Exception as e:
            print(f"Error updating labels: {e}")

        try:
            if hasattr(self, "albumArtLabel"):
                pixmap = QPixmap()
                pixmap.loadFromData(requests.get(album_cover_url).content)
                self.albumArtLabel.setPixmap(pixmap.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio))
        except Exception as e:
            print(f"Error updating album art: {e}")
        
        # Try to fetch the video URL and store it as pending.
        try:
            video_url = get_youtube_video_url(track_name, artist_name)
            if video_url:
                self.pending_video_url = video_url
                self.last_video_url = video_url
            else:
                print("YouTube video not found for", track_name, "-", artist_name)
        except Exception as e:
            print(f"Error getting YouTube video URL: {e}")

    def check_video_update(self):
        # This method runs on the main thread via QTimer.
        if self.pending_video_url:
            try:
                self.videoBackgroundView.setUrl(QUrl(self.pending_video_url))
                self.pending_video_url = None
            except Exception as e:
                print(f"Error updating video: {e}")

    def on_video_load_finished(self, success):
        # This slot is called when the videoBackgroundView finishes loading a URL.
        if not success:
            # If loading fails, use QDesktopServices to open the YouTube watch URL externally.
            print("Embedded video failed to load; opening externally.")
            try:
                # Extract video id from the last attempted embed URL.
                # Expected format: https://www.youtube.com/embed/{video_id}?...
                if self.last_video_url:
                    parts = self.last_video_url.split("/embed/")
                    if len(parts) > 1:
                        video_part = parts[1]
                        video_id = video_part.split("?")[0]
                        watch_url = f"https://www.youtube.com/watch?v={video_id}"
                        QDesktopServices.openUrl(QUrl(watch_url))
                        self.last_video_url = None
            except Exception as e:
                print(f"Error opening video externally: {e}")

# Start application
app = QApplication(sys.argv)
window = Window()
window.show()
sys.exit(app.exec())
