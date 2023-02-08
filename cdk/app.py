#!/usr/bin/env python3
import os
from dotenv import load_dotenv
import aws_cdk as cdk
from cdk.emr_serverless_stack import EMRServerlessStack

load_dotenv()


app = cdk.App()

env = cdk.Environment(
    account=os.getenv("CDK_DEFAULT_ACCOUNT"),
    region=os.getenv("CDK_DEFAULT_REGION"),
)

EMRServerlessStack(app, "GeneAssocEMRServerlessStack", env=env)

app.synth()
