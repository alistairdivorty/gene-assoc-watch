from aws_cdk import (
    Stack,
    CfnOutput,
    RemovalPolicy,
    Size,
    aws_emrserverless as emrs,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_iam as iam,
    aws_ec2 as ec2,
)
from constructs import Construct


class EMRServerlessStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = ec2.Vpc.from_lookup(self, id="vpc", vpc_name="VPC")

        bucket = s3.Bucket(
            self,
            "Bucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            versioned=False,
            public_read_access=False,
        )

        s3deploy.BucketDeployment(
            self,
            "DeployCode",
            sources=[s3deploy.Source.asset("../ml-pipeline/jobs")],
            destination_bucket=bucket,
            destination_key_prefix="jobs",
        )

        s3deploy.BucketDeployment(
            self,
            "DeployArtifacts",
            sources=[s3deploy.Source.asset("../ml-pipeline/artifacts")],
            destination_bucket=bucket,
            destination_key_prefix="artifacts",
            ephemeral_storage_size=Size.gibibytes(5),
            memory_limit=5120,
            prune=False,
        )

        s3deploy.BucketDeployment(
            self,
            "DeployModels",
            sources=[s3deploy.Source.asset("../ml-pipeline/assets/models")],
            destination_bucket=bucket,
            destination_key_prefix="models",
            ephemeral_storage_size=Size.gibibytes(10),
            memory_limit=10240,
            prune=False,
        )

        s3deploy.BucketDeployment(
            self,
            "DeployConfigFiles",
            sources=[
                s3deploy.Source.asset("../ml-pipeline/config"),
                s3deploy.Source.json_data(
                    "models.json",
                    {"emrfsModelPath": bucket.s3_url_for_object("models/")},
                ),
            ],
            destination_bucket=bucket,
            destination_key_prefix="config",
        )

        CfnOutput(self, "JobsURI", value=bucket.s3_url_for_object("jobs/"))
        CfnOutput(self, "ConfigsURI", value=bucket.s3_url_for_object("config/"))
        CfnOutput(self, "ArtifactsURI", value=bucket.s3_url_for_object("artifacts/"))
        CfnOutput(self, "LogsURI", value=bucket.s3_url_for_object("logs/"))

        s3_access_policy = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    actions=[
                        "s3:ListBucket",
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:DeleteObject",
                    ],
                    effect=iam.Effect.ALLOW,
                    resources=[
                        bucket.bucket_arn,
                        f"{bucket.bucket_arn}/*",
                    ],
                ),
            ]
        )

        glue_access_policy = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    actions=[
                        "glue:GetDatabase",
                        "glue:GetDataBases",
                        "glue:CreateTable",
                        "glue:GetTable",
                        "glue:GetTables",
                        "glue:GetPartition",
                        "glue:GetPartitions",
                        "glue:CreatePartition",
                        "glue:BatchCreatePartition",
                        "glue:GetUserDefinedFunctions",
                    ],
                    effect=iam.Effect.ALLOW,
                    resources=["*"],
                ),
            ]
        )

        emr_serverless_job_role = iam.Role(
            self,
            "emr-serverless-job-role",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("emr-serverless.amazonaws.com"),
            ),
            inline_policies={
                "S3Access": s3_access_policy,
                "GlueAccess": glue_access_policy,
            },
        )

        CfnOutput(self, "JobRoleArn", value=emr_serverless_job_role.role_arn)

        emr_serverless_security_group = ec2.SecurityGroup(
            self, "EMRServerlessSG", vpc=vpc
        )

        emr_serverless_app = emrs.CfnApplication(
            self,
            "SparkApp",
            release_label="emr-6.6.0",
            type="SPARK",
            name="gene-assoc",
            network_configuration=emrs.CfnApplication.NetworkConfigurationProperty(
                subnet_ids=vpc.select_subnets().subnet_ids,
                security_group_ids=[emr_serverless_security_group.security_group_id],
            ),
            auto_stop_configuration=emrs.CfnApplication.AutoStopConfigurationProperty(
                enabled=True, idle_timeout_minutes=1
            ),
        )

        CfnOutput(self, "ApplicationID", value=emr_serverless_app.attr_application_id)
