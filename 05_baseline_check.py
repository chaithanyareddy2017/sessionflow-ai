import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

X = np.load('data/X.npy')
y = np.load('data/y.npy')

X_last_track = X[:, -1, :5]
y_target = y[:, -1]

# Take ONLY the last track's features (position 19) for every session
X_last_track = X[:, -1, :5]   # exclude skipped (index 5) — same fairness rule as the LSTM's candidate input
y_target = y[:, -1]         # shape (5000,)

X_train, X_test, y_train, y_test = train_test_split(
    X_last_track, y_target, test_size=0.20, random_state=42
)

print("Train skip rate:", y_train.mean(), " Test skip rate:", y_test.mean())

clf = LogisticRegression()
clf.fit(X_train, y_train)

train_acc = clf.score(X_train, y_train)
test_acc = clf.score(X_test, y_test)

print(f"\nLogistic Regression Train Acc: {train_acc:.4f}")
print(f"Logistic Regression Test Acc:  {test_acc:.4f}")
print(f"\nBaseline ('always predict no-skip'): {1 - y_test.mean():.4f}")