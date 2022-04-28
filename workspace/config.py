from phidata.app.postgres import PostgresDb
from phidata.infra.aws.config import AwsConfig, AwsResourceGroup
from phidata.infra.aws.create.iam.role import create_glue_iam_role
from phidata.infra.aws.resource.s3.bucket import S3Bucket
from phidata.infra.docker.config import DockerConfig
from phidata.workspace import WorkspaceConfig

ws_key = "phidata-starter-aws"

# -*- Define docker resources

# Dev database: A postgres instance for storing dev data
dev_db = PostgresDb(
    name="dev-db",
    db_user="dev",
    db_password="dev",
    db_schema="dev",
    # You can connect to this db on port 5532
    container_host_port=5532,
)

# -*- Define the DockerConfig
dev_docker_config = DockerConfig(
    apps=[dev_db],
)

# -*- Define AWS resources

# S3 bucket for storing data
data_s3_bucket = S3Bucket(
    name=f"{ws_key}-data",
    acl="private",
)

# Iam Role for Glue crawlers
glue_iam_role = create_glue_iam_role(
    name=f"{ws_key}-glue-crawler-role",
    s3_buckets=[data_s3_bucket],
    # skip_delete=True,
)

# -*- Define the AwsConfig
prd_aws_config = AwsConfig(
    env="prd",
    resources=AwsResourceGroup(
        iam_roles=[glue_iam_role],
        s3_buckets=[data_s3_bucket],
    ),
)

# -*- Define the WorkspaceConfig
workspace = WorkspaceConfig(
    default_env="dev",
    docker=[dev_docker_config],
    aws=[prd_aws_config],
)
