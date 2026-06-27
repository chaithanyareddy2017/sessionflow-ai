import numpy as np
from sklearn.model_selection import train_test_split

X = np.load('data/X.npy')
y = np.load('data/y.npy')

print("X shape:", X.shape)  # (5000, 20, 5)
print("y shape:", y.shape)  # (5000, 20)

# We only care about predicting the LAST track's skip label,
# given the full 20-track sequence as input.
# Input: all 20 tracks (model sees the whole session including the last track's own features)
# Target: just the skip label of position 19 (the last track)
y_target = y[:, -1]  # shape (5000,)

print("y_target shape:", y_target.shape)
print("y_target skip rate:", y_target.mean())

X_train, X_test, y_train, y_test = train_test_split(
    X, y_target, test_size=0.20, random_state=42
)

print("\nX_train:", X_train.shape, " X_test:", X_test.shape)
print("y_train:", y_train.shape, " y_test:", y_test.shape)
print("Train skip rate:", y_train.mean(), " Test skip rate:", y_test.mean())

import torch
import torch.nn as nn

# Convert numpy arrays to torch tensors
X_train_t = torch.tensor(X_train, dtype=torch.float32)
y_train_t = torch.tensor(y_train, dtype=torch.float32)
X_test_t = torch.tensor(X_test, dtype=torch.float32)
y_test_t = torch.tensor(y_test, dtype=torch.float32)

print("Tensor shapes:", X_train_t.shape, y_train_t.shape)

class SkipLSTM(nn.Module):
    def __init__(self, input_size=5, hidden_size=32, num_layers=1):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True  # input shape: (batch, seq_len, features)
        )
        self.fc = nn.Linear(hidden_size, 1)  # output: 1 skip probability

    def forward(self, x):
        # x shape: (batch, seq_len=20, features=5)
        lstm_out, (h_n, c_n) = self.lstm(x)
        # h_n shape: (num_layers, batch, hidden_size) -- final hidden state
        last_hidden = h_n[-1]  # (batch, hidden_size) -- summary of the whole sequence
        out = self.fc(last_hidden)  # (batch, 1)
        return torch.sigmoid(out).squeeze(1)  # (batch,) -- probability between 0-1

model = SkipLSTM()
print(model)

# Quick sanity check: run one forward pass on a small batch, confirm output shape
test_batch = X_train_t[:4]  # first 4 sessions
test_output = model(test_batch)
print("\nTest output shape:", test_output.shape)  # expect (4,)
print("Test output values:", test_output)  # should be 4 numbers between 0-1, untrained so basically random

import torch
import torch.nn as nn

X_train_t = torch.tensor(X_train, dtype=torch.float32)
y_train_t = torch.tensor(y_train, dtype=torch.float32)
X_test_t = torch.tensor(X_test, dtype=torch.float32)
y_test_t = torch.tensor(y_test, dtype=torch.float32)

print("Tensor shapes:", X_train_t.shape, y_train_t.shape)

class SkipLSTM(nn.Module):
    def __init__(self, input_size=5, hidden_size=32, num_layers=1):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x):
        # x shape: (batch, seq_len, features)
        lstm_out, (h_n, c_n) = self.lstm(x)
        # h_n is the final hidden state — shape (num_layers, batch, hidden_size)
        last_hidden = h_n[-1]  # (batch, hidden_size)
        out = self.fc(last_hidden)  # (batch, 1)
        return out.squeeze(-1)  # (batch,)

model = SkipLSTM(hidden_size=64)
print(model)

# Quick smoke test — does a forward pass run without error?
sample_out = model(X_train_t[:4])
print("\nSample output shape:", sample_out.shape)  # expect (4,)
print("Sample output values:", sample_out)

# Loss function: binary cross-entropy with logits (since model outputs raw logits, not probabilities)
criterion = nn.BCEWithLogitsLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

EPOCHS = 150

for epoch in range(EPOCHS):
    model.train()
    optimizer.zero_grad()

    outputs = model(X_train_t)
    loss = criterion(outputs, y_train_t)

    loss.backward()
    optimizer.step()

    if epoch % 5 == 0:
        # Quick eval on test set every 5 epochs
        model.eval()
        with torch.no_grad():
            test_outputs = model(X_test_t)
            test_loss = criterion(test_outputs, y_test_t)
            test_preds = (torch.sigmoid(test_outputs) > 0.5).float()
            test_acc = (test_preds == y_test_t).float().mean()

        print(f"Epoch {epoch:3d} | Train Loss: {loss.item():.4f} | Test Loss: {test_loss.item():.4f} | Test Acc: {test_acc.item():.4f}")