import pandas as pd

playlist_df = pd.read_csv('data/my_playlist_tracks.csv')
kaggle_df = pd.read_csv('data/cleaned_tracks.csv')

print("Playlist tracks:", len(playlist_df))
print("Kaggle tracks:", len(kaggle_df))

# Normalize names for matching: lowercase, strip whitespace
playlist_df['track_name_clean'] = playlist_df['track_name'].str.lower().str.strip()
playlist_df['artist_clean'] = playlist_df['artist'].str.lower().str.strip()

kaggle_df['track_name_clean'] = kaggle_df['track_name'].str.lower().str.strip()
kaggle_df['artist_clean'] = kaggle_df['artists'].str.lower().str.strip()

# Merge on cleaned track name + artist
matched = playlist_df.merge(
    kaggle_df,
    on=['track_name_clean', 'artist_clean'],
    how='inner',
    suffixes=('_playlist', '_kaggle')
)

print("\nMatched tracks:", len(matched))
print(matched[['track_name_playlist', 'artist_playlist', 'energy', 'tempo', 'danceability']].head(10))

matched.to_csv('data/matched_tracks.csv', index=False)
print("\nSaved to data/matched_tracks.csv")