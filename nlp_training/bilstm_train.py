"""
BiLSTM NER tagger for urinalysis text + comparison with the CRF.

Needs in the working folder:  crf_train.py, urine_ner_full.json (or urine_ner.json)
Run in Colab:  %run bilstm_train.py
Torch is preinstalled in Colab; a GPU is optional (the data is tiny).

It reuses crf_train.py silently (same data, same scorer, same CRF model),
so both models are trained and scored on exactly the same splits.
Outputs: per-label tables for the BiLSTM, a CRF-vs-BiLSTM comparison table,
and comparison_results.csv (handy for your PPT).
"""
import contextlib
import csv
import io
import random
import runpy

import numpy as np
import torch
import torch.nn as nn
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ---------- reuse the CRF script (data, scorer, trained CRF) ----------
with contextlib.redirect_stdout(io.StringIO()):
    g = runpy.run_path("crf_train.py")
train, val, test = g["train"], g["val"], g["test"]
eval_sets = g["eval_sets"]          # [(name, split), ...] incl. TEST_HAND if present
evaluate, crf, X, Y = g["evaluate"], g["crf"], g["X"], g["Y"]
sent2features = g["sent2features"]

# ---------- vocabulary ----------
PAD, UNK = 0, 1
words = sorted({w.lower() for ex in train for w in ex["tokens"]})
w2i = {w: i + 2 for i, w in enumerate(words)}
tag_list = sorted({t for ex in train for t in ex["tags"]})
t2i = {t: i for i, t in enumerate(tag_list)}


def shape(w):
    """Tiny shape feature so unseen words / levels are still recognisable."""
    if any(c.isdigit() for c in w) or "+" in w:
        return 1
    if not any(c.isalnum() for c in w):
        return 2
    if w[0].isupper():
        return 3
    return 0


def encode(ex, word_dropout=0.0):
    ids = []
    for w in ex["tokens"]:
        i = w2i.get(w.lower(), UNK)
        if word_dropout and random.random() < word_dropout:
            i = UNK  # teaches the model to cope with unseen words
        ids.append(i)
    shp = [shape(w) for w in ex["tokens"]]
    tg = [t2i.get(t, t2i["O"]) for t in ex["tags"]]
    return ids, shp, tg


def batchify(exs, word_dropout=0.0):
    enc = [encode(e, word_dropout) for e in exs]
    L = max(len(e[0]) for e in enc)
    W = torch.zeros(len(enc), L, dtype=torch.long)
    S = torch.zeros(len(enc), L, dtype=torch.long)
    T = torch.full((len(enc), L), -100, dtype=torch.long)
    for b, (ids, shp, tg) in enumerate(enc):
        n = len(ids)
        W[b, :n] = torch.tensor(ids)
        S[b, :n] = torch.tensor(shp)
        T[b, :n] = torch.tensor(tg)
    return W.to(device), S.to(device), T.to(device)


# ---------- model ----------
class BiLSTMTagger(nn.Module):
    def __init__(self, vocab_size, n_tags, emb=64, shp=8, hid=64):
        super().__init__()
        self.emb = nn.Embedding(vocab_size, emb, padding_idx=PAD)
        self.shp = nn.Embedding(4, shp)
        self.drop = nn.Dropout(0.3)
        self.lstm = nn.LSTM(emb + shp, hid, batch_first=True, bidirectional=True)
        self.out = nn.Linear(2 * hid, n_tags)

    def forward(self, W, S):
        lengths = (W != PAD).sum(1).cpu()
        x = self.drop(torch.cat([self.emb(W), self.shp(S)], dim=-1))
        packed = pack_padded_sequence(x, lengths, batch_first=True, enforce_sorted=False)
        h, _ = self.lstm(packed)
        h, _ = pad_packed_sequence(h, batch_first=True, total_length=W.size(1))
        return self.out(self.drop(h))


model = BiLSTMTagger(len(w2i) + 2, len(t2i)).to(device)
opt = torch.optim.Adam(model.parameters(), lr=5e-3)
loss_fn = nn.CrossEntropyLoss(ignore_index=-100)

# ---------- train (fixed epochs: no tuning on the test sets) ----------
EPOCHS, BATCH = 30, 16
data = train[:]
for epoch in range(1, EPOCHS + 1):
    model.train()
    random.shuffle(data)
    total = 0.0
    for i in range(0, len(data), BATCH):
        W, S, T = batchify(data[i:i + BATCH], word_dropout=0.1)
        logits = model(W, S)
        loss = loss_fn(logits.view(-1, len(t2i)), T.view(-1))
        opt.zero_grad()
        loss.backward()
        opt.step()
        total += loss.item()
    if epoch % 5 == 0 or epoch == 1:
        print(f"epoch {epoch:2d}  loss {total:.3f}")


# ---------- predict ----------
def predict(split):
    model.eval()
    out = []
    with torch.no_grad():
        for i in range(0, len(split), 32):
            chunk = split[i:i + 32]
            W, S, _ = batchify(chunk)
            pred = model(W, S).argmax(-1).cpu()
            for b, ex in enumerate(chunk):
                out.append([tag_list[j] for j in pred[b, :len(ex["tokens"])].tolist()])
    return out


def show(name, rows):
    print(f"\n{name}")
    print(f"{'label':<12}{'P':>8}{'R':>8}{'F1':>8}")
    for lab, (p, r, f) in sorted(rows.items()):
        print(f"{lab:<12}{p:8.3f}{r:8.3f}{f:8.3f}")


# ---------- evaluate both models on the same sets ----------
all_sets = [("TRAIN (overfitting check)", train)] + eval_sets
results = {}  # (set, model) -> rows
for name, split in all_sets:
    results[(name, "CRF")] = evaluate(Y(split), crf.predict(X(split)))
    results[(name, "BiLSTM")] = evaluate(Y(split), predict(split))

print("\n================ BiLSTM RESULTS ================")
for name, _ in all_sets[1:]:
    show(name, results[(name, "BiLSTM")])

print("\n============ CRF vs BiLSTM (overall) ============")
print(f"{'Set':<44}{'Model':<8}{'P':>7}{'R':>7}{'F1':>7}")
for name, _ in all_sets:
    for m in ("CRF", "BiLSTM"):
        p, r, f = results[(name, m)]["OVERALL"]
        print(f"{name:<44}{m:<8}{p:7.3f}{r:7.3f}{f:7.3f}")

hard = next((n for n, _ in all_sets if n.startswith("TEST_HAND")), None)
if hard:
    print(f"\nPer-label F1 on {hard}")
    print(f"{'label':<12}{'CRF':>8}{'BiLSTM':>8}")
    for lab in ("ANALYTE", "LEVEL", "CONDITION"):
        c = results[(hard, "CRF")].get(lab, (0, 0, 0))[2]
        b = results[(hard, "BiLSTM")].get(lab, (0, 0, 0))[2]
        print(f"{lab:<12}{c:8.3f}{b:8.3f}")

with open("comparison_results.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["set", "model", "label", "precision", "recall", "f1"])
    for (name, m), rows in results.items():
        for lab, (p, r, fs) in sorted(rows.items()):
            w.writerow([name, m, lab, round(p, 3), round(r, 3), round(fs, 3)])
print("\nSaved comparison_results.csv")

# ---------- demo on a new sentence ----------
demo = "Dipstick showed protein +2 and trace ketones suggesting kidney disease .".split()
ex = {"tokens": demo, "tags": ["O"] * len(demo)}
print("\nCRF   :", list(zip(demo, crf.predict_single(sent2features(demo)))))
print("BiLSTM:", list(zip(demo, predict([ex])[0])))
