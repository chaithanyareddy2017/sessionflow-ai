import numpy as np
import torch
import torch.nn as nn
from sklearn.model_selection import train_test_split

X = np.load('data/X.npy')  # shape (5000, 20, 5)
y = np.load('data/y.npy')  # shape (5000, 20)

# Split: first 19 tracks = history, last track = candidate
X_history = X[:, :19, :]          # shape (5000, 19, 6) -- includes skipped, correct for history
X_candidate = X[:, 19, :5]        # shape (5000, 5) -- EXCLUDES skipped (index 5) to prevent leaking the answer
y_target = y[:, -1]

print("X_history shape:", X_history.shape)
print("X_candidate shape:", X_candidate.shape)
print("y_target shape:", y_target.shape)

# Split into train/test — IMPORTANT: split all three together so rows stay aligned
Xh_train, Xh_test, Xc_train, Xc_test, y_train, y_test = train_test_split(
    X_history, X_candidate, y_target, test_size=0.20, random_state=42
)

print("\nXh_train:", Xh_train.shape, " Xc_train:", Xc_train.shape, " y_train:", y_train.shape)
print("Xh_test:", Xh_test.shape, " Xc_test:", Xc_test.shape, " y_test:", y_test.shape)

# Convert to tensors
Xh_train_t = torch.tensor(Xh_train, dtype=torch.float32)
Xc_train_t = torch.tensor(Xc_train, dtype=torch.float32)
y_train_t = torch.tensor(y_train, dtype=torch.float32)
Xh_test_t = torch.tensor(Xh_test, dtype=torch.float32)
Xc_test_t = torch.tensor(Xc_test, dtype=torch.float32)
y_test_t = torch.tensor(y_test, dtype=torch.float32)


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
print(model)

# Smoke test
sample_out = model(Xh_train_t[:4], Xc_train_t[:4])
print("\nSample output shape:", sample_out.shape)  # expect (4,)
print("Sample output values:", sample_out)

criterion = nn.BCEWithLogitsLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

EPOCHS = 100
best_test_acc = 0.0

for epoch in range(EPOCHS):
    model.train()
    optimizer.zero_grad()

    outputs = model(Xh_train_t, Xc_train_t)
    loss = criterion(outputs, y_train_t)

    loss.backward()
    optimizer.step()

    if epoch % 5 == 0:
        model.eval()
        with torch.no_grad():
            test_outputs = model(Xh_test_t, Xc_test_t)
            test_loss = criterion(test_outputs, y_test_t)
            test_preds = (torch.sigmoid(test_outputs) > 0.5).float()
            test_acc = (test_preds == y_test_t).float().mean().item()

        if test_acc > best_test_acc:
            best_test_acc = test_acc
            torch.save(model.state_dict(), 'data/best_lstm_v2.pt')

        print(f"Epoch {epoch:3d} | Train Loss: {loss.item():.4f} | Test Loss: {test_loss.item():.4f} | Test Acc: {test_acc:.4f}")

print(f"\nBest Test Acc: {best_test_acc:.4f}")
print("Compare to: Logistic Regression 0.5950, Baseline 0.5480")