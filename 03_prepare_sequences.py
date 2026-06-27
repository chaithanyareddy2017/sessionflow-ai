import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

df = pd.read_csv('data/synthetic_sessions.csv')
print("Loaded:", df.shape)

df = df.sort_values(['session_id', 'position'])

FEATURE_COLS = ['energy', 'tempo', 'danceability', 'valence', 'loudness', 'skipped']
TARGET_COL = 'skipped'

grouped = df.groupby('session_id')

print("Number of sessions:", grouped.ngroups)
print("Tracks per session (should all be 20):")
print(df.groupby('session_id').size().describe())

# Scale features
# Save the original unscaled skipped column BEFORE scaling anything,
# since y must always be 0/1, never scaled.
df['skipped_original'] = df['skipped'].copy()


scaler = StandardScaler()
df[FEATURE_COLS] = scaler.fit_transform(df[FEATURE_COLS])

NUM_SESSIONS = grouped.ngroups
SEQ_LEN = 20
NUM_FEATURES = len(FEATURE_COLS)

X = np.zeros((NUM_SESSIONS, SEQ_LEN, NUM_FEATURES))
y = np.zeros((NUM_SESSIONS, SEQ_LEN))

# NOTE: grouped was created BEFORE scaling df in-place above.
# Re-create grouped AFTER scaling so X actually contains scaled values.
grouped = df.groupby('session_id')

for i, (session_id, session_df) in enumerate(grouped):
    session_df = session_df.sort_values('position')
    X[i] = session_df[FEATURE_COLS].values
    y[i] = session_df['skipped_original'].values

print("\nX shape:", X.shape)
print("y shape:", y.shape)

sample_session = df[df['session_id'] == 0].sort_values('position')
print("\nSession 0 original skipped values:", sample_session['skipped'].values)
print("Session 0 from X/y array skipped values:", y[0])


np.save('data/X.npy', X)
np.save('data/y.npy', y)
print("\nSaved X.npy and y.npy to data/")