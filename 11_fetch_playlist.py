import spotipy
from spotipy.oauth2 import SpotifyOAuth

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    scope="playlist-read-private"
))

playlists = sp.current_user_playlists(limit=20)

print("Your playlists:")
for i, p in enumerate(playlists['items']):
    name = p['name'] if p['name'] else "(untitled)"
    track_count = p['items']['total']
    owner = p['owner']['display_name']
    print(f"{i}: {name} | owner: {owner} | tracks: {track_count} | id: {p['id']}")