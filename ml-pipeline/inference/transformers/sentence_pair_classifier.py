import os
import mlflow
from pyspark.sql import SparkSession
from pyspark import keyword_only
from pyspark.ml import Transformer
from pyspark.ml.param.shared import (
    HasInputCol,
    HasOutputCol,
    Param,
    Params,
    TypeConverters,
)
from pyspark.ml.util import DefaultParamsReadable, DefaultParamsWritable
from pyspark.sql.functions import lit, col, from_json, struct
from pyspark.sql import DataFrame
from pyspark.sql.types import StructType, StructField, StringType, FloatType


class SentencePairClassifier(
    Transformer,
    HasInputCol,
    HasOutputCol,
    DefaultParamsReadable,
    DefaultParamsWritable,
):
    premiseCol = Param(
        Params._dummy(),
        "premiseCol",
        "Name of column containing the NLI premise.",
        typeConverter=TypeConverters.toString,
    )

    hypothesis = Param(
        Params._dummy(),
        "hypothesis",
        "The NLI hypothesis.",
        typeConverter=TypeConverters.toString,
    )

    emrfsModelPath = Param(
        Params._dummy(),
        "emrfsModelPath",
        "The location, in URI format, of the MLflow model parent folder.",
        typeConverter=TypeConverters.toString,
    )

    @keyword_only
    def __init__(
        self,
        premiseCol=None,
        hypothesis=None,
        outputCol=None,
        emrfsModelPath=None,
    ):
        super().__init__()
        self._setDefault(
            premiseCol="premise",
            outputCol="output",
            emrfsModelPath=None,
        )
        kwargs = self._input_kwargs
        self.setParams(**kwargs)

    @keyword_only
    def setParams(
        self,
        premiseCol=None,
        hypothesis=None,
        outputCol=None,
        emrfsModelPath=None,
    ):
        kwargs = self._input_kwargs
        return self._set(**kwargs)

    def setOutputCol(self, outputCol):
        return self.setParams(outputCol=outputCol)

    def setPremiseCol(self, premiseCol):
        return self.setParams(premiseCol=premiseCol)

    def setHypothesis(self, hypothesis):
        return self.setParams(hypothesis=hypothesis)

    def setEmrfsModelPath(self, emrfsModelPath):
        return self.setParams(emrfsModelPath=emrfsModelPath)

    def getPremiseCol(self):
        return self.getOrDefault(self.premiseCol)

    def getHypothesis(self):
        return self.getOrDefault(self.hypothesis)

    def getModelUri(self):
        model_name = "sentence_pair_classifier"
        emrfs_model_path = self.getOrDefault(self.emrfsModelPath)
        if not emrfs_model_path:
            return os.path.join("assets/models", model_name)
        return os.path.join(emrfs_model_path, model_name)

    def _transform(self, df: DataFrame) -> DataFrame:
        spark = SparkSession.getActiveSession()

        predict = mlflow.pyfunc.spark_udf(
            spark,
            model_uri=self.getModelUri(),
            result_type="string",
            env_manager="local",
        )

        return df.withColumn(
            self.getOutputCol(),
            from_json(
                predict(
                    struct(
                        col(self.getPremiseCol()).alias("premise"),
                        lit(self.getHypothesis()).alias("hypothesis"),
                    )
                ),
                StructType(
                    [
                        StructField(
                            "label",
                            StringType(),
                            False,
                        ),
                        StructField(
                            "score",
                            FloatType(),
                            False,
                        ),
                    ]
                ),
            ),
        )
