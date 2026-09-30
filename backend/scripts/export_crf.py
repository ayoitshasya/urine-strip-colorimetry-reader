import json
import sys

import pycrfsuite

sys.path.insert(0, "backend")
from app.nlp.ner import sent2features

data = json.load(open(sys.argv[1]))
trainer = pycrfsuite.Trainer(algorithm="lbfgs", verbose=False)
trainer.set_params({"c1": 0.1, "c2": 0.1, "max_iterations": 100,
                    "feature.possible_transitions": True})
for ex in data["train"]:
    trainer.append(sent2features(ex["tokens"]), ex["tags"])
trainer.train("backend/app/nlp/models/urine_crf.crfsuite")
print("saved backend/app/nlp/models/urine_crf.crfsuite")