import os
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
from pyspark.sql import DataFrame
from pyspark.ml import Pipeline
from sparknlp.base import DocumentAssembler
from sparknlp.annotator import (
    DocumentNormalizer,
    SentenceDetectorDLModel,
)


class SentenceTokenizer(
    Transformer,
    HasInputCol,
    HasOutputCol,
    DefaultParamsReadable,
    DefaultParamsWritable,
):
    emrfsModelPath = Param(
        Params._dummy(),
        "emrfsModelPath",
        "The location, in URI format, of the Spark NLP model parent folder.",
        typeConverter=TypeConverters.toString,
    )

    @keyword_only
    def __init__(self, inputCol=None, outputCol=None, emrfsModelPath=None):
        super().__init__()
        self._setDefault(
            inputCol="input",
            outputCol="output",
            emrfsModelPath=None,
        )
        kwargs = self._input_kwargs
        self.setParams(**kwargs)

    @keyword_only
    def setParams(self, inputCol=None, outputCol=None, emrfsModelPath=None):
        kwargs = self._input_kwargs
        return self._set(**kwargs)

    def setInputCol(self, inputCol):
        return self.setParams(inputCol=inputCol)

    def setOutputCol(self, outputCol):
        return self.setParams(outputCol=outputCol)

    def setEmrfsModelPath(self, emrfsModelPath):
        return self.setParams(emrfsModelPath=emrfsModelPath)

    def getInputCol(self):
        return self.getOrDefault(self.inputCol)

    def getOutputCol(self):
        return self.getOrDefault(self.outputCol)

    def getModelUri(self, model_name):
        emrfs_model_path = self.getOrDefault(self.emrfsModelPath)
        if not emrfs_model_path:
            return os.path.join("assets/models", model_name)
        return os.path.join(emrfs_model_path, model_name)

    def _transform(self, df: DataFrame) -> DataFrame:
        document_assembler = (
            DocumentAssembler().setInputCol(self.getInputCol()).setOutputCol("document")
        )

        document_normalizer = (
            DocumentNormalizer()
            .setInputCols("document")
            .setOutputCol("normalizedDocument")
            .setAction("clean")
            .setPatterns(["<[^>]*>"])
            .setReplacement(" ")
            .setPolicy("pretty_all")
            .setLowercase(False)
        )

        sentence_detector = (
            SentenceDetectorDLModel.load(self.getModelUri("sentence_detector_dl_xx"))
            .setInputCols(["normalizedDocument"])
            .setOutputCol(self.getOutputCol())
        )

        return (
            Pipeline(
                stages=[
                    document_assembler,
                    document_normalizer,
                    sentence_detector,
                ]
            )
            .fit(df)
            .transform(df)
        )
