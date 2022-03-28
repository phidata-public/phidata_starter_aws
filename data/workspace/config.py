from phidata.app.postgres import PostgresDb
from phidata.infra.aws.config import AwsConfig
from phidata.infra.aws.create.iam.role import create_glue_iam_role
from phidata.infra.aws.resource.group import AwsResourceGroup
from phidata.infra.aws.resource.s3 import S3Bucket
from phidata.infra.docker.config import DockerConfig
from phidata.workspace import WorkspaceConfig

######################################################
## Configure docker resources
## Applications:
##  - Dev database: A postgres db running in a container for storing dev data
######################################################

dev_db = PostgresDb(
    name="dev-db",
    postgres_db="dev",
    postgres_user="dev",
    postgres_password="dev",
    # You can connect to this db on port 5532 (on the host machine)
    container_host_port=5532,
)
dev_docker_config = DockerConfig(
    apps=[dev_db],
)

######################################################
## Configure AWS resources:
##  - S3 bucket
##  - EKS cluster + nodegroup + vpc stack
######################################################

# s3 bucket for storing data
# TODO: replace the bucket name with your team name and make it globally unique
data_s3_bucket = S3Bucket(
    name=f"phidata-starter-aws",
    acl="private",
)
glue_iam_role = create_glue_iam_role(
    name=f"glue-crawler-role",
    s3_buckets=[data_s3_bucket],
)

aws_resources = AwsResourceGroup(
    s3_buckets=[data_s3_bucket],
    iam_roles=[glue_iam_role],
)
prd_aws_config = AwsConfig(
    env="prd",
    resources=aws_resources,
)

######################################################
## Configure the workspace
######################################################
workspace = WorkspaceConfig(
    default_env="dev",
    docker=[dev_docker_config],
    aws=[prd_aws_config],
    aws_region="us-east-1",
)
