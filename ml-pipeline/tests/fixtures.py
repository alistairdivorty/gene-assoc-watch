import pytest, os
from distutils.util import strtobool
from dotenv import load_dotenv, find_dotenv
from inference.services.spark import start_spark

load_dotenv(find_dotenv(), override=True)


@pytest.fixture(scope="session")
def spark():
    sparknlp_artifact_id = {
        0: "spark-nlp_2.12",
        1: "spark-nlp-m1_2.12",
    }[strtobool(os.environ["MAC_M1"])]

    spark, *_ = start_spark(
        jars_packages=[
            "org.apache.hadoop:hadoop-aws:3.3.2",
            f"com.johnsnowlabs.nlp:{sparknlp_artifact_id}:4.2.1",
            "org.mongodb.spark:mongo-spark-connector:10.0.5",
        ],
        spark_config={
            "fs.s3a.aws.credentials.provider": "com.amazonaws.auth.DefaultAWSCredentialsProviderChain",
            "spark.kryoserializer.buffer.max": "2000M",
            "spark.driver.memory": "10g",
            "spark.mongodb.read.connection.uri": os.environ["MONGODB_CONNECTION_URI"],
            "spark.mongodb.write.connection.uri": os.environ["MONGODB_CONNECTION_URI"],
        },
    )

    yield spark

    spark.stop()
