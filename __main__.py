import pulumi
import pulumi_aws as aws
from pulumi_aws import s3, iam, lambda_, glue, rds

# Import networking resources
from resources.networking import vpc, private_subnets, security_group

# Load environment-specific configurations
config = pulumi.Config()
env = config.require("environment")  # dev, staging, or prod
bucket_name = f"{config.require('bucketName')}-{env}"
database_name = f"{config.require('databaseName')}{env}"
db_username = config.require_secret("dbUsername")
db_password = config.require_secret("dbPassword")

# Tags that will be applied to all resources
default_tags = {
    "Environment": env,
    "Project": config.require("projectName"),
    "ManagedBy": "pulumi"
}

# Create an S3 Bucket with proper configuration
bucket = s3.Bucket(bucket_name,
    acl="private",
    versioning=s3.BucketVersioningArgs(
        enabled=True,
    ),
    server_side_encryption_configuration=s3.BucketServerSideEncryptionConfigurationArgs(
        rule=s3.BucketServerSideEncryptionConfigurationRuleArgs(
            apply_server_side_encryption_by_default=s3.BucketServerSideEncryptionConfigurationRuleApplyServerSideEncryptionByDefaultArgs(
                sse_algorithm="AES256",
            ),
        ),
    ),
    lifecycle_rules=[s3.BucketLifecycleRuleArgs(
        id="archive-rule",
        # status="Enabled",
        enabled=True,
        transitions=[s3.BucketLifecycleRuleTransitionArgs(
            days=90,
                   storage_class="STANDARD_IA",
        )],
    )],
    tags=default_tags,
)

# Create IAM policies for S3 access
s3_access_policy = iam.Policy("s3AccessPolicy",
    description="Policy for accessing the data bucket",
    policy=bucket.arn.apply(lambda arn: f"""{{
        "Version": "2012-10-17",
        "Statement": [{{
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "{arn}",
                "{arn}/*"
            ]
        }}]
    }}"""),
)

# Create an IAM Role for Lambda with proper permissions
lambda_role = iam.Role("lambdaRole",
    assume_role_policy="""{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }""",
    tags=default_tags,
)

# Attach policies to the Lambda role
lambda_s3_policy_attachment = iam.RolePolicyAttachment("lambdaS3PolicyAttachment",
    role=lambda_role.name,
    policy_arn=s3_access_policy.arn,
)

lambda_basic_execution_attachment = iam.RolePolicyAttachment("lambdaBasicExecutionAttachment",
    role=lambda_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
)

lambda_vpc_policy_attachment = iam.RolePolicyAttachment(
    "lambdaVpcPolicyAttachment",
    role=lambda_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole",
)

# Define an RDS Serverless Cluster with proper security
db_subnet_group = rds.SubnetGroup("db-subnet-group",
    subnet_ids=[s.id for s in private_subnets],
    tags=default_tags,
)

db_cluster = rds.Cluster("dataWarehouse",
    engine="aurora-postgresql",
    engine_mode="provisioned",
    database_name=database_name,
    master_username=db_username,
    master_password=db_password,
    db_subnet_group_name=db_subnet_group.name,
    vpc_security_group_ids=[security_group.id],
    skip_final_snapshot=env != "prod",  # Take final snapshots in production
    final_snapshot_identifier="final-hn-snapshot" if env == "prod" else None,
    serverlessv2_scaling_configuration=rds.ClusterScalingConfigurationArgs(
        max_capacity=16 if env == "prod" else 8,
        min_capacity=4 if env == "prod" else 0,
        seconds_until_auto_pause=3600 if env == "dev" else None,
    ),
    backup_retention_period=7 if env == "prod" else 1,
    tags=default_tags,
)

# Create the Lambda Layer
lambda_layer = lambda_.LayerVersion(
    "requestsLayer",
    layer_name="requests-layer",
    code=pulumi.AssetArchive({
        ".": pulumi.FileArchive("./requests_layer"),  # Path to layer code
    }),
    compatible_runtimes=["python3.9"],  # Specify runtime compatibility
    description="Layer to import requests library",
)

# Lambda function with environment configuration
lambda_function = lambda_.Function("hackernewsLambda",
    runtime="python3.9",
    code=pulumi.AssetArchive({
        ".": pulumi.FileArchive("./lambda-code"),
    }),
    handler="index.lambda_handler",
    role=lambda_role.arn,
    environment=lambda_.FunctionEnvironmentArgs(
        variables={
            "BUCKET_NAME": bucket.id,
            "ENVIRONMENT": env,
            "DB_ENDPOINT": db_cluster.endpoint,
        }
    ),
    timeout=300,  # 5 minutes
    memory_size=512,  # Adjusted based on workload
    tags=default_tags,
    layers=[lambda_layer.arn],
)


# Export key resources
pulumi.export("environment", env)
pulumi.export("bucket_name", bucket.id)
pulumi.export("bucket_arn", bucket.arn)
pulumi.export("lambda_function_name", lambda_function.name)
pulumi.export("lambda_function_arn", lambda_function.arn)
pulumi.export("db_cluster_id", db_cluster.id)
pulumi.export("db_endpoint", db_cluster.endpoint)
