# nlp_training — NLP IA2 training and evaluation code

Training and evaluation scripts for the NLP features of the urine strip reader:

1. **NER** over urine-test report sentences (CRF vs BiLSTM) with labels `ANALYTE`, `CONDITION`, `LEVEL`.
2. **English → Hindi Seq2Seq with attention** that translates generated reports, plus a clinical consistency check.

The code that *serves* these models in the app lives in [`backend/app/nlp/`](../backend/app/nlp/). Nothing here is imported by the web app.

## Files

| File | Purpose |
|---|---|
| `generate_dataset.py` | Generates the templated BIO-tagged NER dataset → `urine_ner.json` (seeded, `random.seed(42)`). |
| `add_handwritten.py` | Reads `urine_ner.json`, adds 45 hand-written sentences with unseen phrasing as `test_hand`, writes `urine_ner_full.json` (train/val/test/test_hand). |
| `crf_train.py` | Trains and evaluates the CRF NER model (`sklearn-crfsuite`). Also imported by `bilstm_train.py` and `roundtrip_demo.py`. |
| `bilstm_train.py` | Trains the BiLSTM NER model, compares it with the CRF on every split → `comparison_results.csv`. |
| `roundtrip_demo.py` | Demo: strip JSON → generated report → CRF NER over the report. |
| `seq2seq_train.py` | Trains the English→Hindi Seq2Seq with attention, evaluates BLEU / exact match / clinical consistency → `seq2seq_results.csv`, `seq2seq_loss.png`, `attention_heatmap.png`, `seq2seq_hi.pt`. |
| `urine_ner.json` | Templated NER dataset (output of `generate_dataset.py`). |
| `parallel_en_hi.json` | English–Hindi parallel corpus (output of `hindi_data.py`). |
| `comparison_results.csv` | CRF vs BiLSTM precision/recall/F1 per label and split. |
| `seq2seq_results.csv` | Seq2Seq BLEU, exact match and clinical consistency per split. |
| `seq2seq_loss.png` | Seq2Seq training loss curve. |
| `attention_heatmap.png` | Example attention alignment (English → Hindi). |
| `seq2seq_hi.pt` | Trained PyTorch checkpoint (encoder, decoder, vocabularies, ~4 MB). The app serves a NumPy export of the same model, `backend/app/nlp/models/seq2seq_hi.npz`. |

### Files deliberately not duplicated here

These are identical to the copies in `backend/app/nlp/` and are used from there:

- `hindi_data.py` — Hindi tokenisers, templates and the `is_consistent` check; running it writes `parallel_en_hi.json`
- `report_generator.py` — strip JSON → English report
- `urine_ner_full.json` — regenerate it with `add_handwritten.py` (step 2) or copy it from `backend/app/nlp/`

## Setup

```bash
cd nlp_training
python -m venv venv && source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt

# make hindi_data.py and report_generator.py importable
export PYTHONPATH=../backend/app/nlp                 # Windows PowerShell: $env:PYTHONPATH="../backend/app/nlp"
```

Run every script from inside `nlp_training/` — they read and write files in the current directory.

## Run order

```bash
python generate_dataset.py     # 1. -> urine_ner.json
python add_handwritten.py      # 2. -> urine_ner_full.json (adds the 45 hand-written test sentences)
python crf_train.py            # 3. CRF NER training + evaluation
python bilstm_train.py         # 4. BiLSTM NER + CRF-vs-BiLSTM table -> comparison_results.csv
python ../backend/app/nlp/hindi_data.py   # 5. -> parallel_en_hi.json (written to the current directory)
python seq2seq_train.py        # 6. Seq2Seq training -> results CSV, plots, seq2seq_hi.pt
python roundtrip_demo.py       # 7. optional end-to-end demo
```

> Run step 2 before step 3: `crf_train.py` silently falls back to `urine_ner.json` when `urine_ner_full.json` is missing, which would drop the hand-written test set.
>
> `seq2seq_train.py` and `bilstm_train.py` call `plt.show()` / print results; on a headless machine set `MPLBACKEND=Agg`. The scripts were written for Colab (`%run`).

## Results (see the CSVs)

- NER on the 45 hand-written sentences with unseen phrasing: **CRF F1 0.983**, **BiLSTM F1 0.935**.
- NER on templated train/validation/test: 1.00 for both models (templated data is easy; this is not evidence of generalisation).
- Seq2Seq: 1.00 BLEU, exact match and clinical consistency on all templated splits, including held-out analyte/level combinations.

These are proof-of-concept numbers on small, templated data. This is not a clinical tool.
