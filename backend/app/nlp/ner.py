import os
import re
from functools import lru_cache

import pycrfsuite

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "urine_crf.crfsuite")
TOKEN_RE = re.compile(r"\d+\.\d+|[+\-]?\d+\+?|\w+|[^\w\s]")


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


@lru_cache(maxsize=1)
def _tagger():
    t = pycrfsuite.Tagger()
    t.open(MODEL_PATH)
    return t


def highlight(line):
    """Split a report line into [{'text': ..., 'label': 'ANALYTE'|'LEVEL'|'CONDITION'|None}]."""
    spans = [(m.start(), m.end()) for m in TOKEN_RE.finditer(line)]
    if not spans:
        return [{"text": line, "label": None}] if line else []
    tokens = [line[a:b] for a, b in spans]
    tags = _tagger().tag(sent2features(tokens))

    ents, cur = [], None
    for (a, b), tag in zip(spans, tags):
        label = tag[2:] if tag != "O" else None
        if label and cur and cur["label"] == label and not tag.startswith("B-"):
            cur["end"] = b
        else:
            if cur:
                ents.append(cur)
            cur = {"start": a, "end": b, "label": label} if label else None
    if cur:
        ents.append(cur)

    segs, pos = [], 0
    for e in ents:
        if e["start"] > pos:
            segs.append({"text": line[pos:e["start"]], "label": None})
        segs.append({"text": line[e["start"]:e["end"]], "label": e["label"]})
        pos = e["end"]
    if pos < len(line):
        segs.append({"text": line[pos:], "label": None})
    return segs

from .hindi_data import HI_ASSOC, HI_NAME  # noqa: E402

_HI_TERMS = {}
for _n in HI_NAME.values():
    _HI_TERMS[_n] = "ANALYTE"
for _phrase in HI_ASSOC.values():
    for _part in _phrase.replace(",", " या ").split(" या "):
        _part = _part.strip()
        if _part and _part != "उपवास":
            _HI_TERMS[_part] = "CONDITION"
_HI_TERMS["नहीं पाया गया"] = "LEVEL"
_HI_RE = re.compile(
    "|".join([r"[+\-]\d"] + [re.escape(t) for t in sorted(_HI_TERMS, key=len, reverse=True)])
)


def highlight_hindi(line):
    segs, pos = [], 0
    for m in _HI_RE.finditer(line):
        if m.start() > pos:
            segs.append({"text": line[pos:m.start()], "label": None})
        segs.append({"text": m.group(), "label": _HI_TERMS.get(m.group(), "LEVEL")})
        pos = m.end()
    if pos < len(line):
        segs.append({"text": line[pos:], "label": None})
    return segs