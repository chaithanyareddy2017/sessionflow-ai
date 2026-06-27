import spotipy
from spotipy.oauth2 import SpotifyOAuth

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope="playlist-read-private"))

track = sp.track("0HsDFeWMvnM9rEyvB23RYF")
print("Preview URL:", track.get('preview_url'))
