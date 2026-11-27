"""
Generates a templated, BIO-labeled urinalysis NER dataset.
Tags: ANALYTE, LEVEL, CONDITION  (BIO scheme: B-/I-/O)

Run in Colab:  %run generate_dataset.py   (or paste into a cell)
Output: urine_ner.json (list of {"tokens": [...], "tags": [...]})
"""
import json
import random

random.seed(42)

ANALYTES = ["glucose", "protein", "ketones", "blood", "pH"]
# Synonyms / variants make the task less trivial (Module 4: lexical knowledge)
ANALYTE_SYNONYMS = {
    "glucose": ["glucose", "glucose", "sugar"],
    "protein": ["protein", "protein", "albumin"],
    "ketones": ["ketones", "ketones", "ketone bodies"],
    "blood": ["blood", "blood", "hemoglobin"],
    "pH": ["pH"],
}
LEVELS = ["negative", "trace", "+1", "+2", "+3", "1+", "2+", "3+"]

# condition linked to analyte (only used with abnormal levels)
CONDITIONS = {
    "glucose": ["diabetes", "glycosuria", "diabetes mellitus"],
    "protein": ["kidney disease", "proteinuria", "nephropathy"],
    "ketones": ["ketoacidosis", "ketosis"],
    "blood": ["urinary tract infection", "hematuria", "kidney stones"],
    "pH": ["urinary tract infection", "kidney stones"],
}

# Templates: {A}=analyte, {L}=level, {C}=condition
TEMPLATES_WITH_COND = [
    "Urine test showed {A} {L} suggesting {C} .",
    "The strip reported {A} {L} , which may indicate {C} .",
    "Elevated {A} ( {L} ) is associated with {C} .",
    "Patient had {A} {L} in urine and was evaluated for {C} .",
    "Detected {A} {L} , possible {C} .",
]
TEMPLATES_NO_COND = [
    "Urine strip showed {A} {L} .",
    "The reading for {A} was {L} .",
    "{A} {L} was recorded on the test strip .",
    "Result : {A} {L} .",
]
TEMPLATES_TWO = [
    "Urinalysis showed {A} {L} and {A2} {L2} .",
    "The strip reported {A} {L} with {A2} {L2} .",
]


def tag_phrase(phrase, label):
    """Return tokens + BIO tags for a (possibly multi-word) phrase."""
    toks = phrase.split()
    tags = [f"B-{label}"] + [f"I-{label}"] * (len(toks) - 1)
    return toks, tags


def fill(template, slots):
    tokens, tags = [], []
    for piece in template.split(" "):
        if piece in ("{A}", "{A2}", "{L}", "{L2}", "{C}"):
            key = piece.strip("{}")
            label = {"A": "ANALYTE", "A2": "ANALYTE", "L": "LEVEL",
                     "L2": "LEVEL", "C": "CONDITION"}[key]
            t, g = tag_phrase(slots[key], label)
            tokens += t
            tags += g
        else:
            tokens.append(piece)
            tags.append("O")
    return {"tokens": tokens, "tags": tags}


def sample_analyte():
    a = random.choice(ANALYTES)
    return a, random.choice(ANALYTE_SYNONYMS[a])


def make_sentence():
    r = random.random()
    a, a_text = sample_analyte()
    level = random.choice(LEVELS)
    if r < 0.45:
        cond = random.choice(CONDITIONS[a])
        tpl = random.choice(TEMPLATES_WITH_COND)
        return fill(tpl, {"A": a_text, "L": level, "C": cond})
    if r < 0.80:
        tpl = random.choice(TEMPLATES_NO_COND)
        return fill(tpl, {"A": a_text, "L": level})
    a2, a2_text = sample_analyte()
    while a2 == a:
        a2, a2_text = sample_analyte()
    tpl = random.choice(TEMPLATES_TWO)
    return fill(tpl, {"A": a_text, "L": level, "A2": a2_text,
                      "L2": random.choice(LEVELS)})


def main(n=300, path="urine_ner.json"):
    seen, data = set(), []
    while len(data) < n:
        ex = make_sentence()
        key = " ".join(ex["tokens"])
        if key in seen:  # avoid duplicates leaking across splits
            continue
        seen.add(key)
        data.append(ex)

    random.shuffle(data)
    n_train, n_val = int(0.70 * n), int(0.15 * n)
    splits = {
        "train": data[:n_train],
        "val": data[n_train:n_train + n_val],
        "test": data[n_train + n_val:],
    }
    with open(path, "w") as f:
        json.dump(splits, f, indent=1)

    print({k: len(v) for k, v in splits.items()})
    for ex in splits["train"][:3]:
        print(list(zip(ex["tokens"], ex["tags"])))


if __name__ == "__main__":
    main()
