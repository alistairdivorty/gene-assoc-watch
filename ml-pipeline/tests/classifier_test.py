from inference.transformers.sentence_pair_classifier import SentencePairClassifier
from pyspark.ml import PipelineModel


class TestClassifier:
    def test_sentence_pairs_classified(self, spark):
        df = spark.createDataFrame(
            [
                {
                    "premise": "This study examined the effects of Her2 blockade on tumor angiogenesis, vascular architecture, and hypoxia in Her2(+) and Her2(-) MCF7 xenograft tumors.",
                    "hypothesis": "Gene–disease association.",
                }
            ]
        )

        df = PipelineModel(
            stages=[
                SentencePairClassifier(
                    premiseCol="premise",
                    hypothesisCol="hypothesis",
                    outputCol="output",
                )
            ]
        ).transform(df)

        df.show(truncate=False)

        row = df.first()
        assert row is not None
        assert row["output"]["label"] == "entailment"
