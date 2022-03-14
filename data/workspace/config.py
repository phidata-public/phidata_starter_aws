from phidata.app.devbox import Devbox, DevboxDevModeArgs
from phidata.app.postgres import PostgresDb
from phidata.infra.aws.config import AwsConfig
from phidata.infra.aws.create.iam.role import create_glue_iam_role
from phidata.infra.aws.resource.group import AwsResourceGroup
from phidata.infra.aws.resource.s3 import S3Bucket
from phidata.infra.docker.config import DockerConfig
from phidata.workspace import WorkspaceConfig

# Workspace name
ws_name = "data"

######################################################
## Configure the dev environment running locally on docker
## Applications:
##  - Devbox: A containerized environment for testing and debugging workflows.
##  - Dev database: A postgres db running in a container for storing dev data
######################################################

dev_pg_name = "dev-pg"
dev_pg = PostgresDb(
    name=dev_pg_name,
    # You can connect to this db on port 5532 (on the host machine)
    container_host_port=5532,
    postgres_user="dev",
    postgres_db="dev",
    postgres_password="dev",
)
dev_pg_conn_id = "dev_pg"
devbox = Devbox(
    # Mount Aws config from on the container, will be used for interacting with aws resouces
    mount_aws_config=True,
    # Init Airflow webserver when the container starts
    init_airflow_webserver=True,
    # use_cache=False will recreate the container every time we run `phi ws up`
    use_cache=False,
    dev_mode=DevboxDevModeArgs(),
    db_connections={dev_pg_conn_id: dev_pg.get_connection_url_docker()},
    create_airflow_test_user=True,
)
dev_docker_config = DockerConfig(
    env="dev",
    apps=[devbox, dev_pg],
)

######################################################
## Configure the prd environment running on AWS
## AWS Resources:
##  - S3 bucket
##  - EKS cluster + nodegroup + vpc stack
######################################################

# s3 bucket for storing data
# TODO: prefix the bucket name with your team name and make it globally unique
data_s3_bucket = S3Bucket(
    name=f"phi-starter-aws-{ws_name}-warehouse",
    acl="private",
)
glue_iam_role = create_glue_iam_role(
    name=f"{ws_name}-glue-crawler-role",
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
    # name should match the folder containing
    # the products and workspace directories. default: data
    # this should also match the module name in setup.py
    name=ws_name,
    # default_env="dev",
    docker=[dev_docker_config],
    aws=[prd_aws_config],
    # aws_region="us-east-1",
)
