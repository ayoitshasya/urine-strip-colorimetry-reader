"""
Adds hand-written urinalysis sentences to the templated dataset.

Markup:  [text|LABEL]   with LABEL = ANALYTE, LEVEL or CONDITION
Example: Dipstick positive for [blood|ANALYTE] [2+|LEVEL] , likely [UTI|CONDITION] .

Reads : urine_ner.json          (from generate_dataset.py, never modified)
Writes: urine_ner_full.json     (train + val + test + test_hand)

Even-numbered sentences go into TRAIN; odd-numbered ones become TEST_HAND,
a harder test set of phrasing the models never saw in the templates.
The list below has 90 sentences; you can add more at the bottom if you like.
"""
import json
import re

SENTENCES = [
    "Dipstick positive for [blood|ANALYTE] [2+|LEVEL] , likely [UTI|CONDITION] .",
    "No [glucose|ANALYTE] detected , [protein|ANALYTE] [negative|LEVEL] .",
    "[Ketones|ANALYTE] were [trace|LEVEL] after prolonged fasting .",
    "The urine showed [+3|LEVEL] [sugar|ANALYTE] , raising concern for [diabetes mellitus|CONDITION] .",
    "Persistent [protein|ANALYTE] [1+|LEVEL] on repeat testing may point to [nephropathy|CONDITION] .",
    "[Hemoglobin|ANALYTE] [+1|LEVEL] was noted on the strip .",
    "Doctor ordered a follow-up as [ketone bodies|ANALYTE] were [+2|LEVEL] , concerning for [ketoacidosis|CONDITION] .",
    "Strip showed [trace|LEVEL] [blood|ANALYTE] and [negative|LEVEL] [glucose|ANALYTE] .",
    "Marked [glycosuria|CONDITION] with [glucose|ANALYTE] [3+|LEVEL] was observed .",
    "[Albumin|ANALYTE] [2+|LEVEL] in the sample suggests [proteinuria|CONDITION] .",
    "Both [protein|ANALYTE] and [blood|ANALYTE] were [+1|LEVEL] on the test today .",
    "Result reads [glucose|ANALYTE] [negative|LEVEL] , [ketones|ANALYTE] [negative|LEVEL] , [protein|ANALYTE] [trace|LEVEL] .",
    "Visible [hematuria|CONDITION] was confirmed with [blood|ANALYTE] [3+|LEVEL] .",
    "[Sugar|ANALYTE] in urine was [+2|LEVEL] ; the physician suspected [diabetes|CONDITION] .",
    "Low [ketones|ANALYTE] ( [trace|LEVEL] ) were considered normal .",
    "Reported [protein|ANALYTE] [+3|LEVEL] alongside [blood|ANALYTE] [+2|LEVEL] , consistent with [kidney disease|CONDITION] .",
    "Test strip revealed [blood|ANALYTE] [1+|LEVEL] ; symptoms suggested [kidney stones|CONDITION] .",
    "The nurse recorded [glucose|ANALYTE] [+1|LEVEL] during routine screening .",
    "[Ketosis|CONDITION] was suspected because [ketones|ANALYTE] were [2+|LEVEL] .",
    "Nothing abnormal except [protein|ANALYTE] [trace|LEVEL] .",
    "High [glucose|ANALYTE] [3+|LEVEL] and [ketones|ANALYTE] [2+|LEVEL] indicate possible [ketoacidosis|CONDITION] .",
    "[Blood|ANALYTE] [negative|LEVEL] , [protein|ANALYTE] [negative|LEVEL] , no sign of [infection|CONDITION] .",
    "Follow-up needed for [albumin|ANALYTE] [+2|LEVEL] .",
    "The lab flagged [hemoglobin|ANALYTE] [3+|LEVEL] , so [hematuria|CONDITION] was investigated .",
    "Patient with known [diabetes|CONDITION] had [glucose|ANALYTE] [+3|LEVEL] today .",
    "Routine check found [ketone bodies|ANALYTE] [trace|LEVEL] only .",
    "[Proteinuria|CONDITION] persisted , with [protein|ANALYTE] [2+|LEVEL] on both visits .",
    "Slight [blood|ANALYTE] [trace|LEVEL] noted ; no [UTI|CONDITION] symptoms reported .",
    "Elevated [sugar|ANALYTE] [+1|LEVEL] and [protein|ANALYTE] [+1|LEVEL] were seen .",
    "Strip was read as [glucose|ANALYTE] [2+|LEVEL] , [protein|ANALYTE] [trace|LEVEL] , [blood|ANALYTE] [negative|LEVEL] .",
    "Suspected [nephropathy|CONDITION] due to rising [protein|ANALYTE] [3+|LEVEL] .",
    "[Ketones|ANALYTE] [+1|LEVEL] with [glucose|ANALYTE] [negative|LEVEL] is common after fasting .",
    "She had [blood|ANALYTE] [+2|LEVEL] and was treated for [urinary tract infection|CONDITION] .",
    "[Glucose|ANALYTE] : [negative|LEVEL] ; [Protein|ANALYTE] : [+1|LEVEL] .",
    "[Trace|LEVEL] amounts of [albumin|ANALYTE] were found .",
    "Doctors linked [3+|LEVEL] [blood|ANALYTE] to [kidney stones|CONDITION] .",
    "[Ketones|ANALYTE] rose to [+3|LEVEL] , signalling [ketoacidosis|CONDITION] .",
    "Only [glucose|ANALYTE] was abnormal at [+1|LEVEL] .",
    "[Negative|LEVEL] for [ketones|ANALYTE] and [blood|ANALYTE] .",
    "[Hematuria|CONDITION] with [hemoglobin|ANALYTE] [+2|LEVEL] prompted a scan .",
    "The dipstick was positive for [glucose|ANALYTE] at [+2|LEVEL] .",
    "Urinalysis report : [protein|ANALYTE] [+1|LEVEL] , [blood|ANALYTE] [trace|LEVEL] , [ketones|ANALYTE] [negative|LEVEL] .",
    "A [3+|LEVEL] reading for [glucose|ANALYTE] pointed toward uncontrolled [diabetes|CONDITION] .",
    "Her [protein|ANALYTE] level was [trace|LEVEL] and no [kidney disease|CONDITION] was suspected .",
    "Evidence of [blood|ANALYTE] ( [2+|LEVEL] ) raised the possibility of a [urinary tract infection|CONDITION] .",
    "Presence of [ketones|ANALYTE] at [1+|LEVEL] was linked to a low carbohydrate diet .",
    "The strip turned positive for [albumin|ANALYTE] , graded [+3|LEVEL] .",
    "[Glucose|ANALYTE] and [ketones|ANALYTE] were both [negative|LEVEL] this morning .",
    "Increased [hemoglobin|ANALYTE] [2+|LEVEL] was reported by the lab , suggesting [hematuria|CONDITION] .",
    "The child had [sugar|ANALYTE] [trace|LEVEL] in the sample but no other findings .",
    "Repeat testing showed [protein|ANALYTE] [+2|LEVEL] , so [nephropathy|CONDITION] was considered .",
    "Urine was tested and [blood|ANALYTE] came back [+3|LEVEL] .",
    "Elevated [ketone bodies|ANALYTE] [3+|LEVEL] and vomiting suggested [ketoacidosis|CONDITION] .",
    "[Glucose|ANALYTE] [trace|LEVEL] , [protein|ANALYTE] [negative|LEVEL] , [blood|ANALYTE] [negative|LEVEL] ; result within limits .",
    "Physician noted [proteinuria|CONDITION] after [albumin|ANALYTE] measured [2+|LEVEL] .",
    "The strip read [+1|LEVEL] for [blood|ANALYTE] and [+1|LEVEL] for [protein|ANALYTE] .",
    "Sample positive for [glucose|ANALYTE] [3+|LEVEL] ; patient advised to test for [diabetes|CONDITION] .",
    "Pain and [blood|ANALYTE] [2+|LEVEL] in urine hinted at [kidney stones|CONDITION] .",
    "No [ketones|ANALYTE] were found , only [glucose|ANALYTE] [+1|LEVEL] .",
    "[Trace|LEVEL] [protein|ANALYTE] is often harmless , unlike [protein|ANALYTE] [3+|LEVEL] .",
    "After exercise , [protein|ANALYTE] [1+|LEVEL] appeared briefly .",
    "[Ketosis|CONDITION] was confirmed when [ketones|ANALYTE] reached [+3|LEVEL] .",
    "The report listed [hemoglobin|ANALYTE] [negative|LEVEL] and [albumin|ANALYTE] [trace|LEVEL] .",
    "A pregnant patient showed [glucose|ANALYTE] [+1|LEVEL] and was screened for [diabetes|CONDITION] .",
    "[Blood|ANALYTE] : [2+|LEVEL] ; [Glucose|ANALYTE] : [negative|LEVEL] ; [Ketones|ANALYTE] : [trace|LEVEL] .",
    "Concerning [protein|ANALYTE] [3+|LEVEL] along with [glycosuria|CONDITION] was documented .",
    "Nurse observed [sugar|ANALYTE] [2+|LEVEL] on the strip and informed the doctor .",
    "Mild [blood|ANALYTE] [trace|LEVEL] without symptoms of [UTI|CONDITION] needs no treatment .",
    "[Albumin|ANALYTE] [+1|LEVEL] and [glucose|ANALYTE] [+1|LEVEL] were recorded for the patient .",
    "Test came back [negative|LEVEL] for [glucose|ANALYTE] , but [ketones|ANALYTE] were [+2|LEVEL] .",
    # ---- report-style sentences (match the wording of report_generator.py) ----
    "[Ketones|ANALYTE] were detected in [trace|LEVEL] amounts , which may be associated with [ketosis|CONDITION] , fasting or [ketoacidosis|CONDITION] .",
    "[Blood|ANALYTE] was detected in [trace|LEVEL] amounts , which may be associated with a [urinary tract infection|CONDITION] , [hematuria|CONDITION] or [kidney stones|CONDITION] .",
    "[Glucose|ANALYTE] was [not detected|LEVEL] .",
    "[Protein|ANALYTE] was [not detected|LEVEL] .",
    "[Ketones|ANALYTE] were [not detected|LEVEL] in this sample .",
    "[Blood|ANALYTE] was [not detected|LEVEL] .",
    "[Protein|ANALYTE] was markedly elevated ( [+3|LEVEL] ) , which may be associated with [proteinuria|CONDITION] or [kidney disease|CONDITION] .",
    "[Ketones|ANALYTE] were moderately elevated ( [+2|LEVEL] ) , which may be associated with [ketosis|CONDITION] , fasting or [ketoacidosis|CONDITION] .",
    "[Glucose|ANALYTE] was markedly elevated ( [+3|LEVEL] ) , which may be associated with [diabetes|CONDITION] or [glycosuria|CONDITION] .",
    "[Blood|ANALYTE] was mildly elevated ( [+1|LEVEL] ) , which may be associated with a [urinary tract infection|CONDITION] , [hematuria|CONDITION] or [kidney stones|CONDITION] .",
    "[Protein|ANALYTE] was moderately elevated ( [+2|LEVEL] ) , which may be associated with [proteinuria|CONDITION] or [kidney disease|CONDITION] .",
    "[Glucose|ANALYTE] was detected in [trace|LEVEL] amounts , which may be associated with [diabetes|CONDITION] or [glycosuria|CONDITION] .",
    "Urine [pH|ANALYTE] is 7.5 , which is within the typical range .",
    "Urine [pH|ANALYTE] is 4.5 , which is on the acidic side .",
    "Overall , abnormal findings were noted for : [Ketones|ANALYTE] , [Blood|ANALYTE] . Please consult a doctor for a proper evaluation .",
    "Overall , abnormal findings were noted for : [Protein|ANALYTE] , [Glucose|ANALYTE] . Consider repeating the test and discussing the result with a doctor .",
    "Overall , no abnormal findings were detected on this strip .",
    "Overall , abnormal findings were noted for : [Ketones|ANALYTE] , [Protein|ANALYTE] , [Blood|ANALYTE] . Please consult a doctor for a proper evaluation .",
    "Please consult a doctor for a proper evaluation .",
    "Consider repeating the test and discussing the result with a doctor .",
    # ---- ADD YOUR OWN SENTENCES BELOW (same markup) ----
]

