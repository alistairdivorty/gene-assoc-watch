## ML Pipeline

- [What It Does](#1-what-it-does)
- [Local Setup](#2-local-setup)
  - [Prerequisites](#21-prerequisites)
  - [Set Up Environment](#22-set-up-environment)
- [Testing](#3-testing)
- [Directory Structure](#4-directory-structure)
- [Start a `SparkSession`](#5-starting-a-sparksession)
- [Run Job in Local Development Environment](#6-run-job-in-local-development-environment)
- [Deployment](#7-deployment)
  - [Packaging Dependencies](#71-packaging-dependencies)
  - [Deploy CloudFormation Stack](#72-deploy-cloudformation-stack)
- [Run Job in Production Environment](#8-run-job-in-production-environment)

### 1. What It Does

This is an application for performing distributed batch processing of ML workloads on the [Apache Spark](https://spark.apache.org/) framework.

### 2. Local Setup

#### 2.1. Prerequisites

- [Conda package and environment manager](https://docs.conda.io/projects/conda/en/latest/)
- [OpenJDK 11](https://adoptopenjdk.net/releases.html)

#### 2.2 Set up environment

Start by installing the conda package and environment manager. The [Miniconda](https://docs.conda.io/en/latest/miniconda.html#) installer can be used to install a small, bootstrap version of Anaconda that includes only conda, Python, the packages they depend on, and a small number of other useful packages, including pip.

To create a fresh conda environment, run `conda create -n <env-name> python=3.10`, substituting `<env-name>` with your desired environment name. Once the environment has been created, activate the environment by running `conda activate <env-name>`.

Next, install the project dependencies, including distributions of [Apache Hadoop](https://hadoop.apache.org/) and [Apache Spark](https://spark.apache.org/), by running `pip install -r requirements_dev.txt` from the `ml-pipeline` directory.

Set the necessary environment variables by modifying the command below as required depending on the location of your Miniconda installation and environment name.

```shell
conda env config vars set \
PYTHONPATH=<path/to/project/dir>/ml-pipeline:$HOME/opt/miniconda3/envs/<env-name>/lib/python3.10/site-packages \
SPARK_HOME=$HOME/opt/miniconda3/envs/<env-name>/lib/python3.10/site-packages/pyspark \
PYSPARK_PYTHON=$HOME/opt/miniconda3/envs/<env-name>/bin/python \
PYSPARK_DRIVER_PYTHON=$HOME/opt/miniconda3/envs/<env-name>/bin/python \
OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
```

Reactivate the environment by running `conda activate <env-name>`.

To create a file for storing environment variables, run `cp .env.example .env`.

To download model files needed for local inference, run `docker build -f assets.Dockerfile -o . .`. Model files will be outputted to the `assets/models` directory.

### 3. Testing

This project uses the [pytest](https://docs.pytest.org/en/7.1.x/) software testing framework. Run `DEBUG=1 pytest` to execute all tests. Use the `-s` flag to prevent pytest from capturing data written to STDOUT, and the `-v` flag to increase the verbosity of test output.

### 4. Directory Structure

```
📦ml-pipeline
 ┣ 📂artifacts
 ┃ ┣ 📜packages.tar.gz
 ┃ ┗ 📜uber-JAR.jar
 ┣ 📂assets
 ┃ ┗ 📂models
 ┃ ┃ ┣ 📂sentence_pair_classifier
 ┃ ┃ ┗ 📂sentence_detector_dl_xx
 ┣ 📂config
 ┣ 📂data
 ┣ 📂finetuning
 ┣ 📂inference
 ┃ ┣ 📂services
 ┃ ┃ ┣ 📜logger.py
 ┃ ┃ ┗ 📜spark.py
 ┃ ┣ 📂transformers
 ┃ ┃ ┣ 📜sentence_pair_classifier.py
 ┃ ┃ ┗ 📜sentence_tokenizer.py
 ┃ ┗ 📜sentence_pair_classifier.py
 ┣ 📂jobs
 ┃ ┗ 📜gda.py
 ┣ 📂scripts
 ┃ ┗ 📜package_models.py
 ┣ 📂tests
 ┃ ┣ 📜conftest.py
 ┃ ┣ 📜fixtures.py
 ┃ ┣ 📜classifier_test.py
 ┃ ┗ 📜gda_test.py
 ┣ 📜.env
 ┣ 📜.env.example
 ┣ 📜.gitignore
 ┣ 📜artifacts.Dockerfile
 ┣ 📜assets.Dockerfile
 ┣ 📜pom.xml
 ┣ 📜pyproject.toml
 ┣ 📜pytest.ini
 ┣ 📜requirements.txt
 ┗ 📜requirements_dev.txt
```

The `jobs` directory contains Python scripts that can be sent to a Spark cluster and executed as jobs. The `inference` directory contains the custom [Transformers](https://spark.apache.org/docs/latest/ml-pipeline.html#transformers) and [MLflow Python model](https://www.mlflow.org/docs/latest/python_api/mlflow.pyfunc.html) classes that provide the core functionality.

### 5. Starting a `SparkSession`

The `inference.services.spark` module provides a `start_spark` function for creating a [SparkSession](https://spark.apache.org/docs/latest/sql-getting-started.html#starting-point-sparksession) on the worker node and registering an application with the cluster. The following example shows how to create a `SparkSession` and specify the [Maven coordinates](https://maven.apache.org/pom.html#Maven_Coordinates) of [JAR](https://docs.oracle.com/javase/8/docs/technotes/guides/jar/jarGuide.html) files to be downloaded and transferred to the cluster.

```python
from inference.services.spark import start_spark

spark, log, config = start_spark(
    jars_packages=[
        "org.apache.hadoop:hadoop-aws:3.3.2",
        "org.mongodb.spark:mongo-spark-connector:10.0.5",
        "com.johnsnowlabs.nlp:spark-nlp_2.12:4.2.1",
    ],
    spark_config={
        "spark.mongodb.read.connection.uri": os.environ["MONGODB_CONNECTION_URI"],
        "spark.mongodb.write.connection.uri": os.environ["MONGODB_CONNECTION_URI"],
        "fs.s3a.aws.credentials.provider": "com.amazonaws.auth.DefaultAWSCredentialsProviderChain",
        "spark.kryoserializer.buffer.max": "2000M",
        "spark.driver.memory": "10g",
    },
)
```

Note that only the `app_name` argument will take effect when calling `start_spark` from a job submitted to a cluster via the `spark-submit` script in Spark's `bin` directory. The purpose of the other arguments is to facilitate local development and testing from within an interactive terminal session or Python console. The `start_spark` function detects the execution environment in order to determine which arguments the session builder should use – the function arguments or the `spark-submit` arguments. The `config` dictionary is populated with configuration values contained in JSON files located at paths specified by the `files` argument or `--files` option. The top level keys of the `config` dictionary correspond to the names of the JSON files submitted to the cluster.

### 6. Run Job in Local Development Environment

The following example shows how to submit a job to a local standalone Spark cluster, specify the [Maven coordinates](https://maven.apache.org/pom.html#Maven_Coordinates) of [JAR](https://docs.oracle.com/javase/8/docs/technotes/guides/jar/jarGuide.html) files to be downloaded and transferred to the cluster, and supply configuration values to the `SparkConf` object that will be passed to the `SparkContext`.

```shell
$SPARK_HOME/bin/spark-submit \
--master "local[*]" \
--packages "org.apache.hadoop:hadoop-aws:3.3.2,org.mongodb.spark:mongo-spark-connector:10.0.5,com.johnsnowlabs.nlp:spark-nlp-m1_2.12:4.2.1" \
--conf "spark.mongodb.read.connection.uri=mongodb+srv://<username>:<password>@•••••.•••••.mongodb.net/geneassoc" \
--conf "spark.mongodb.write.connection.uri=mongodb+srv://<username>:<password>@•••••.•••••.mongodb.net/geneassoc" \
--conf "fs.s3a.aws.credentials.provider=com.amazonaws.auth.DefaultAWSCredentialsProviderChain" \
--conf "spark.driver.memory=10g" \
--conf "spark.kryoserializer.buffer.max=2000M" \
jobs/gda.py
```

### 7. Deployment

#### 7.1. Packaging Dependencies

The project includes a Dockerfile with instructions for packaging dependencies into archives that can be uploaded to [Amazon S3](https://aws.amazon.com/s3/) and downloaded to Spark executors. Dependencies can be packaged for deployment by running the command `docker build -f artifacts.Dockerfile -o . .`. A TAR archive containing the Python dependencies and an uber-JAR containing the Java dependencies will be outputted to a directory named `artifacts`.

The project also includes a Dockerfile with instructions for fetching model files that must be uploaded to Amazon S3 and downloaded to Spark executors. Model files can be readied for deployment by running the command `docker build -f assets.Dockerfile -o . .`. Model files will be outputted to the directory `assets/models`.

#### 7.2 Deploy CloudFormation Stack

To deploy the application using the [AWS CDK Toolkit](https://docs.aws.amazon.com/cdk/v2/guide/cli.html), change the current working directory to `cdk` and run `cdk deploy EMRServerlessStack`. See the [AWS CDK app](../README.md#4-aws-cdk-app) section of the main README for details of how to set up the AWS CDK Toolkit. The AWS CDK app takes care of uploading the deployment artifacts and assets to the project's dedicated S3 bucket. The app also creates and uploads a JSON configuration file named `models.json` that specifies the S3 URI for the `models` folder. For production job runs, this file needs to be submitted to the Spark cluster by passing the URI as an argument to the `--files` option. The AWS CDK app outputs the ID of the EMR Serverless application created by the CloudFormation stack, along with the [ARN](https://docs.aws.amazon.com/general/latest/gr/aws-arns-and-namespaces.html) for the [IAM](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html) execution role, S3 URIs for the `jobs`, `config`, `artifacts`, `models` and `logs` folders, and the S3 URI for the ZIP archive containing a custom Java KeyStore.

### 8. Run Job in Production Environment

The following is an example of how to submit a job to the [EMR Serverless](https://docs.aws.amazon.com/emr/latest/EMR-Serverless-UserGuide/emr-serverless.html) application deployed by the [AWS CDK app](#6-aws-cdk-app) using the [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-welcome.html). The placeholder values should be replaced with the values outputted by the CDK app after deployment.

```shell
aws emr-serverless start-job-run \
    --execution-timeout-minutes 200 \
    --region eu-west-1 \
    --application-id <application-ID> \
    --execution-role-arn <role-ARN> \
    --job-driver '{
        "sparkSubmit": {
            "entryPoint": "s3://<bucket-name>/jobs/gda.py",
            "entryPointArguments": [],
            "sparkSubmitParameters": "--conf spark.archives=s3://<bucket-name>/artifacts/packages.tar.gz#environment --conf spark.jars=s3://<bucket-name>/artifacts/uber-JAR.jar --files=s3://<bucket-name>/config/models.json --conf spark.emr-serverless.driverEnv.PYSPARK_DRIVER_PYTHON=./environment/bin/python --conf spark.emr-serverless.driverEnv.PYSPARK_PYTHON=./environment/bin/python --conf spark.emr-serverless.executorEnv.PYSPARK_PYTHON=./environment/bin/python --conf spark.emr-serverless.driver.disk=30g --conf spark.emr-serverless.executor.disk=30g --conf spark.executor.instances=5 --conf spark.mongodb.read.connection.uri=mongodb+srv://<username>:<password>@•••••.•••••.mongodb.net/geneassoc --conf spark.mongodb.write.connection.uri=mongodb+srv://<username>:<password>@•••••.•••••.mongodb.net/geneassoc --conf spark.kryoserializer.buffer.max=2000M"
        }
    }' \
    --configuration-overrides '{
        "monitoringConfiguration": {
            "s3MonitoringConfiguration": {
                "logUri": "s3://<bucket-name>/logs/"
            }
        }
    }'
```
