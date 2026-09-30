"""
Re-export a retrained model for the backend. Run this wherever PyTorch is
installed (e.g. the Colab notebook, right after seq2seq_train.py):

    python export_seq2seq.py seq2seq_hi.pt

Copy the two outputs into backend/app/nlp/models/ (replace the old ones).
"""
import json
import sys

import numpy as np
import torch

src = sys.argv[1] if len(sys.argv) > 1 else "seq2seq_hi.pt"
ck = torch.load(src, map_location="cpu")
arrays = {f"{part}.{name}": t.numpy().astype(np.float32)
          for part in ("enc", "dec") for name, t in ck[part].items()}
np.savez_compressed("seq2seq_hi.npz", **arrays)
with open("vocab.json", "w", encoding="utf-8") as f:
    json.dump({"sv": ck["sv"], "tv": ck["tv"]}, f, ensure_ascii=False)
print("wrote seq2seq_hi.npz and vocab.json")
