import datetime
import xml.etree.ElementTree as ET
from pyspark.sql.functions import col, collect_list, struct, to_date
from pyspark.sql import Window
from pyspark.ml import Pipeline, PipelineModel
from pyspark.ml.feature import SQLTransformer
from pyspark.sql import SparkSession
from pyspark.sql import DataFrame
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    ArrayType,
)
from inference.services.spark import start_spark
from inference.transformers.sentence_pair_classifier import SentencePairClassifier
from inference.transformers.sentence_tokenizer import SentenceTokenizer


def main():
    spark, logger, config = start_spark()

    df = extract_(spark)

    df = transform_(df)

    load_(df)

    spark.stop()


def extract_(spark: SparkSession) -> DataFrame:
    file_rdd = spark.read.text("data/articles.xml", wholetext=True).rdd
    schema = StructType(
        [
            StructField(
                "pmid",
                StringType(),
                False,
            ),
            StructField(
                "journal",
                StringType(),
                True,
            ),
            StructField(
                "firstPublicationDate",
                StringType(),
                False,
            ),
            StructField(
                "authors",
                ArrayType(
                    StructType(
                        [
                            StructField(
                                "fullName",
                                StringType(),
                                True,
                            ),
                            StructField(
                                "lastName",
                                StringType(),
                                True,
                            ),
                            StructField(
                                "firstName",
                                StringType(),
                                True,
                            ),
                            StructField(
                                "initials",
                                StringType(),
                                True,
                            ),
                        ]
                    )
                ),
                True,
            ),
            StructField(
                "title",
                StringType(),
                True,
            ),
            StructField(
                "abstract",
                StringType(),
                True,
            ),
        ]
    )
    return file_rdd.flatMap(parse_xml).toDF(schema)


def parse_xml(rdd):
    results = []
    root = ET.fromstring(rdd[0])

    for result in root.findall("./resultList/result[pmid]"):
        record = []

        pmid = result.find("./pmid")
        assert pmid is not None
        record.append(pmid.text)

        journal_title = result.find("./journalInfo/journal/title")
        record.append(journal_title.text if journal_title is not None else None)

        first_publication_date = result.find("./firstPublicationDate")
        record.append(
            first_publication_date.text if first_publication_date is not None else None
        )

        def parse_author_name(element):
            name_map = {}
            for n in ["fullName", "lastName", "firstName", "initials"]:
                e = element.find(f"./{n}")
                if e is not None:
                    name_map[n] = e.text
            return name_map

        authors = list(
            filter(
                None,
                map(
                    lambda e: parse_author_name(e),
                    result.findall("./authorList/author"),
                ),
            )
        )
        record.append(authors if authors != [] else None)

        title = result.find("./title")
        record.append(title.text if title is not None else None)

        abstract = result.find("./abstractText")
        record.append(abstract.text if abstract is not None else None)

        results.append(record)

    return results


def transform_(df: DataFrame) -> DataFrame:
    pipeline = Pipeline().setStages(
        [
            SentencePairClassifier()
            .setPremiseCol("abstract")
            .setHypothesis("This example is a gene–disease association.")
            .setOutputCol("abstractPrediction"),
            SQLTransformer().setStatement(
                "SELECT * FROM __THIS__ WHERE abstractPrediction.label = 'entailment' AND abstractPrediction.score > 0.8"
            ),
            SentenceTokenizer().setInputCol("abstract").setOutputCol("sentences"),
            SQLTransformer().setStatement(
                "SELECT EXPLODE(sentences) AS sentence, * FROM __THIS__"
            ),
            SentencePairClassifier()
            .setPremiseCol("sentence.result")
            .setHypothesis("This example is a gene–disease association."),
        ]
    )

    df = (
        pipeline.fit(df)
        .transform(df)
        .filter((col("output").label == "entailment") & (col("output").score > 0.7))
        .withColumn(
            "gda",
            struct(
                [
                    col("sentence.result").alias("sentence"),
                    col("output").score.alias("score"),
                ],
            ),
        )
        .withColumn(
            "gda",
            collect_list("gda").over(Window.partitionBy("pmid")),
        )
        .dropDuplicates(["pmid"])
        .withColumn(
            "firstPublicationDate", to_date(col("firstPublicationDate"), "yyyy-MM-dd")
        )
        .select(
            "pmid",
            "journal",
            "firstPublicationDate",
            "authors",
            "title",
            "abstract",
            "gda",
        )
    )

    return df


def load_(df: DataFrame):
    (
        df.write.format("mongodb")
        .mode("append")
        .option("collection", "pubmedArticles")
        .option("operationType", "replace")
        .option("idFieldList", "pmid")
        .save()
    )


if __name__ == "__main__":
    main()
