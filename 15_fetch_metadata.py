import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import time

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope="playlist-read-private"))

df = pd.read_csv('data/my_playlist_tracks.csv')

popularity_list = []
genre_list = []

for idx, row in df.iterrows():
    track_id = row['spotify_id']
    try:
        track = sp.track(track_id)
        popularity = track['popularity']

        # Genre comes from the ARTIST, not the track directly
        artist_id = track['artists'][0]['id']
        artist = sp.artist(artist_id)
        genres = artist['genres']
        genre = genres[0] if genres else "unknown"

    except Exception as e:
        print(f"Failed on row {idx} ({row['track_name']}): {e}")
        popularity = None
        genre = "unknown"

    popularity_list.append(popularity)
    genre_list.append(genre)
    time.sleep(0.1)  # avoid hammering the API too fast

df['popularity'] = popularity_list
df['genre'] = genre_list

print(df.head(10))
df.to_csv('data/playlist_with_metadata.csv', index=False)
print("\nSaved to data/playlist_with_metadata.csv")