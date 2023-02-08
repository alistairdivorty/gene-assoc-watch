# GeneAssocWatch

This monorepo contains a machine learning pipeline for performing zero-shot extraction of gene–disease associations from medical literature, a web application for serving model inferences, and an application for provisioning the required cloud infrastructure.

- [ML Pipeline](#1-ml-pipeline)
- [Web Backend](#2-web-backend)
- [Web Frontend](#3-web-frontend)
- [AWS CDK App](#4-aws-cdk-app)

## 1. ML Pipeline

- [What It Does](#11-what-it-does)
- [Local Setup](#12-local-setup)
  - [Prerequisites](#121-prerequisites)
  - [Set Up Environment](#122-set-up-environment)
- [Testing](#13-testing)
- [Directory Structure](#14-directory-structure)
- [Start a `SparkSession`](#15-starting-a-sparksession)
- [Run Job in Local Development Environment](#16-run-job-in-local-development-environment)
- [Deployment](#17-deployment)
  - [Packaging Dependencies](#171-packaging-dependencies)
  - [Deploy CloudFormation Stack](#172-deploy-cloudformation-stack)
- [Run Job in Production Environment](#18-run-job-in-production-environment)

### 1.1. What It Does

This is an application for performing distributed batch processing of ML workloads on the [Apache Spark](https://spark.apache.org/) framework.

### 1.2. Local Setup

#### 1.2.1. Prerequisites

- [Conda package and environment manager](https://docs.conda.io/projects/conda/en/latest/)
- [OpenJDK 11](https://adoptopenjdk.net/releases.html)

#### 1.2.2 Set up environment

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

### 1.3. Testing

This project uses the [pytest](https://docs.pytest.org/en/7.1.x/) software testing framework. Run `DEBUG=1 pytest` to execute all tests. Use the `-s` flag to prevent pytest from capturing data written to STDOUT, and the `-v` flag to increase the verbosity of test output.

### 1.4. Directory Structure

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

### 1.5. Starting a `SparkSession`

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

### 1.6. Run Job in Local Development Environment

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

### 1.7. Deployment

#### 1.7.1. Packaging Dependencies

The project includes a Dockerfile with instructions for packaging dependencies into archives that can be uploaded to [Amazon S3](https://aws.amazon.com/s3/) and downloaded to Spark executors. Dependencies can be packaged for deployment by running the command `docker build -f artifacts.Dockerfile -o . .`. A TAR archive containing the Python dependencies and an uber-JAR containing the Java dependencies will be outputted to a directory named `artifacts`.

The project also includes a Dockerfile with instructions for fetching model files that must be uploaded to Amazon S3 and downloaded to Spark executors. Model files can be readied for deployment by running the command `docker build -f assets.Dockerfile -o . .`. Model files will be outputted to the directory `assets/models`.

#### 1.7.2 Deploy CloudFormation Stack

To deploy the application using the [AWS CDK Toolkit](https://docs.aws.amazon.com/cdk/v2/guide/cli.html), change the current working directory to `cdk` and run `cdk deploy GeneAssocEMRServerlessStack`. See the [AWS CDK app](#4-aws-cdk-app) section for details of how to set up the AWS CDK Toolkit. The AWS CDK app takes care of uploading the deployment artifacts and assets to the project's dedicated S3 bucket. The app also creates and uploads a JSON configuration file named `models.json` that specifies the S3 URI for the `models` folder. For production job runs, this file needs to be submitted to the Spark cluster by passing the URI as an argument to the `--files` option. The AWS CDK app outputs the ID of the EMR Serverless application created by the CloudFormation stack, along with the [ARN](https://docs.aws.amazon.com/general/latest/gr/aws-arns-and-namespaces.html) for the [IAM](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html) execution role, S3 URIs for the `jobs`, `config`, `artifacts`, `models` and `logs` folders, and the S3 URI for the ZIP archive containing a custom Java KeyStore.

### 1.8. Run Job in Production Environment

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

## 2. Web App Backend

- [What It Does](#21-what-it-does)
- [Local Setup](#22-local-setup)
  - [Prerequisites](#221-prerequisites)
  - [Set Up Environment](#222-set-up-environment)
- [Directory Structure](#23-directory-structure)
- [Deployment](#24-deployment)

### 2.1. What It Does

This is a web application backend for serving model inferences architected using the [Flask](https://flask.palletsprojects.com/en/2.2.x/) framework.

### 2.2. Local Setup

#### 2.2.1. Prerequisites

- [Conda package and environment manager](https://docs.conda.io/projects/conda/en/latest/)

#### 2.2.2. Set Up Environment

Start by installing the conda package and environment manager. The [Miniconda](https://docs.conda.io/en/latest/miniconda.html#) installer can be used to install a small, bootstrap version of Anaconda that includes only conda, Python, the packages they depend on, and a small number of other useful packages, including pip.

To create a fresh conda environment, run `conda create -n <env-name> python=3.10`, substituting `<env-name>` with your desired environment name. Once the environment has been created, activate the environment by running `conda activate <env-name>`.

Install the Python dependencies for the backend by running `pip install -r requirements.txt` from the `web-backend` directory.

Set the necessary environment variables by modifying the command below as required depending on the location of your Miniconda installation and environment name.

```shell
conda env config vars set \
PYTHONPATH=<path/to/project/dir>/web-backend:$HOME/opt/miniconda3/envs/<env-name>/lib/python3.10/site-packages
```

Reactivate the environment by running `conda activate <env-name>`.

To create a file for storing environment variables, run `cp .env.example .env` from the `web-backend` directory.

Run `flask run` from the `web-backend` directory to start the local Flask development server. By default the server is started on port 5000.

### 2.3. Directory Structure

```
📦web-backend
 ┣ 📂api
 ┃ ┃ ┣ 📜__init__.py
 ┃ ┃ ┣ 📜articles.py
 ┃ ┃ ┗ 📜home.py
 ┃ ┣ 📂app
 ┃ ┃ ┗ 📜__init__.py
 ┣ 📜.env
 ┣ 📜.env.example
 ┣ 📜.gitignore
 ┣ 📜Dockerfile
 ┣ 📜main.py
 ┣ 📜requirements.txt
 ┗ 📜zappa_settings.json
```

### 2.4. Deployment

To deploy the application using the [AWS CDK Toolkit](https://docs.aws.amazon.com/cdk/v2/guide/cli.html), change the current working directory to `cdk` and run `cdk deploy GeneAssocWebAppStack`. See the [AWS CDK app](#4-aws-cdk-app) section for details of how to set up the AWS CDK Toolkit. The CDK app takes care of bundling the project files using the [Zappa](https://github.com/zappa/Zappa) build tool for deployment to [AWS Lambda](https://aws.amazon.com/lambda/).

## 3. Web App Frontend

- [What It Does](#31-what-it-does)
- [Local Setup](#32-local-setup)
  - [Prerequisites](#321-prerequisites)
  - [Set Up Environment](#322-set-up-environment)
- [Directory Structure](#33-directory-structure)
- [Deployment](#34-deployment)

### 3.1. What It Does

This is a web application frontend for allowing users to view model inferences architected using the [Next.js](https://nextjs.org/) framework.

### 3.2. Local Setup

#### 3.2.1. Prerequisites

- [Node.js JavaScript runtime environment](https://nodejs.org/en/download/)

#### 3.2.2. Set Up Environment

Install the Node dependencies by running `npm install` from the `nextjs-app` directory.

Run `npm run dev` to start the local Next.js development server. By default the server is started on port 3000. Navigate to `http://localhost:3000` to view the site in a web browser.

### 3.3. Directory Structure

```
📦web-frontend
 ┣ 📂components
 ┃ ┣📜Article.tsx
 ┃ ┗📜...
 ┣ 📂context
 ┃ ┗📜articlesContext.tsx
 ┣ 📂hooks
 ┃ ┣📜useArticlesContext.tsx
 ┃ ┗📜useIntersectionObserver.tsx
 ┣ 📂pages
 ┃ ┣ 📂api
 ┃ ┃ ┗ 📜hello.ts
 ┃ ┣ 📜_app.tsx
 ┃ ┣ 📜_document.tsx
 ┃ ┗ 📜index.tsx
 ┣ 📂public
 ┃ ┣ 📜favicon.ico
 ┃ ┗ 📜robots.txt
 ┣ 📂styles
 ┃ ┗ 📜globals.css
 ┣ 📂types
 ┃ ┗ 📜index.ts
 ┣ 📜.eslintrc.json
 ┣ 📜.gitignore
 ┣ 📜.prettierrc.json
 ┣ 📜next-env.d.ts
 ┣ 📜next.config.js
 ┣ 📜package-lock.json
 ┣ 📜package.json
 ┣ 📜postcss.config.js
 ┣ 📜tailwind.config.js
 ┗ 📜tsconfig.json
```

### 3.4. Deployment

To deploy the application using the [AWS CDK Toolkit](https://docs.aws.amazon.com/cdk/v2/guide/cli.html), change the current working directory to `cdk` and run `cdk deploy GeneAssocWebAppStack`. See the [AWS CDK app](#4-aws-cdk-app) section for details of how to set up the AWS CDK Toolkit. The CDK app takes care of bundling the project files using the [standalone output](https://nextjs.org/docs/advanced-features/output-file-tracing) build mode for deployment to [AWS Lambda](https://aws.amazon.com/lambda/).

## 4. AWS CDK App

- [What It Does](#41-what-it-does)
- [Local Setup](#42-local-setup)
  - [Prerequisites](#421-prerequisites)
  - [Set Up Environment](#422-set-up-environment)
- [Directory Structure](#43-directory-structure)
- [Deployment](#44-deployment)

### 4.1. What It Does

The [AWS Cloud Development Kit (CDK)](https://docs.aws.amazon.com/cdk/v2/guide/home.html) is a framework for defining cloud infrastructure in code and provisioning it through [AWS CloudFormation](https://aws.amazon.com/cloudformation/). This is an AWS CDK application that defines the cloud infrastructure required by the services contained in this repository.

### 4.2. Local Setup

#### 4.2.1. Prerequisites

- [Node.js JavaScript runtime environment](https://nodejs.org/en/download/)
- [Python 3.10](https://www.python.org/downloads/)
- [pip package installer](https://pip.pypa.io/en/stable/installation/)

#### 4.2.2. Set Up Environment

To install the [CDK Toolkit](https://docs.aws.amazon.com/cdk/v2/guide/cli.html) (a CLI tool for interacting with a CDK app) using the [Node Package Manager](https://www.npmjs.com/), run the command `npm install -g aws-cdk`. The CDK Toolkit needs access to AWS credentials. Access to your credentials can be configured using the [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) by running `aws configure` and following the prompts.

Install the Python dependencies by running `pip install -r requirements.txt` from the `cdk` directory.

### 4.3. Directory Structure

```
📦cdk
 ┣ 📂cdk
 ┃ ┣ 📜emr_serverless_stack.py
 ┃ ┗ 📜web_app_stack.py
 ┣ 📂tests
 ┣ 📜.env
 ┣ 📜.env.example
 ┣ 📜.gitignore
 ┣ 📜README.md
 ┣ 📜app.py
 ┣ 📜cdk.context.json
 ┣ 📜cdk.json
 ┗ 📜requirements.txt
```

### 4.4. Deployment

To deploy all the stacks defined by the application, change the current working directory to `cdk` and run `cdk deploy --all`.
