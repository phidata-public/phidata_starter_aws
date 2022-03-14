from phidata.app.airflow import Airflow
from phidata.app.databox import Databox
from phidata.app.jupyter import Jupyter
from phidata.app.devbox import Devbox, DevboxDevModeArgs
from phidata.app.postgres import PostgresDb
from phidata.infra.aws.config import AwsConfig
from phidata.infra.aws.resource.cloudformation import CloudFormationStack
from phidata.infra.aws.resource.eks.cluster import EksCluster
from phidata.infra.aws.resource.eks.node_group import EksNodeGroup
from phidata.infra.aws.resource.group import AwsResourceGroup
from phidata.infra.aws.resource.s3 import S3Bucket
from phidata.infra.docker.config import DockerConfig
from phidata.infra.k8s.config import K8sConfig
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
    # TODO: update to read from a secrets file
    postgres_password="dev",
)
devbox = Devbox(
    # Mount Aws config on the container
    mount_aws_config=True,
    # Init Airflow webserver when the container starts
    init_airflow_webserver=True,
    # Init Airflow scheduler as a deamon process
    # init_airflow_scheduler=True,
    # Creates a link between the airflow_dir and airflow_home on the container
    # Useful when debugging the airflow conf
    link_airflow_home=True,
    # use_cache=False implies the container will be
    # recreated every time you run `phi ws up`
    use_cache=False,
    dev_mode=DevboxDevModeArgs(),
    db_connections={"dev_pg": dev_pg.get_connection_url_docker()},
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
# TODO: please prefix the bucket name with your team name to make it globally unique
data_s3_bucket = S3Bucket(
    name=f"{ws_name}-warehouse",
    acl="private",
)
data_vpc_stack = CloudFormationStack(
    name=f"{ws_name}-vpc",
    template_url="https://amazon-eks.s3.us-west-2.amazonaws.com/cloudformation/2020-10-29/amazon-eks-vpc-private-subnets.yaml",
    ## uncomment when workspace is production-ready
    ## skip_delete=True implies this resource will NOT be deleted with `phi ws down`
    # skip_delete=True,
)
data_eks_cluster = EksCluster(
    name=f"{ws_name}-cluster",
    vpc_stack=data_vpc_stack,
    # skip_delete=True,
)
data_eks_nodegroup = EksNodeGroup(
    name=f"{ws_name}-ng",
    eks_cluster=data_eks_cluster,
    min_size=2,
    max_size=5,
    # skip_delete=True,
)
aws_resources = AwsResourceGroup(
    s3_buckets=[data_s3_bucket],
    cloudformation_stacks=[data_vpc_stack],
    eks_cluster=data_eks_cluster,
    eks_nodegroups=[data_eks_nodegroup],
)
prd_aws_config = AwsConfig(
    env="prd",
    resources=aws_resources,
)

######################################################
## Applications running on EKS Cluster
##  - Postgres Database: For storing prod data
##  - Databox: A containerized environment for testing prod workflows before merging.
##  - Airflow: For orchestrating prod workflows
##  - Jupyter: For analyzing prod data
######################################################

prd_pg_name = "prd-pg"
# The password is created on K8s as a Secret, it needs to be in base64
# echo "prd" | base64
prd_pg_password = "cHJkCg=="
prd_pg = PostgresDb(
    name=prd_pg_name,
    postgres_user="prd",
    postgres_db="prd",
    # TODO: update to read from a secrets file
    postgres_password=prd_pg_password,
)
databox = Databox()
airflow = Airflow(enabled=False)
jupyter = Jupyter(enabled=False)

prd_k8s_config = K8sConfig(
    env="prd",
    apps=[prd_pg, databox, airflow, jupyter],
    eks_cluster=data_eks_cluster,
)

######################################################
## Configure the workspace
######################################################
workspace = WorkspaceConfig(
    name=ws_name,
    default_env="dev",
    docker=[dev_docker_config],
    k8s=[prd_k8s_config],
    aws=[prd_aws_config],
)
