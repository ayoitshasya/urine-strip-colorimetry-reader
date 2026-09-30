# -----------------------------------------------------------------------
# service.py
#
# What this file does:
#   Turns the /analyze results into a plain-language report in English
#   and Hindi. Pipeline (from the NLP IA2 project):
#     strip results -> template report generator (English)
#                   -> LSTM seq2seq translator, sentence by sentence (Hindi)
#                   -> clinical consistency check on every Hindi sentence
#
# Safety behaviour:
#   If a Hindi sentence fails the consistency check (a fact from the
#   English line is missing or wrong), that line is returned in English
#   and flagged, rather than showing a possibly wrong medical statement.
# -----------------------------------------------------------------------

from functools import lru_cache

from .hindi_data import en_tok, hi_join, is_consistent
from .ner import highlight, highlight_hindi
from .report_generator import generate_report
from .translator import Seq2SeqTranslator


@lru_cache(maxsize=1)
def _translator():
    return Seq2SeqTranslator()   # loaded once, on first request


def _normalise(results):
    """The reference chart has a Glucose '+4' the report generator has no
    wording for, so cap it at '+3' (the highest level it describes)."""
    fixed = {}
    for name, data in results.items():
        raw = data.get("result") if isinstance(data, dict) else data
        fixed[name] = {"result": "+3" if str(raw).strip() == "+4" else raw}
    return fixed


def build_bilingual_report(results):
    """results: {'Glucose': {'result': '+1', ...}, ...} as returned by /analyze."""
    english = generate_report({"results": _normalise(results)})
    tr = _translator()
    hindi_lines, checks, segments, hi_segments = [], [], [], []
    for line in english.split("\n"):
        # NER highlighting; the title and disclaimer are boilerplate, so skip them
        skip = line.startswith(("URINE STRIP REPORT", "Note:"))
        segments.append(highlight(line) if line.strip() and not skip
                        else ([{"text": line, "label": None}] if line else []))
        if not line.strip():
            hindi_lines.append("")
            hi_segments.append([])
            continue
        hi = hi_join(tr.translate(en_tok(line)))
        try:
            ok = is_consistent(line, hi.split())
        except Exception:
            ok = False
        hindi_lines.append(hi if ok else line)
        if not ok:
            hi_segments.append(segments[-1])          # English fallback line
        elif skip:
            hi_segments.append([{"text": hi, "label": None}])   # title / disclaimer: no highlights
        else:
            hi_segments.append(highlight_hindi(hi))
        checks.append({"english": line, "hindi": hi if ok else None, "consistent": ok})
    return {
        "english": english,
        "english_segments": segments,
        "hindi": "\n".join(hindi_lines),
        "hindi_segments": hi_segments,
        "all_consistent": all(c["consistent"] for c in checks),
        "lines": checks,
    }