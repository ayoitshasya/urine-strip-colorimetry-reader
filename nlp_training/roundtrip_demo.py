"""
Round-trip demo:  strip JSON -> generated report -> CRF NER over the report.

Needs in the working folder: crf_train.py, report_generator.py,
urine_ner_full.json (or urine_ner.json).
Run in Colab:  %run roundtrip_demo.py
"""
import contextlib
import io
import re
import runpy

# train the CRF silently (reuses crf_train.py) and load the generator
with contextlib.redirect_stdout(io.StringIO()):
    g = runpy.run_path("crf_train.py")
crf, sent2features = g["crf"], g["sent2features"]
from report_generator import generate_report  # noqa: E402

TOKEN_RE = re.compile(r"\d+\.\d+|[+\-]?\d+\+?|\w+|[^\w\s]")


def extract_entities(tokens, tags):
    """Group BIO tags into (label, text) entities."""
    ents, cur, label = [], [], None
    for tok, tag in zip(tokens, tags):
        if tag.startswith("B-") or (tag.startswith("I-") and tag[2:] != label):
            if cur:
                ents.append((label, " ".join(cur)))
            cur, label = [tok], tag[2:]
        elif tag.startswith("I-"):
            cur.append(tok)
        else:
            if cur:
                ents.append((label, " ".join(cur)))
            cur, label = [], None
    if cur:
        ents.append((label, " ".join(cur)))
    return ents


# ---- 1. strip reader output (same shape as your /analyze JSON) ----
strip_json = {"results": {
    "Glucose": {"result": "+1"},
    "Protein": {"result": "Trace"},
    "pH": {"result": "6.0"},
    "Ketones": {"result": "Negative"},
    "Blood": {"result": "+2"},
}}

# ---- 2. generate the report ----
report = generate_report(strip_json)
print(report)

# ---- 3. run the CRF over each sentence line of the report ----
print("\n=========== NER OVER THE GENERATED REPORT ===========")
skip = ("URINE STRIP REPORT", "Note:")
for line in report.split("\n"):
    if not line.strip() or line.startswith(skip):
        continue
    tokens = TOKEN_RE.findall(line)
    tags = crf.predict_single(sent2features(tokens))
    ents = extract_entities(tokens, tags)
    print("\n" + line)
    print("  entities:", ents if ents else "none found")
