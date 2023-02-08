FROM alpine:latest as download_sparknlp_models

RUN apk update && apk add unzip

RUN mkdir models

RUN wget \
    https://s3.amazonaws.com/auxdata.johnsnowlabs.com/public/models/sentence_detector_dl_xx_2.7.0_2.4_1609610616998.zip

RUN unzip \
    sentence_detector_dl_xx_2.7.0_2.4_1609610616998.zip \
    -d models/sentence_detector_dl_xx

FROM download_sparknlp_models as package_transformers_models

RUN pip install mlflow

COPY inference inference

COPY pyproject.toml .

RUN pip install .

COPY finetuning/t5_pubmed_mnli models/t5_pubmed_mnli

COPY scripts/package_models.py .

RUN mkdir models

RUN python package_models.py

FROM scratch as export

COPY --from=download_sparknlp_models models assets/models

COPY --from=package_transformers_models models assets/models