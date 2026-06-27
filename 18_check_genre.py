import spotipy
from spotipy.oauth2 import SpotifyOAuth

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope="playlist-read-private"))

artist = sp.artist("5jJrJU7VVmxQQLcLAmmxXc")  # Sai Abhyankkar's artist ID from your data
print("Keys:", list(artist.keys()))
print("Genres:", artist.get('genres', 'MISSING'))