from pandas.core.frame import DataFrame
from pandas.core.series import Series
import mlflow
import numpy as np


class SentencePairClassifier(mlflow.pyfunc.PythonModel):
    def __init__(self, model_path):
        from transformers import (
            AutoTokenizer,
            AutoModelForSeq2SeqLM,
        )

        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_path)

    def predict(self, context, model_input: DataFrame) -> DataFrame:
        return model_input.apply(self.generate, axis=1)

    def generate(self, row: Series) -> dict:
        input_ = f"mnli: premise: {row.premise} hypothesis: {row.hypothesis}"
        encoding = self.tokenizer.encode_plus(
            input_, padding="max_length", max_length=256, return_tensors="pt"
        )
        input_ids, attention_masks = encoding["input_ids"], encoding["attention_mask"]

        outputs = self.model.generate(
            input_ids=input_ids,
            attention_mask=attention_masks,
            max_length=8,
            early_stopping=True,
            return_dict_in_generate=True,
            output_scores=True,
        )

        transition_scores = self.model.compute_transition_scores(
            outputs.sequences, outputs.scores, normalize_logits=True
        )

        return {
            "label": " ".join(
                self.tokenizer.decode(
                    output, skip_special_tokens=True, clean_up_tokenization_spaces=True
                )
                for output in outputs.sequences
            ),
            "score": np.exp(transition_scores[0][0].numpy()),
        }
