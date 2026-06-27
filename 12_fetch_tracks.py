import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    scope="playlist-read-private"
))

PLAYLIST_ID = "1Pkg8F05LwQFdVPos9Rusg"

results = sp.playlist_items(PLAYLIST_ID, limit=100)

tracks = []
for entry in results['items']:
    track = entry['item']
    if track is None:
        continue
    tracks.append({
        'track_name': track['name'],
        'artist': track['artists'][0]['name'],
        'spotify_id': track['id'],
    })

df = pd.DataFrame(tracks)
print("Total tracks fetched:", len(df))
print(df.head(10))

df.to_csv('data/my_playlist_tracks.csv', index=False)
print("\nSaved to data/my_playlist_tracks.csv")