TOKEN_RE = re.compile(r"\d+\.\d+|[+\-]?\d+\+?|\w+|[^\w\s]")
ENTITY_RE = re.compile(r"\[([^\]|]+)\|(ANALYTE|LEVEL|CONDITION)\]")


def tokenize(text):
    return TOKEN_RE.findall(text)


def parse(sentence):
    tokens, tags, pos = [], [], 0
    for m in ENTITY_RE.finditer(sentence):
        for t in tokenize(sentence[pos:m.start()]):
            tokens.append(t)
            tags.append("O")
        ent = tokenize(m.group(1))
        for j, t in enumerate(ent):
            tokens.append(t)
            tags.append(("B-" if j == 0 else "I-") + m.group(2))
        pos = m.end()
    for t in tokenize(sentence[pos:]):
        tokens.append(t)
        tags.append("O")
    return {"tokens": tokens, "tags": tags}


def main():
    with open("urine_ner.json") as f:
        data = json.load(f)

    parsed = [parse(s) for s in SENTENCES]
    data["train"] = data["train"] + parsed[0::2]
    data["test_hand"] = parsed[1::2]

    with open("urine_ner_full.json", "w") as f:
        json.dump(data, f, indent=1)

    print({k: len(v) for k, v in data.items()})
    for ex in parsed[:3]:
        print(list(zip(ex["tokens"], ex["tags"])))


if __name__ == "__main__":
    main()
