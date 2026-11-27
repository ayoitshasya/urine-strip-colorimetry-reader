"""
English -> Hindi LSTM seq2seq with Bahdanau attention (PyTorch).

Needs in the working folder: hindi_data.py, report_generator.py,
parallel_en_hi.json (run hindi_data.py first). crf_train.py + urine_ner_full.json
are optional (used for the NER verification step in the demo).
Run in Colab:  %run seq2seq_train.py      (T4 GPU optional; ~1-2 min)

Outputs: printed results table, seq2seq_results.csv, seq2seq_loss.png,
attention_heatmap.png, seq2seq_hi.pt (trained model), and a demo report.
"""
import contextlib
import csv
import io
import json
import random
import runpy

import numpy as np
import torch
import torch.nn as nn
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence

from hindi_data import en_tok, hi_join, is_consistent
from report_generator import generate_report

SEED = 42
random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ---------------- data ----------------
with open("parallel_en_hi.json", encoding="utf-8") as f:
    D = json.load(f)
train, val = D["train"], D["val"]
test_sets = [("VAL (summaries)", val), ("TEST_COMBO (held-out analyte/level)", D["test_combo"]),
             ("TEST_SUMMARY (held-out summaries)", D["test_summary"])]

PAD, SOS, EOS, UNK = 0, 1, 2, 3


def build_vocab(seqs):
    return {t: i + 4 for i, t in enumerate(sorted({t for s in seqs for t in s}))}


sv = build_vocab([p["src"] for p in train])
tv = build_vocab([p["tgt"] for p in train])
itot = {i: t for t, i in tv.items()}


def pad(seqs):
    L = max(len(s) for s in seqs)
    return torch.tensor([s + [PAD] * (L - len(s)) for s in seqs]).to(device)


def enc_src(toks):
    return [sv.get(t, UNK) for t in toks] + [EOS]


def enc_tgt(toks):
    return [SOS] + [tv.get(t, UNK) for t in toks] + [EOS]


# ---------------- model ----------------
H, E = 128, 96


class Encoder(nn.Module):
    def __init__(self, V):
        super().__init__()
        self.emb = nn.Embedding(V, E, padding_idx=PAD)
        self.rnn = nn.LSTM(E, H, batch_first=True, bidirectional=True)
        self.drop = nn.Dropout(0.2)

    def forward(self, src):
        lens = (src != PAD).sum(1).cpu()
        pk = pack_padded_sequence(self.drop(self.emb(src)), lens, batch_first=True, enforce_sorted=False)
        out, (h, c) = self.rnn(pk)
        out, _ = pad_packed_sequence(out, batch_first=True, total_length=src.size(1))
        return out, torch.cat([h[0], h[1]], -1), torch.cat([c[0], c[1]], -1)


class Decoder(nn.Module):
    def __init__(self, V):
        super().__init__()
        D = 2 * H
        self.emb = nn.Embedding(V, E, padding_idx=PAD)
        self.We = nn.Linear(D, 128, bias=False)
        self.Wd = nn.Linear(D, 128)
        self.v = nn.Linear(128, 1, bias=False)
        self.cell = nn.LSTMCell(E + D, D)
        self.out = nn.Linear(2 * D, V)
        self.drop = nn.Dropout(0.2)

    def step(self, y, h, c, enc, mask):
        score = self.v(torch.tanh(self.We(enc) + self.Wd(h).unsqueeze(1))).squeeze(-1)
        a = torch.softmax(score.masked_fill(~mask, -1e9), -1)          # attention weights
        ctx = torch.bmm(a.unsqueeze(1), enc).squeeze(1)                # context vector
        h, c = self.cell(torch.cat([self.drop(self.emb(y)), ctx], -1), (h, c))
        return self.out(torch.cat([h, ctx], -1)), h, c, a


encoder, decoder = Encoder(len(sv) + 4).to(device), Decoder(len(tv) + 4).to(device)
params = list(encoder.parameters()) + list(decoder.parameters())
opt = torch.optim.Adam(params, lr=3e-3)
crit = nn.CrossEntropyLoss(ignore_index=PAD)

# ---------------- train (fixed epochs, no tuning on test sets) ----------------
EPOCHS, BATCH, TF = 150, 16, 0.7
losses = []
data = train[:]
for epoch in range(1, EPOCHS + 1):
    encoder.train(); decoder.train()
    random.shuffle(data)
    total = 0.0
    for i in range(0, len(data), BATCH):
        chunk = data[i:i + BATCH]
        src = pad([enc_src(p["src"]) for p in chunk])
        tgt = pad([enc_tgt(p["tgt"]) for p in chunk])
        enc_out, h, c = encoder(src)
        mask = src != PAD
        y, loss = tgt[:, 0], 0.0
        for t in range(1, tgt.size(1)):
            logits, h, c, _ = decoder.step(y, h, c, enc_out, mask)
            loss = loss + crit(logits, tgt[:, t])
            y = tgt[:, t] if random.random() < TF else logits.argmax(-1)
        loss = loss / (tgt.size(1) - 1)
        opt.zero_grad(); loss.backward()
        nn.utils.clip_grad_norm_(params, 1.0)
        opt.step()
        total += loss.item()
    losses.append(total)
    if epoch == 1 or epoch % 25 == 0:
        print(f"epoch {epoch:3d}  loss {total:.3f}")


