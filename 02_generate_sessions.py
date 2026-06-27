import pandas as pd
import numpy as np

np.random.seed(42)

df = pd.read_csv('data/cleaned_tracks.csv')
print("Loaded:", df.shape)

NUM_SESSIONS = 5000
SESSION_LENGTH = 20


def generate_user_profile():
    energy_center = np.random.uniform(0.3, 0.9)
    energy_width = np.random.uniform(0.15, 0.3)
    tempo_center = np.random.uniform(80, 160)
    tempo_width = np.random.uniform(15, 30)
    return {
        'energy_min': max(0, energy_center - energy_width),
        'energy_max': min(1, energy_center + energy_width),
        'tempo_min': tempo_center - tempo_width,
        'tempo_max': tempo_center + tempo_width,
    }


def calculate_skip_probability(track_energy, track_tempo, user_profile, skip_streak):
    """
    skip_streak = number of consecutive tracks skipped immediately before this one.
    Adds momentum: the more skips in a row, the more likely the next skip too.
    """
    if track_energy < user_profile['energy_min']:
        energy_dist = user_profile['energy_min'] - track_energy
    elif track_energy > user_profile['energy_max']:
        energy_dist = track_energy - user_profile['energy_max']
    else:
        energy_dist = 0

    if track_tempo < user_profile['tempo_min']:
        tempo_dist = (user_profile['tempo_min'] - track_tempo) / 50
    elif track_tempo > user_profile['tempo_max']:
        tempo_dist = (track_tempo - user_profile['tempo_max']) / 50
    else:
        tempo_dist = 0

    mismatch = energy_dist + tempo_dist

    # Momentum term: each consecutive prior skip adds to the probability directly.
    # This is the ONLY thing that gives the LSTM's history-reading an actual edge over LR,
    # since LR never sees skip_streak (it only sees the candidate track's own features).
    momentum_boost = min(skip_streak * 0.08, 0.25)  # capped — momentum nudges, never guarantees

    base_skip_rate = 0.05
    skip_prob = base_skip_rate + mismatch * 1.5 + momentum_boost
    skip_prob = min(skip_prob, 0.97)

    return skip_prob


def decide_skip(skip_prob):
    """
    Reduce pure randomness: make the extremes near-deterministic,
    only flip a coin in the genuinely ambiguous middle band.
    This raises the theoretical accuracy ceiling for ANY model.
    """
    if skip_prob >= 0.75:
        return 1
    elif skip_prob <= 0.20:
        return 0
    else:
        return 1 if np.random.rand() < skip_prob else 0


# Sanity check
test_user = generate_user_profile()
print("\nTest user profile:", test_user)
print("No streak, perfect match:", calculate_skip_probability(
    (test_user['energy_min'] + test_user['energy_max']) / 2,
    (test_user['tempo_min'] + test_user['tempo_max']) / 2,
    test_user, skip_streak=0))
print("3-skip streak, perfect match:", calculate_skip_probability(
    (test_user['energy_min'] + test_user['energy_max']) / 2,
    (test_user['tempo_min'] + test_user['tempo_max']) / 2,
    test_user, skip_streak=3))

# Full generation
all_session_rows = []

for session_id in range(NUM_SESSIONS):
    user_profile = generate_user_profile()
    session_tracks = df.sample(SESSION_LENGTH).reset_index(drop=True)

    skip_streak = 0
    for position in range(SESSION_LENGTH):
        track = session_tracks.iloc[position]
        skip_prob = calculate_skip_probability(
            track['energy'], track['tempo'], user_profile, skip_streak
        )
        skipped = decide_skip(skip_prob)

        if skipped == 1:
            skip_streak += 1
        else:
            skip_streak = 0

        all_session_rows.append({
            'session_id': session_id,
            'position': position,
            'track_id': track['track_id'],
            'track_name': track['track_name'],
            'energy': track['energy'],
            'tempo': track['tempo'],
            'danceability': track['danceability'],
            'valence': track['valence'],
            'loudness': track['loudness'],
            'skip_prob': skip_prob,
            'skipped': skipped,
        })

    if session_id % 1000 == 0:
        print(f"Generated {session_id} sessions...")

sessions_df = pd.DataFrame(all_session_rows)
print("\nFinal shape:", sessions_df.shape)
print("Overall skip rate:", sessions_df['skipped'].mean())

sessions_df.to_csv('data/synthetic_sessions.csv', index=False)
print("Saved to data/synthetic_sessions.csv")

print("\nskip_prob distribution:")
print(sessions_df['skip_prob'].describe())