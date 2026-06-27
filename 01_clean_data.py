import pandas as pd

# Load
df = pd.read_csv('data/dataset.csv')
print("Initial shape:", df.shape)

# Drop the stray index column
df = df.drop(columns=['Unnamed: 0'])

# Check nulls before dropping
print("\nNulls per column:")
print(df.isnull().sum()[df.isnull().sum() > 0])

# Drop rows with nulls in artists/album_name/track_name
df = df.dropna(subset=['artists', 'album_name', 'track_name'])
print("\nShape after dropping nulls:", df.shape)

# Investigate tempo == 0 (suspicious — real tracks don't have 0 BPM)
zero_tempo_count = (df['tempo'] == 0).sum()
print(f"\nRows with tempo == 0: {zero_tempo_count}")
print(f"As % of total: {zero_tempo_count / len(df) * 100:.2f}%")

# Drop tempo==0 rows — negligible volume (0.14%), likely undetectable-tempo instrumental/ambient tracks
df = df[df['tempo'] != 0]
print("\nFinal shape after dropping zero-tempo rows:", df.shape)

# Save cleaned data for the next step
df.to_csv('data/cleaned_tracks.csv', index=False)
print("Saved to data/cleaned_tracks.csv")


# Don't decide what to do with them yet — just look first
print("\nSample of tempo==0 rows:")
print(df[df['tempo'] == 0][['track_name', 'artists', 'tempo', 'energy', 'danceability']].head())