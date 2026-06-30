from dotenv import load_dotenv
load_dotenv()
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyOAuth

df = pd.read_csv('data/cleaned_tracks.csv')
sample_track_id = df.sample(1, random_state=1).iloc[0]['track_id']
print("Testing track_id:", sample_track_id)

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope="streaming user-read-email user-read-private"))
track = sp.track(sample_track_id)
print("Name:", track['name'], '-', track['artists'][0]['name'])
print("URI:", track['uri'])