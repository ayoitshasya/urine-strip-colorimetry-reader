"""
CRF NER model for urinalysis text (no seqeval needed).
Requires: urine_ner.json (from generate_dataset.py) in the working folder.
Run in Colab:  %run crf_train.py
"""
import json
from collections import defaultdict

import sklearn_crfsuite

# ---------- data ----------
import os
DATA_FILE = "urine_ner_full.json" if os.path.exists("urine_ner_full.json") else "urine_ner.json"
print("Using dataset:", DATA_FILE)
with open(DATA_FILE) as f:
    data = json.load(f)
train, val, test = data["train"], data["val"], data["test"]
test_hand = data.get("test_hand")  # hand-written, harder test set (optional)


# ---------- features ----------
def word_features(tokens, i):
    w = tokens[i]
    feats = {
        "bias": 1.0,
        "w.lower": w.lower(),
        "w.suffix3": w[-3:].lower(),
        "w.suffix2": w[-2:].lower(),
        "w.prefix3": w[:3].lower(),
        "w.isdigit": w.isdigit(),
        "w.has_plus": "+" in w,
        "w.istitle": w.istitle(),
        "w.isupper": w.isupper(),
        "w.len": len(w),
    }
    if i > 0:
        p = tokens[i - 1]
        feats.update({"-1.lower": p.lower(), "-1.has_plus": "+" in p})
    else:
        feats["BOS"] = True
    if i < len(tokens) - 1:
        n = tokens[i + 1]
        feats.update({"+1.lower": n.lower(), "+1.has_plus": "+" in n})
    else:
        feats["EOS"] = True
    return feats


def sent2features(tokens):
    return [word_features(tokens, i) for i in range(len(tokens))]


X = lambda split: [sent2features(ex["tokens"]) for ex in split]
Y = lambda split: [ex["tags"] for ex in split]

# ---------- train ----------
crf = sklearn_crfsuite.CRF(
    algorithm="lbfgs", c1=0.1, c2=0.1, max_iterations=100,
    all_possible_transitions=True,
)
crf.fit(X(train), Y(train))


# ---------- entity-level scoring (replaces seqeval) ----------
def get_entities(tags):
    ents, start, label = set(), None, None
    for i, t in enumerate(list(tags) + ["O"]):
        if start is not None and (t == "O" or t.startswith("B-") or t[2:] != label):
            ents.add((label, start, i))
            start = None
        if t.startswith("B-") or (t.startswith("I-") and start is None):
            start, label = i, t[2:]
    return ents


def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f


def evaluate(y_true, y_pred):
    counts = defaultdict(lambda: [0, 0, 0])  # label -> [tp, fp, fn]
    for a, b in zip(y_true, y_pred):
        A, B = get_entities(a), get_entities(b)
        for e in A & B:
            counts[e[0]][0] += 1
        for e in B - A:
            counts[e[0]][1] += 1
        for e in A - B:
            counts[e[0]][2] += 1
    rows = {lab: prf(*c) for lab, c in counts.items()}
    tp, fp, fn = (sum(c[i] for c in counts.values()) for i in range(3))
    rows["OVERALL"] = prf(tp, fp, fn)
    return rows


def show(name, rows):
    print(f"\n{name}")
    print(f"{'label':<12}{'P':>8}{'R':>8}{'F1':>8}")
    for lab, (p, r, f) in sorted(rows.items()):
        print(f"{lab:<12}{p:8.3f}{r:8.3f}{f:8.3f}")


eval_sets = [("VALIDATION (templated)", val), ("TEST (templated)", test)]
if test_hand:
    eval_sets.append(("TEST_HAND (hand-written, unseen phrasing)", test_hand))
for name, split in eval_sets:
    show(name, evaluate(Y(split), crf.predict(X(split))))

# ---------- quick demo on new text ----------
demo = "Dipstick showed protein +2 and trace ketones suggesting kidney disease .".split()
print("\nDemo:", list(zip(demo, crf.predict_single(sent2features(demo)))))
