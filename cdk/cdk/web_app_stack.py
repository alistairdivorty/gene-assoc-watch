import os
from aws_cdk import (
    Stack,
    BundlingOptions,
    DockerImage,
    Duration,
    aws_ec2 as ec2,
    aws_s3_assets as s3assets,
    aws_lambda as lambda_,
    aws_apigateway as apigw,
    aws_events as events,
    aws_events_targets as events_targets,
    aws_route53 as route53,
    aws_certificatemanager as acm,
    aws_route53_targets as route53_targets,
)
from constructs import Construct


class WebAppStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = ec2.Vpc.from_lookup(self, id="vpc", vpc_name="VPC")

        deployment_bundle = s3assets.Asset(
            self,
            "BundledApp",
            path="../web-backend",
            bundling=BundlingOptions(
                image=DockerImage.from_build("../web-backend", platform="linux/amd64"),
                command=[
                    "sh",
                    "-c",
                    """
                        python3 -m venv venv;
                        . venv/bin/activate;
                        python3 -m pip install -r requirements.txt;
                        zappa package production -o bundle.zip;
                        cp bundle.zip /asset-output/bundle.zip
                    """,
                ],
            ),
        )

        lambda_function = lambda_.Function(
            self,
            "Function",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_bucket(
                deployment_bundle.bucket, deployment_bundle.s3_object_key
            ),
            handler="handler.lambda_handler",
            timeout=Duration.seconds(30),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            allow_public_subnet=True,
            memory_size=512,
            environment={
                "MONGODB_CONNECTION_URI": os.environ["MONGODB_CONNECTION_URI"]
            },
        )

        api = apigw.LambdaRestApi(self, "RestAPI", handler=lambda_function)

        event_rule = events.Rule(
            self,
            "FunctionWarming",
            schedule=events.Schedule.rate(Duration.minutes(5)),
        )

        event_rule.add_target(events_targets.LambdaFunction(lambda_function))

        hosted_zone = route53.HostedZone.from_hosted_zone_attributes(
            self,
            "HostedZone",
            zone_name="geneassocwatch.com",
            hosted_zone_id=os.environ["HOSTED_ZONE_ID"],
        )

        api.add_domain_name(
            "CustomDomain",
            certificate=acm.Certificate(
                self,
                "Certificate",
                domain_name="api.geneassocwatch.com",
                validation=acm.CertificateValidation.from_dns(hosted_zone),
            ),
            domain_name="api.geneassocwatch.com",
        )

        route53.ARecord(
            self,
            "ARecord",
            zone=hosted_zone,
            record_name="api.geneassocwatch.com",
            target=route53.RecordTarget.from_alias(route53_targets.ApiGateway(api)),
        )
