# -----------------------------------------------------------------------
# translator.py
#
# What this file does:
#   Runs the trained English -> Hindi LSTM seq2seq model (Bahdanau
#   attention) for inference only, in plain numpy. The weights come from
#   models/seq2seq_hi.npz, exported from seq2seq_hi.pt trained in the
#   NLP IA2 notebook (see backend/scripts/export_seq2seq.py).
#
# Why numpy and not PyTorch:
#   The model is ~4 MB. PyTorch would add several hundred MB of RAM and
#   install size, which is a problem on Render's free tier. The maths
#   below mirrors Encoder / Decoder.step in seq2seq_train.py exactly.
# -----------------------------------------------------------------------

import json
import os

import numpy as np

_DIR = os.path.join(os.path.dirname(__file__), "models")
PAD, SOS, EOS, UNK = 0, 1, 2, 3


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def _lstm_step(x, h, c, w_ih, w_hh, b):
    """One LSTM step. PyTorch gate order: input, forget, cell, output."""
    z = w_ih @ x + w_hh @ h + b
    i, f, g, o = np.split(z, 4)
    c = _sigmoid(f) * c + _sigmoid(i) * np.tanh(g)
    return _sigmoid(o) * np.tanh(c), c


class Seq2SeqTranslator:
    def __init__(self, model_dir=_DIR):
        self.w = dict(np.load(os.path.join(model_dir, "seq2seq_hi.npz")))
        with open(os.path.join(model_dir, "vocab.json"), encoding="utf-8") as f:
            vocab = json.load(f)
        self.sv, self.tv = vocab["sv"], vocab["tv"]
        self.itot = {i: t for t, i in self.tv.items()}
        self.H = self.w["enc.rnn.weight_hh_l0"].shape[1]

    def _encode(self, ids):
        w, H = self.w, self.H
        x = w["enc.emb.weight"][ids]
        fwd, bwd = [], [None] * len(ids)
        h = c = np.zeros(H, np.float32)
        for t in range(len(ids)):
            h, c = _lstm_step(x[t], h, c, w["enc.rnn.weight_ih_l0"], w["enc.rnn.weight_hh_l0"],
                              w["enc.rnn.bias_ih_l0"] + w["enc.rnn.bias_hh_l0"])
            fwd.append(h)
        hf, cf = h, c
        h = c = np.zeros(H, np.float32)
        for t in reversed(range(len(ids))):
            h, c = _lstm_step(x[t], h, c, w["enc.rnn.weight_ih_l0_reverse"], w["enc.rnn.weight_hh_l0_reverse"],
                              w["enc.rnn.bias_ih_l0_reverse"] + w["enc.rnn.bias_hh_l0_reverse"])
            bwd[t] = h
        enc = np.concatenate([np.stack(fwd), np.stack(bwd)], axis=1)      # (T, 2H)
        return enc, np.concatenate([hf, h]), np.concatenate([cf, c])      # h, c: forward final + backward final

    def translate(self, tokens, max_len=90):
        """List of English tokens -> list of Hindi tokens."""
        w = self.w
        ids = [self.sv.get(t, UNK) for t in tokens] + [EOS]
        enc, h, c = self._encode(ids)
        We = enc @ w["dec.We.weight"].T                                   # attention keys, computed once
        y, out = SOS, []
        for _ in range(max_len):
            score = np.tanh(We + (w["dec.Wd.weight"] @ h + w["dec.Wd.bias"])) @ w["dec.v.weight"][0]
            a = np.exp(score - score.max()); a /= a.sum()
            ctx = a @ enc
            h, c = _lstm_step(np.concatenate([w["dec.emb.weight"][y], ctx]), h, c,
                              w["dec.cell.weight_ih"], w["dec.cell.weight_hh"],
                              w["dec.cell.bias_ih"] + w["dec.cell.bias_hh"])
            y = int(np.argmax(w["dec.out.weight"] @ np.concatenate([h, ctx]) + w["dec.out.bias"]))
            if y == EOS:
                break
            out.append(self.itot.get(y, "<unk>"))
        return out
