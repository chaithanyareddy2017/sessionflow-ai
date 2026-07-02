import streamlit as st
import base64
import streamlit.components.v1 as components

from dotenv import load_dotenv
load_dotenv()


import requests

API_BASE = "http://127.0.0.1:8000"

if 'session_id' not in st.session_state:
    st.session_state.session_id = "streamlit_session_1"
    try:
        requests.post(f"{API_BASE}/session/start", params={"session_id": st.session_state.session_id})
    except Exception as e:
        st.error(f"Could not connect to backend: {e}")

import pandas as pd

@st.cache_data
def load_demo_tracks():
    df = pd.read_csv('data/cleaned_tracks.csv')
    # Sample 30 random tracks once, reused for this demo session
    return df.sample(30, random_state=1).reset_index(drop=True)

@st.cache_data
def get_album_art(track_id):
    try:
        track = sp.track(track_id)
        images = track['album']['images']
        return images[1]['url'] if len(images) > 1 else images[0]['url']  # medium size (300px)
    except Exception:
        return None  # fallback to gradient if lookup fails



demo_tracks = load_demo_tracks()


if 'played_history' not in st.session_state:
    # Start with your original 5 demo tracks
    st.session_state.played_history = []
    for i in range(5):
        track = demo_tracks.iloc[i]
        st.session_state.played_history.append({
            "track_id": track['track_id'],
            "track_name": track['track_name'],
            "artists": track['artists'],
            "energy": track['energy'],
            "tempo": track['tempo'],
            "danceability": track['danceability'],
            "valence": track['valence'],
            "loudness": track['loudness'],
            "art_url": get_album_art(track['track_id']),  # fetch once at init
        })

if 'current_playing' not in st.session_state:
    st.session_state.current_playing = st.session_state.played_history[0]

def play_random_next_track():
    response = requests.get(f"{API_BASE}/random_track")
    new_track = response.json()
    new_track['art_url'] = get_album_art(new_track['track_id'])
    st.session_state.played_history.insert(0, new_track)
    if len(st.session_state.played_history) > 5:
        st.session_state.played_history = st.session_state.played_history[:5]
    st.session_state.current_playing = new_track
    st.session_state.trigger_play_uri = f"spotify:track:{new_track['track_id']}"
    


import spotipy
from spotipy.oauth2 import SpotifyOAuth

@st.cache_resource
def get_spotify_client():
    return spotipy.Spotify(auth_manager=SpotifyOAuth(scope="playlist-read-private"))

sp = get_spotify_client()



def load_icon_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

icon_b64 = load_icon_b64("assets/favicon_64.png")
logo_b64 = load_icon_b64("assets/logo_128.png")

