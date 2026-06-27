import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import StandardScaler
import joblib

# ---- Rebuild the exact same scaler used during training ----
# (must match 03_prepare_sequences.py exactly, or features won't be normalized
# the same way at inference time as they were during training)

df = pd.read_csv('data/synthetic_sessions.csv')
df = df.sort_values(['session_id', 'position'])

FEATURE_COLS = ['energy', 'tempo', 'danceability', 'valence', 'loudness', 'skipped']

scaler = StandardScaler()
scaler.fit(df[FEATURE_COLS])  # fit only — we already have df's original values, no need to transform here

joblib.dump(scaler, 'data/feature_scaler.pkl')
print("Saved scaler to data/feature_scaler.pkl")
print("Scaler means:", scaler.mean_)
print("Scaler scales:", scaler.scale_)


# ---- Re-define the exact model architecture (must match 06_train_lstm_v2.py exactly) ----
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


model = SkipLSTMv2()
model.load_state_dict(torch.load('data/best_lstm_v2.pt'))
model.eval()

print("\nModel loaded successfully from data/best_lstm_v2.pt")
print(model)

# ---- Smoke test: confirm the loaded model produces sane output ----
dummy_history = torch.zeros(1, 19, 6)
dummy_candidate = torch.zeros(1, 5)
with torch.no_grad():
    output = model(dummy_history, dummy_candidate)
    prob = torch.sigmoid(output)

print("\nSmoke test output (logit):", output.item())
print("Smoke test output (probability):", prob.item())