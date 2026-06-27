import spotipy
from spotipy.oauth2 import SpotifyOAuth

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope="playlist-read-private"))

# Try the batch endpoint instead of single-track
tracks = sp.tracks(["0HsDFeWMvnM9rEyvB23RYF"])
track = tracks['tracks'][0]

print("Keys:", list(track.keys()))
print("Popularity:", track.get('popularity', 'STILL MISSING'))