st.set_page_config(
    page_title="SessionFlow AI",
    page_icon=f"data:image/png;base64,{icon_b64}",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------- CSS ----------
st.markdown("""
<style>
    .stApp {
        background-color: #ffffff;
    }
    #MainMenu, header, footer {visibility: hidden;}

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1rem;
        max-width: 1100px;
    }

    .panel-title {
        font-family: 'Georgia', serif;
        font-size: 1.05rem;
        font-weight: 700;
        letter-spacing: 0.5px;
        color: #1a1a2e;
        margin-bottom: 1rem;
    }

    .track-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 10px 14px;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }

    .track-thumb {
        width: 46px;
        height: 46px;
        border-radius: 8px;
        flex-shrink: 0;
        background-size: cover;
        background-position: center;
    }

    .track-info {
        flex-grow: 1;
    }

    .track-name {
        font-weight: 600;
        font-size: 0.85rem;
        color: #1a1a2e;
        margin: 0;
    }

    .track-artist {
        font-size: 0.75rem;
        color: #555;
        margin: 0;
    }

    .track-tags {
        display: flex;
        gap: 6px;
        margin-top: 4px;
    }

    .tag {
        font-size: 0.65rem;
        padding: 2px 8px;
        border-radius: 20px;
        font-weight: 600;
    }

    .tag-bpm {
        background-color: #e8e2f7;
        color: #5b3fa0;
    }

    .tag-high { background-color: #fde2e2; color: #c0392b; }
    .tag-veryhigh { background-color: #fcdada; color: #9c2424; }
    .tag-medium { background-color: #fff1cf; color: #a3760b; }
    .tag-low { background-color: #dceefc; color: #2471a3; }

    .track-time {
        font-size: 0.7rem;
        color: #999;
        white-space: nowrap;
    }

    /* Right panel: now playing card */
    .now-playing-card {
        background: linear-gradient(135deg, #e9d8fd 0%, #d6c2f5 100%);
        border-radius: 18px;
        padding: 18px;
        box-shadow: 0 0 25px rgba(155, 109, 230, 0.35);
        margin-bottom: 16px;
    }

    .now-playing-label {
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 1px;
        color: #4a3a73;
        margin-bottom: 10px;
    }

    .album-art {
        width: 100%;
        max-width: 220px;
        margin: 0 auto;
        display: block;
        border-radius: 10px;
        aspect-ratio: 1/1;
        background: radial-gradient(circle at 30% 30%, #ff8a4c, #2b1810 70%);
        position: relative;
        overflow: hidden;
    }

    .album-text-top {
        position: absolute;
        top: 8px; left: 8px;
        font-size: 0.6rem;
        color: #fff;
        font-weight: 600;
        letter-spacing: 1px;
        opacity: 0.85;
    }
    .album-text-bottom {
        position: absolute;
        bottom: 8px; left: 8px;
        font-size: 0.6rem;
        color: #fff;
        font-weight: 600;
        letter-spacing: 1px;
        opacity: 0.85;
    }

    .player-controls {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 22px;
        margin-top: 14px;
    }

    .ctrl-btn {
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .play-btn {
        background-color: #fdf3e3;
        border-radius: 50%;
        width: 42px;
        height: 42px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
        box-shadow: 0 2px 6px rgba(0,0,0,0.15);
    }

    .progress-track {
        background-color: rgba(255,255,255,0.5);
        border-radius: 10px;
        height: 4px;
        margin-top: 12px;
        overflow: hidden;
    }
    .progress-fill {
        background-color: #4a3a73;
        height: 100%;
        width: 35%;
        border-radius: 10px;
    }

    /* Prediction metrics card */
    .metrics-card {
        background-color: #f0eafb;
        border-radius: 18px;
        padding: 20px;
    }

    .metrics-title {
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 1px;
        color: #4a3a73;
        margin-bottom: 14px;
    }

    .metrics-row {
        display: flex;
        align-items: center;
        gap: 20px;
    }

    .skip-prob-text {
        font-size: 0.65rem;
        color: #6b5a8f;
        text-align: center;
        margin-top: 4px;
        line-height: 1.2;
    }

    .metrics-detail {
        flex-grow: 1;
        font-size: 0.75rem;
        color: #333;
        line-height: 1.5;
    }

    .metrics-detail b {
        color: #1a1a2e;
    }

    .footer-note {
        text-align: center;
        font-size: 0.65rem;
        color: #aaa;
        margin-top: 10px;
    }

    /* Header */
    .app-header {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 14px 4px 18px 4px;
        border-bottom: 1px solid #eee;
        margin-bottom: 22px;
    }
    .app-header .logo-dot {
        width: 34px;
        height: 34px;
        border-radius: 9px;
        box-shadow: 0 2px 6px rgba(74, 58, 115, 0.35);
    }
    .app-header .app-title {
        font-family: Georgia, serif;
        font-size: 1.3rem;
        font-weight: 700;
        color: #1a1a2e;
        letter-spacing: 0.3px;
    }
    .app-header .app-subtitle {
        font-size: 0.7rem;
        color: #999;
        margin-left: 4px;
    }

    /* Footer with gradient heart */
    .app-footer {
        text-align: center;
        margin-top: 28px;
        padding-top: 16px;
        border-top: 1px solid #eee;
        font-size: 1.2rem;
        color: #999;
    }
    .gradient-heart {
        display: inline-block;
        font-size: 1rem;
        background: linear-gradient(135deg, #ff6f91, #8e6fd9, #4a3a73);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        vertical-align: middle;
    }
</style>
""", unsafe_allow_html=True)

# ---------- Header ----------
st.markdown(f"""
<div class="app-header">
    <img class="logo-dot" src="data:image/png;base64,{logo_b64}" />
    <div class="app-title">SessionFlow AI</div>
</div>
""", unsafe_allow_html=True)

# ---------- Dummy Data ----------
recently_played = []
for i in range(5):
    track = demo_tracks.iloc[i]
    energy_level = "High Energy" if track['energy'] > 0.66 else "Medium Energy" if track['energy'] > 0.33 else "Low Energy"
    tag_class = "tag-high" if track['energy'] > 0.66 else "tag-medium" if track['energy'] > 0.33 else "tag-low"

    art_url = get_album_art(track['track_id'])

    recently_played.append({
        "name": track['track_name'],
        "artist": track['artists'],
        "time": f"{(i+1)*5} min ago",
        "bpm": round(track['tempo']),
        "energy": energy_level,
        "tag_class": tag_class,
        "art_url": art_url,
    })

# Use the 6th demo track as the "candidate" (next track to predict)
current = st.session_state.current_playing

try:
    response = requests.post(
        f"{API_BASE}/predict_from_session",
        params={"session_id": st.session_state.session_id},
        json={
            "energy": current['energy'],
            "tempo": current['tempo'],
            "danceability": current['danceability'],
            "valence": current['valence'],
            "loudness": current['loudness'],
        }
    )
    result = response.json()
    skip_probability = round(result.get('skip_probability', 0) * 100)
except Exception as e:
    skip_probability = 0
    st.error(f"Prediction failed: {e}")




# ---------- Layout ----------
left_col, right_col = st.columns([1, 1], gap="medium")

with left_col:
    st.markdown("""
    <style>
       div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stMarkdown"] .panel-title) {
        background-color: #fdf3e3;
        border-radius: 18px;
        padding: 20px;
    }
    </style>
    <div class="left-panel-wrap-inner">
    """, unsafe_allow_html=True)

    st.markdown('<div class="panel-title">RECENTLY PLAYED</div>', unsafe_allow_html=True)

    for idx, t in enumerate(st.session_state.played_history):
        col_art, col_info, col_btn = st.columns([1, 4, 1])
        with col_art:
            art = t.get('art_url')
            if art:
                st.image(art, width=46)
        with col_info:
            st.markdown(
                f"<span style='color:#1a1a2e; font-weight:600;'>{t['track_name']}</span><br>"
                f"<span style='color:#555; font-size:0.8rem;'>{t['artists']}</span>",
                unsafe_allow_html=True
            )
            if st.button("▶", key=f"play_{idx}_{t['track_id']}"):
             # Push everything played so far (before this click) into Redis as session history
               for hist_track in st.session_state.played_history[:idx]:
                 requests.post(
                  f"{API_BASE}/session/{st.session_state.session_id}/add_track",
                    json={
                   "energy": hist_track['energy'],
                   "tempo": hist_track['tempo'],
                   "danceability": hist_track['danceability'],
                   "valence": hist_track['valence'],
                   "loudness": hist_track['loudness'],
                   "skipped": 0,  # we don't actually know if these were skipped; assume played for now
                   }
                )

                 st.session_state.current_playing = t
                 st.session_state.trigger_play_uri = f"spotify:track:{t['track_id']}"
                 st.rerun()

    

with right_col:
    st.markdown('<div class="panel-title">NEXT TRACK PREDICTION</div>', unsafe_allow_html=True)

    current = st.session_state.current_playing
    current_art = get_album_art(current['track_id']) or ''

    trigger_uri = st.session_state.get('trigger_play_uri', None)
    st.session_state.trigger_play_uri = None

    autoplay_js = ""
    if trigger_uri:
        autoplay_js = f"""
        setTimeout(() => {{
            fetch('http://127.0.0.1:8000/spotify/token')
                .then(res => res.json())
                .then(data => {{
                    if (deviceId) {{
                        fetch(`https://api.spotify.com/v1/me/player/play?device_id=${{deviceId}}`, {{
                            method: 'PUT',
                            headers: {{
                                'Authorization': 'Bearer ' + data.access_token,
                                'Content-Type': 'application/json'
                            }},
                            body: JSON.stringify({{ uris: ['{trigger_uri}'] }})
                        }});
                    }}
                }});
        }}, 1500);
        """

    combined_player_html = f"""
    <div style="font-family: Arial, sans-serif;">
        <div style="display:flex; align-items:center; gap:12px; padding:10px; background:#f0eafb; border-radius:10px; margin-bottom:12px;">
            <img src="{current_art}" style="width:60px;height:60px;border-radius:8px;object-fit:cover;" onerror="this.style.display='none'">
            <div>
                <div style="font-weight:bold; font-size:0.95rem;">{current['track_name']}</div>
                <div style="font-size:0.8rem; color:#666;">{current['artists']}</div>
            </div>
        </div>

        <div id="spotify-status" style="font-size: 0.85rem; color: #4a3a73; padding: 8px 0;">
            Loading Spotify player...
        </div>
        <button id="activateBtn" disabled style="
            font-size: 0.85rem; padding: 8px 16px; border-radius: 8px; border: none;
            background: #4a3a73; color: white; cursor: pointer; margin-bottom: 8px;">
            Activate Player
        </button>
        <div>
            <button id="prevBtn" disabled>⏮</button>
            <button id="playPauseBtn" disabled>⏯</button>
            <button id="nextBtn" disabled>⏭</button>
        </div>
    </div>

    <script src="https://sdk.scdn.co/spotify-player.js"></script>
    <script>
        let player = null;
        let deviceId = null;

        window.onSpotifyWebPlaybackSDKReady = () => {{
            document.getElementById('spotify-status').innerText = "Fetching token...";

            fetch('http://127.0.0.1:8000/spotify/token')
                .then(res => res.json())
                .then(data => {{
                    const token = data.access_token;
                    if (!token) {{
                        document.getElementById('spotify-status').innerText = "No token received.";
                        return;
                    }}

                    player = new Spotify.Player({{
                        name: 'SessionFlow AI Player',
                        getOAuthToken: cb => {{ cb(token); }},
                        volume: 0.5
                    }});

                    player.addListener('ready', ({{ device_id }}) => {{
                        deviceId = device_id;
                        document.getElementById('spotify-status').innerText =
                            "Ready. Click Activate, then click a track on the left.";
                        document.getElementById('activateBtn').disabled = false;
                        {autoplay_js}
                    }});

                    player.addListener('player_state_changed', (state) => {{
                        if (!state) return;
                        const track = state.track_window.current_track;
                        document.getElementById('spotify-status').innerText =
                            track.name + " — " + track.artists.map(a => a.name).join(', ') +
                            (state.paused ? " (paused)" : " (playing)");
                        document.getElementById('prevBtn').disabled = false;
                        document.getElementById('playPauseBtn').disabled = false;
                        document.getElementById('nextBtn').disabled = false;
                    }});

                    player.addListener('authentication_error', ({{ message }}) => {{
                        document.getElementById('spotify-status').innerText = "Auth error: " + message;
                    }});

                    player.addListener('account_error', ({{ message }}) => {{
                        document.getElementById('spotify-status').innerText = "Account error: " + message;
                    }});

                    player.connect();
                }});
        }};

        document.getElementById('activateBtn').onclick = () => {{
            if (player) {{
                player.activateElement();
                document.getElementById('spotify-status').innerText = "Activated!";
            }}
        }};

        document.getElementById('prevBtn').onclick = () => {{ if (player) player.previousTrack(); }};
        document.getElementById('playPauseBtn').onclick = () => {{ if (player) player.togglePlay(); }};
        document.getElementById('nextBtn').onclick = () => {{ if (player) player.nextTrack(); }};
    </script>
    """

    components.html(combined_player_html, height=280, scrolling=True)


    if st.button("⏭ Next Random Track", key="next_random_btn"):
        play_random_next_track()
        st.rerun()




    radius = 54
    circumference = 2 * 3.14159 * radius
    filled = circumference * (skip_probability / 100)
    remaining = circumference - filled

    donut_svg = (
        f'<svg width="130" height="130" viewBox="0 0 130 130">'
        f'<circle cx="65" cy="65" r="{radius}" fill="none" stroke="#e3d9f7" stroke-width="12"></circle>'
        f'<circle cx="65" cy="65" r="{radius}" fill="none" stroke="#4a3a73" stroke-width="12" '
        f'stroke-dasharray="{filled:.1f} {remaining:.1f}" stroke-linecap="round" '
        f'transform="rotate(-90 65 65)"></circle>'
        f'<text x="65" y="60" text-anchor="middle" font-size="26" font-weight="700" fill="#1a1a2e" font-family="Georgia, serif">{skip_probability}%</text>'
        f'<text x="65" y="80" text-anchor="middle" font-size="9" fill="#6b5a8f" font-family="Arial">PROBABILITY</text>'
        f'<text x="65" y="91" text-anchor="middle" font-size="9" fill="#6b5a8f" font-family="Arial">OF SKIP</text>'
        f'</svg>'
    )

    metrics_card_html = (
        '<div class="metrics-card">'
        '<div class="metrics-title">PREDICTION METRICS</div>'
        '<div class="metrics-row">'
        f'<div>{donut_svg}</div>'
        '<div class="metrics-detail">'
        f"<b>Last Action:</b><br>User skipped '{last_skipped_track}' ({last_skip_reason})<br><br>"
        f'<b>User Genre Preference:</b><br>{user_genre_pref}<br><br>'
        f'<b>Model Confidence:</b><br>{model_confidence}%'
        '</div>'
        '</div>'
        '</div>'
    )
    st.markdown(metrics_card_html, unsafe_allow_html=True)

st.markdown("""
<div class="app-footer">
    Built with <span class="gradient-heart">♥</span> by SessionFlow
</div>
""", unsafe_allow_html=True)