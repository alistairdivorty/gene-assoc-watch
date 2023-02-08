import json
import mlflow
from mlflow.models import ModelSignature
from inference.sentence_pair_classifier import SentencePairClassifier

mlflow.pyfunc.save_model(
    "models/sentence_pair_classifier",
    python_model=SentencePairClassifier(model_path="models/t5_pubmed_mnli"),
    signature=ModelSignature.from_dict(
        {
            "inputs": json.dumps(
                [
                    {"name": "premise", "type": "string"},
                    {"name": "hypothesis", "type": "string"},
                ]
            ),
        }
    ),
)
