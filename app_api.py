from dotenv import load_dotenv
load_dotenv()


from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import torch
import torch.nn as nn
import joblib
import numpy as np



import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

app = FastAPI(title="SessionFlow AI - Skip Predictor")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080", "http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# ---- Model definition (must match training exactly) ----
class SkipLSTMv2(nn.Module):
    def __init__(self, history_size=6, candidate_size=5, hidden_size=32, num_layers=1):
        super().__init__()
        self.lstm = nn.LSTM(history_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size + candidate_size, 1)

    def forward(self, history, candidate):
        lstm_out, (h_n, c_n) = self.lstm(history)
        history_summary = h_n[-1]
        combined = torch.cat([history_summary, candidate], dim=1)
        out = self.fc(combined)
        return out.squeeze(-1)

# ---- Load saved artifacts ONCE at startup, not per-request ----
model = SkipLSTMv2()
model.load_state_dict(torch.load('data/best_lstm_v2.pt'))
model.eval()

scaler = joblib.load('data/feature_scaler.pkl')

print("Model and scaler loaded successfully.")


# ---- Define what a request looks like ----
class HistoryTrack(BaseModel):
    energy: float
    tempo: float
    danceability: float
    valence: float
    loudness: float
    skipped: int  # 0 or 1 — whether this past track was skipped

class CandidateTrack(BaseModel):
    energy: float
    tempo: float
    danceability: float
    valence: float
    loudness: float

class PredictRequest(BaseModel):
    history: List[HistoryTrack]  # should be exactly 19 tracks
    candidate: CandidateTrack    # the 20th track we're predicting


@app.get("/")
def root():
    return {"status": "SessionFlow AI backend is running"}

MAX_HISTORY = 19

@app.post("/predict")
def predict_skip(request: PredictRequest):
    history_list = request.history

    actual_length = len(history_list)

    if actual_length == 0:
        return {"error": "history cannot be empty"}

    # Truncate: keep only the most recent MAX_HISTORY tracks if too many were sent
    if actual_length > MAX_HISTORY:
        history_list = history_list[-MAX_HISTORY:]

    history_raw = np.array([
        [t.energy, t.tempo, t.danceability, t.valence, t.loudness, t.skipped]
        for t in history_list
    ])

    # Pad: if fewer than MAX_HISTORY tracks, pad at the START with zeros
    # (so real history stays at the END, closest to the candidate prediction —
    # this matters because the LSTM reads left-to-right and the final hidden
    # state is most influenced by the most RECENT timesteps)
    current_length = history_raw.shape[0]
    if current_length < MAX_HISTORY:
        padding = np.zeros((MAX_HISTORY - current_length, 6))
        history_raw = np.vstack([padding, history_raw])

    was_padded = actual_length < MAX_HISTORY

    candidate_raw = np.array([[
        request.candidate.energy,
        request.candidate.tempo,
        request.candidate.danceability,
        request.candidate.valence,
        request.candidate.loudness,
    ]])

    history_scaled = scaler.transform(history_raw)

    candidate_padded = np.hstack([candidate_raw, np.zeros((1, 1))])
    candidate_scaled_full = scaler.transform(candidate_padded)
    candidate_scaled = candidate_scaled_full[:, :5]

    history_tensor = torch.tensor(history_scaled, dtype=torch.float32).unsqueeze(0)
    candidate_tensor = torch.tensor(candidate_scaled, dtype=torch.float32)

    with torch.no_grad():
        logit = model(history_tensor, candidate_tensor)
        probability = torch.sigmoid(logit).item()

    return {
        "skip_probability": round(probability, 4),
        "will_skip": probability > 0.5,
        "history_tracks_received": actual_length,
        "was_padded": was_padded,  # honest flag: caller should know if prediction is on thin data
    }

@app.post("/session/start")
def start_session(session_id: str):
    redis_client.delete(f"session:{session_id}")  # clear any old data with this ID
    redis_client.set(f"session:{session_id}", json.dumps([]))
    return {"status": "session started", "session_id": session_id}

@app.post("/session/{session_id}/add_track")
def add_track_to_session(session_id: str, track: HistoryTrack):
    existing = redis_client.get(f"session:{session_id}")
    history = json.loads(existing) if existing else []

    history.append(track.dict())

    # Keep only the most recent 19 (matches your model's expected history length)
    history = history[-19:]

    redis_client.set(f"session:{session_id}", json.dumps(history))
    return {"status": "track added", "history_length": len(history)}


@app.get("/session/{session_id}/history")
def get_session_history(session_id: str):
    existing = redis_client.get(f"session:{session_id}")
    history = json.loads(existing) if existing else []
    return {"session_id": session_id, "history": history}

@app.post("/predict_from_session")
def predict_from_session(session_id: str, candidate: CandidateTrack):
    existing = redis_client.get(f"session:{session_id}")
    history_data = json.loads(existing) if existing else []

    if len(history_data) == 0:
        return {"error": "no history found for this session_id"}

    history_list = [HistoryTrack(**item) for item in history_data]

    # Reuse the exact same logic as your original /predict endpoint
    actual_length = len(history_list)
    if actual_length > MAX_HISTORY:
        history_list = history_list[-MAX_HISTORY:]

    history_raw = np.array([
        [t.energy, t.tempo, t.danceability, t.valence, t.loudness, t.skipped]
        for t in history_list
    ])

    current_length = history_raw.shape[0]
    if current_length < MAX_HISTORY:
        padding = np.zeros((MAX_HISTORY - current_length, 6))
        history_raw = np.vstack([padding, history_raw])

    was_padded = actual_length < MAX_HISTORY

    candidate_raw = np.array([[candidate.energy, candidate.tempo, candidate.danceability, candidate.valence, candidate.loudness]])

    history_scaled = scaler.transform(history_raw)
    candidate_padded = np.hstack([candidate_raw, np.zeros((1, 1))])
    candidate_scaled_full = scaler.transform(candidate_padded)
    candidate_scaled = candidate_scaled_full[:, :5]

    history_tensor = torch.tensor(history_scaled, dtype=torch.float32).unsqueeze(0)
    candidate_tensor = torch.tensor(candidate_scaled, dtype=torch.float32)

    with torch.no_grad():
        logit = model(history_tensor, candidate_tensor)
        probability = torch.sigmoid(logit).item()

    return {
        "skip_probability": round(probability, 4),
        "will_skip": probability > 0.5,
        "history_tracks_used": actual_length,
        "was_padded": was_padded,
    }

from spotipy.oauth2 import SpotifyOAuth

spotify_auth_manager = SpotifyOAuth(scope="streaming user-read-email user-read-private")

@app.get("/spotify/token")
def get_spotify_token():
    token_info = spotify_auth_manager.get_cached_token()
    if not token_info:
        return {"error": "no cached token, run manual auth flow first"}

    # Refresh if expired
    if spotify_auth_manager.is_token_expired(token_info):
        token_info = spotify_auth_manager.refresh_access_token(token_info['refresh_token'])

    return {"access_token": token_info['access_token']}

@app.get("/random_track")
def get_random_track():
    import pandas as pd
    df = pd.read_csv('data/cleaned_tracks.csv')
    row = df.sample(1).iloc[0]
    return {
        "track_id": row['track_id'],
        "track_name": row['track_name'],
        "artists": row['artists'],
        "energy": float(row['energy']),
        "tempo": float(row['tempo']),
        "danceability": float(row['danceability']),
        "valence": float(row['valence']),
        "loudness": float(row['loudness']),
    }












