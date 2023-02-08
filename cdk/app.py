#!/usr/bin/env python3
import os
from dotenv import load_dotenv
import aws_cdk as cdk
from cdk.web_app_stack import WebAppStack
from cdk.emr_serverless_stack import EMRServerlessStack

load_dotenv()


app = cdk.App()

env = cdk.Environment(
    account=os.getenv("CDK_DEFAULT_ACCOUNT"),
    region=os.getenv("CDK_DEFAULT_REGION"),
)

WebAppStack(app, "GeneAssocWebAppStack", env=env)
EMRServerlessStack(app, "GeneAssocEMRServerlessStack", env=env)

app.synth()
