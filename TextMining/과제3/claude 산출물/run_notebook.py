"""Notebook의 실제 코드를 실행해 시각화 이미지를 생성"""
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'  # OMP 충돌 우회
import torch
import torch.nn as nn
import torch.optim as optim
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

# 한글 글꼴 설정 (Windows 기본)
matplotlib.rcParams['font.family'] = 'Malgun Gothic'
matplotlib.rcParams['axes.unicode_minus'] = False

torch.manual_seed(42)
np.random.seed(42)

OUT = os.path.dirname(os.path.abspath(__file__))
os.makedirs(OUT, exist_ok=True)

# Step 1
corpus = [
    "he is a king", "she is a queen", "he is a man", "she is a woman",
    "seoul is korea capital", "tokyo is japan capital", "paris is france capital"
]
words = " ".join(corpus).split()
word_list = list(set(words))
word_dict = {w: i for i, w in enumerate(word_list)}
number_dict = {i: w for i, w in enumerate(word_list)}
vocab_size = len(word_dict)
print("vocab_size:", vocab_size)
print("word_dict:", word_dict)

# Step 2
window_size = 1
skip_grams = []
for sentence in corpus:
    tokens = sentence.split()
    for i in range(len(tokens)):
        target = word_dict[tokens[i]]
        for j in range(max(0, i - window_size), min(len(tokens), i + window_size + 1)):
            if i != j:
                context = word_dict[tokens[j]]
                skip_grams.append([target, context])
print(f"skip_grams: {len(skip_grams)}")
print("first 5:", skip_grams[:5])

# Step 3
class Word2Vec(nn.Module):
    def __init__(self, vocab_size, embedding_size):
        super().__init__()
        self.W = nn.Linear(vocab_size, embedding_size, bias=False)
        self.WT = nn.Linear(embedding_size, vocab_size, bias=False)
    def forward(self, X):
        return self.WT(self.W(X))

embedding_size = 2
model = Word2Vec(vocab_size, embedding_size)

# Step 4
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.01)
def get_one_hot(idx, V):
    x = torch.zeros(V); x[idx] = 1.0; return x

# Step 5: training
epochs = 5000
losses = []
for epoch in range(epochs):
    loss_val = 0
    for target, context in skip_grams:
        x = get_one_hot(target, vocab_size)
        y_true = torch.tensor([context], dtype=torch.long)
        optimizer.zero_grad()
        y_pred = model(x)
        loss = criterion(y_pred.unsqueeze(0), y_true)
        loss.backward(); optimizer.step()
        loss_val += loss.item()
    losses.append(loss_val/len(skip_grams))
    if epoch % 1000 == 0:
        print(f"Epoch {epoch}: {losses[-1]:.4f}")
print(f"Final base loss: {losses[-1]:.4f}")

# Save loss plot
plt.figure(figsize=(8,4))
plt.plot(losses)
plt.title("Training Loss over Epochs")
plt.xlabel("Epoch"); plt.ylabel("Loss"); plt.grid(True)
plt.tight_layout()
plt.savefig(os.path.join(OUT, "fig_loss_base.png"), dpi=140)
plt.close()

# Step 6: embedding scatter
W_embed = model.W.weight.data.numpy().T
plt.figure(figsize=(10,8))
for i, w in enumerate(word_list):
    x, y = W_embed[i][0], W_embed[i][1]
    plt.scatter(x, y)
    plt.annotate(w, (x, y), xytext=(5,2), textcoords='offset points', ha='right', va='bottom', fontsize=12)
plt.title("Word2Vec (Skip-gram) Embedding Results")
plt.axhline(0, color='grey', lw=0.5); plt.axvline(0, color='grey', lw=0.5)
plt.grid(True); plt.tight_layout()
plt.savefig(os.path.join(OUT, "fig_embedding_base.png"), dpi=140)
plt.close()

# Step 7: tuning
tuning_embedding_size = 10
tuning_window_size = 2
tuning_epochs = 3000
tuning_skip_grams = []
for sentence in corpus:
    tokens = sentence.split()
    for i in range(len(tokens)):
        target = word_dict[tokens[i]]
        for j in range(max(0, i - tuning_window_size), min(len(tokens), i + tuning_window_size + 1)):
            if i != j:
                tuning_skip_grams.append([target, word_dict[tokens[j]]])

torch.manual_seed(42)
tuning_model = Word2Vec(vocab_size, tuning_embedding_size)
tuning_optim = optim.Adam(tuning_model.parameters(), lr=0.01)
tuning_losses = []
for epoch in range(tuning_epochs):
    loss_val = 0
    for target, context in tuning_skip_grams:
        x = get_one_hot(target, vocab_size)
        y_true = torch.tensor([context], dtype=torch.long)
        tuning_optim.zero_grad()
        y_pred = tuning_model(x)
        loss = criterion(y_pred.unsqueeze(0), y_true)
        loss.backward(); tuning_optim.step()
        loss_val += loss.item()
    tuning_losses.append(loss_val/len(tuning_skip_grams))
print(f"Tuned final loss: {tuning_losses[-1]:.4f}")
print(f"Tuned skip-gram pairs: {len(tuning_skip_grams)}")

plt.figure(figsize=(8,4))
plt.plot(tuning_losses, label='Tuned (Embed=10, Window=2)')
plt.title("Tuned Model Loss Reduction")
plt.xlabel("Epoch"); plt.ylabel("Loss"); plt.legend(); plt.grid(True); plt.tight_layout()
plt.savefig(os.path.join(OUT, "fig_loss_tuned.png"), dpi=140)
plt.close()

# Comparison plot
plt.figure(figsize=(8,4))
plt.plot(losses, label='Base (Embed=2, Window=1, 5000ep)')
plt.plot(tuning_losses, label='Tuned (Embed=10, Window=2, 3000ep)')
plt.title("Loss Comparison: Base vs Tuned")
plt.xlabel("Epoch"); plt.ylabel("Loss"); plt.legend(); plt.grid(True); plt.tight_layout()
plt.savefig(os.path.join(OUT, "fig_loss_compare.png"), dpi=140)
plt.close()

# Save numbers used in slides
with open(os.path.join(OUT, "metrics.txt"), "w", encoding="utf-8") as f:
    f.write(f"vocab_size={vocab_size}\n")
    f.write(f"skip_grams_base={len(skip_grams)}\n")
    f.write(f"skip_grams_tuned={len(tuning_skip_grams)}\n")
    f.write(f"final_loss_base={losses[-1]:.4f}\n")
    f.write(f"final_loss_tuned={tuning_losses[-1]:.4f}\n")
    f.write(f"first_5_skipgrams={skip_grams[:5]}\n")
print("Saved figures and metrics.")