# ---------------- translate ----------------
@torch.no_grad()
def translate(tokens, max_len=90):
    encoder.eval(); decoder.eval()
    src = pad([enc_src(tokens)])
    enc_out, h, c = encoder(src)
    mask = src != PAD
    y, out, att = torch.tensor([SOS]).to(device), [], []
    for _ in range(max_len):
        logits, h, c, a = decoder.step(y, h, c, enc_out, mask)
        y = logits.argmax(-1)
        if y.item() == EOS:
            break
        out.append(itot.get(y.item(), "<unk>"))
        att.append(a[0].cpu().numpy())
    return out, np.array(att)


# ---------------- evaluate ----------------
try:
    from nltk.translate.bleu_score import corpus_bleu, SmoothingFunction
    smooth = SmoothingFunction().method1
except Exception:
    corpus_bleu = None

rows = []
print("\n=========== RESULTS ===========")
print(f"{'set':<38}{'n':>4}{'BLEU':>8}{'exact':>8}{'consistent':>12}")
for name, split in [("TRAIN", train)] + test_sets:
    preds = [translate(p["src"])[0] for p in split]
    exact = np.mean([pr == p["tgt"] for pr, p in zip(preds, split)])
    cons = np.mean([is_consistent(p["en"], pr) for pr, p in zip(preds, split)])
    bleu = (corpus_bleu([[p["tgt"]] for p in split], preds, smoothing_function=smooth)
            if corpus_bleu else float("nan"))
    print(f"{name:<38}{len(split):>4}{bleu:8.3f}{exact:8.3f}{cons:12.3f}")
    rows.append([name, len(split), round(bleu, 3), round(exact, 3), round(cons, 3)])
    if name != "TRAIN":
        for pr, p in zip(preds, split):
            if pr != p["tgt"]:
                print("  EN  :", p["en"]); print("  REF :", p["hi"]); print("  PRED:", hi_join(pr))
with open("seq2seq_results.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["set", "n", "bleu", "exact_match", "clinical_consistency"]); w.writerows(rows)

# ---------------- loss curve + attention heatmap ----------------
import glob
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

plt.figure(figsize=(6, 3)); plt.plot(losses); plt.xlabel("epoch"); plt.ylabel("loss")
plt.title("Training loss"); plt.tight_layout(); plt.savefig("seq2seq_loss.png", dpi=150); plt.show()

for fp in glob.glob("/usr/share/fonts/**/*eva*.ttf", recursive=True):   # Devanagari font, if installed
    fm.fontManager.addfont(fp)
    plt.rcParams["font.family"] = fm.FontProperties(fname=fp).get_name()
    break
ex = D["test_combo"][0]
out, att = translate(ex["src"])
plt.figure(figsize=(10, 4))
plt.imshow(att, aspect="auto", cmap="viridis")
plt.xticks(range(len(ex["src"]) + 1), ex["src"] + ["<eos>"], rotation=90)
plt.yticks(range(len(out)), out)
plt.title("Attention: English (x) -> Hindi (y)"); plt.tight_layout()
plt.savefig("attention_heatmap.png", dpi=150); plt.show()
print("(If Hindi labels show as boxes, run: !apt-get -qq install fonts-lohit-deva, then re-run this script.)")

# ---------------- save model ----------------
torch.save({"enc": encoder.state_dict(), "dec": decoder.state_dict(), "sv": sv, "tv": tv}, "seq2seq_hi.pt")

# ---------------- full pipeline demo ----------------
try:
    with contextlib.redirect_stdout(io.StringIO()):
        g = runpy.run_path("crf_train.py")
    crf, s2f = g["crf"], g["sent2features"]
except Exception:
    crf = None

strip_json = {"results": {"Glucose": {"result": "+1"}, "Protein": {"result": "Trace"},
                          "pH": {"result": "6.0"}, "Ketones": {"result": "Negative"},
                          "Blood": {"result": "+2"}}}
print("\n=========== FULL PIPELINE DEMO ===========")
for line in generate_report(strip_json).split("\n"):
    if not line.strip():
        continue
    toks = en_tok(line)
    hi = translate(toks)[0]
    print("\nEN :", line)
    if crf:
        tags = crf.predict_single(s2f(toks))
        print("NER:", [(t, w) for w, t in zip(toks, tags) if t != "O"])
    print("HI :", hi_join(hi))
    print("consistency check:", "PASS" if is_consistent(line, hi) else "FAIL")
