import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope="playlist-read-private"))

track = sp.track("0HsDFeWMvnM9rEyvB23RYF")
print(json.dumps(track, indent=2)[:1500])