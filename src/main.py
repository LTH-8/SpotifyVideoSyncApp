import sys
import os
import spotipy
import threading
import requests
import subprocess
import time

from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget
from PyQt6.QtGui import QIcon, QPixmap, QDesktopServices
from PyQt6.uic import loadUi
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings, QWebEnginePage
from PyQt6.QtCore import QUrl, Qt, QTimer

from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request

# Load credentials from .env
load_dotenv(dotenv_path="src/.env")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")  # YouTube Data API key

spotify_token = None

def get_youtube_video_url(track, artist):
    """
    Searches YouTube for an embeddable official music video for the given track and artist.
    Instead of a standard YouTube embed URL, returns a CodePen-based embed URL,
    which uses CodePen's whitelisted domain.
    """
    query = f"{track} {artist} official music video"
    search_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
         "part": "snippet",
         "q": query,
         "key": YOUTUBE_API_KEY,
         "maxResults": 3,  # Try up to 3 results
         "type": "video",
         "videoEmbeddable": "true",
         "videoSyndicated": "true"
    }
    try:
        response = requests.get(search_url, params=params)
        response.raise_for_status()
        data = response.json()
        items = data.get("items", [])
        if not items:
            print("No search results for query:", query)
            return None

        # Iterate over results and verify embeddability.
        for item in items:
            try:
                video_id = item["id"]["videoId"]
                print("Found video ID:", video_id)
                video_check_url = "https://www.googleapis.com/youtube/v3/videos"
                video_params = {"part": "status", "id": video_id, "key": YOUTUBE_API_KEY}
                video_response = requests.get(video_check_url, params=video_params)
                video_response.raise_for_status()
                video_data = video_response.json()
                video_items = video_data.get("items", [])
                if video_items and video_items[0]["status"].get("embeddable", False):
                    if len(video_id) == 11:
                        # Build CodePen embed URL
                        return f"https://cdpn.io/pen/debug/oNPzxKo?v={video_id}&autoplay=1&mute=1&fs=1"
                    else:
                        print(f"Video ID '{video_id}' is not 11 characters long.")
                else:
                    print(f"Video {video_id} is not embeddable. Trying next result...")
            except Exception as e:
                print(f"Error checking video status: {e}")
                continue
    except Exception as e:
        print(f"Error fetching YouTube video: {e}")
    return None

def open_in_chrome_kiosk(video_id):
    """Open the YouTube watch URL in Google Chrome in kiosk (fullscreen) mode."""
    watch_url = f"https://www.youtube.com/watch?v={video_id}"
    print("Opening in Chrome kiosk mode:", watch_url)
    # Adjust the path to Chrome if necessary.
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    subprocess.Popen([chrome_path, "--kiosk", watch_url])

# --- Spotify authentication classes (unchanged) ---

class SpotifyAuthenticateServer:
    def __init__(self, sp_oauth):
        self.sp_oauth = sp_oauth
        self.app = Flask(__name__)
        @self.app.route("/callback")
        def callback():
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

# --- Main application window ---

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        # Adjust path: if main_window.ui is in "ui" folder under "src", use "ui/main_window.ui"
        # Here we assume main2.py is in src and ui folder is in src/ui/
        ui_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "ui", "main_window.ui")
        loadUi(ui_path, self)
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
        self.last_video_url = None  # Stores last attempted embed URL
        self.last_video_id = None   # Stores the plain YouTube video ID

        # Set up QWebEngineView: load our HTML which uses the CodePen embed
        self.videoBackgroundView.setPage(QWebEnginePage(self.videoBackgroundView))
        # Enable local content access
        self.videoBackgroundView.page().settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        self.videoBackgroundView.page().settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        
        # Instead of a file:// URL, you could serve via HTTP if needed.
        # Here, we'll assume youtube_player.html is in the same directory as main2.py.
        script_dir = os.path.dirname(os.path.realpath(__file__))
        html_path = os.path.join(script_dir, "youtube_player.html")
        print("Loading HTML from:", html_path)
        self.videoBackgroundView.load(QUrl.fromLocalFile(html_path))

        # Timer to update the video embed on the main thread.
        self.video_update_timer = QTimer(self)
        self.video_update_timer.timeout.connect(self.check_video_update)
        self.video_update_timer.start(500)

        # Timer to check for embed errors in JS (set in our HTML via window.videoError).
        self.js_error_timer = QTimer(self)
        self.js_error_timer.timeout.connect(self.check_for_js_errors)
        self.js_error_timer.start(1000)

        # Background thread to monitor Spotify track changes.
        self.thread = threading.Thread(target=self.track_song_changes, daemon=True)
        self.thread.start()

    def spotify_login(self):
        global spotify_token
        auth_url = self.sp_oauth.get_authorize_url()
        self.login_prompt = LoginPrompt(auth_url)
        self.login_prompt.show()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_spotify_token)
        self.timer.start(1000)

    def check_spotify_token(self):
        global spotify_token
        if spotify_token:
            print("Spotify Login Successful!")
            self.timer.stop()

    def track_song_changes(self):
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
            except Exception as e:
                print(f"Error fetching track: {e}")
                time.sleep(2)
            time.sleep(2)

    def update_ui(self, track_name, artist_name, album_cover_url):
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

        try:
            # Get the embed URL using our CodePen workaround.
            video_url = get_youtube_video_url(track_name, artist_name)
            if video_url:
                self.pending_video_url = video_url
                # Extract the plain YouTube video ID from the URL query parameter.
                # Our URL format is: https://cdpn.io/pen/debug/oNPzxKo?v=VIDEO_ID&...
                parts = video_url.split("v=")
                if len(parts) > 1:
                    self.last_video_id = parts[1].split("&")[0]
                print("Using video ID:", self.last_video_id)
            else:
                print("YouTube video not found for", track_name, "-", artist_name)
        except Exception as e:
            print(f"Error getting YouTube video URL: {e}")

    def check_video_update(self):
        if self.pending_video_url:
            print("Attempting to load video URL:", self.pending_video_url)
            self.videoBackgroundView.setUrl(QUrl(self.pending_video_url))
            self.pending_video_url = None

    def check_for_js_errors(self):
        # Check if our HTML set window.videoError
        js_code = "window.videoError || null;"
        self.videoBackgroundView.page().runJavaScript(js_code, self.handle_js_error)

    def handle_js_error(self, result):
        if result in [2, 101, 150]:
            print(f"Detected embed error code: {result}")
            self.videoBackgroundView.page().runJavaScript("window.videoError = null;")
            if self.last_video_id:
                print("Falling back: opening video externally in kiosk mode.")
                open_in_chrome_kiosk(self.last_video_id)
                self.last_video_id = None

# Main entry
app = QApplication(sys.argv)
window = Window()
window.show()
sys.exit(app.exec())
