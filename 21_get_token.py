from dotenv import load_dotenv
load_dotenv()

import spotipy
from spotipy.oauth2 import SpotifyOAuth

auth_manager = SpotifyOAuth(
    scope="streaming user-read-email user-read-private"
)

sp = spotipy.Spotify(auth_manager=auth_manager)

# This forces actual authentication (will open a browser the first time for this new scope)
sp.current_user()

# NOW the token should be cached
token_info = auth_manager.get_cached_token()
print("Access token:", token_info['access_token'])
print("Expires at:", token_info['expires_at'])
print("Scope:", token_info.get('scope'))