from pathlib import Path

from phidata.app.airflow import Airflow
from phidata.app.databox import Databox
from phidata.app.jupyter import Jupyter
from phidata.app.devbox import Devbox, DevboxDevModeArgs
from phidata.app.postgres import PostgresDb
from phidata.app.traefik import IngressRoute, LoadBalancerProvider
from phidata.infra.aws.config import AwsConfig
from phidata.infra.aws.resource.acm.certificate import AcmCertificate
from phidata.infra.aws.resource.cloudformation import CloudFormationStack
from phidata.infra.aws.resource.eks.cluster import EksCluster
from phidata.infra.aws.resource.eks.node_group import EksNodeGroup
from phidata.infra.aws.resource.group import AwsResourceGroup
from phidata.infra.aws.resource.s3 import S3Bucket
from phidata.infra.docker.config import DockerConfig
from phidata.infra.k8s.config import K8sConfig
from phidata.infra.k8s.create.core.v1.service import ServiceType
from phidata.workspace import WorkspaceConfig
from phidata.infra.k8s.create.apps.v1.deployment import CreateDeployment
from phidata.infra.k8s.create.core.v1.container import CreateContainer
from phidata.infra.k8s.create.core.v1.service import CreateService
from phidata.infra.k8s.create.common.port import CreatePort
from phidata.infra.k8s.create.group import CreateK8sResourceGroup
from phidata.utils.common import (
    get_default_service_name,
    get_default_container_name,
    get_default_deploy_name,
    get_default_pod_name,
)

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
    # runs locally in a docker container and has no sensitive info
    postgres_password="dev",
)
devbox = Devbox(
    # Mount Aws credentials on the container
    mount_aws_credentials=True,
    # Init Airflow webserver when the container starts
    init_airflow_webserver=True,
    # Init Airflow scheduler as a deamon process,
    # init_airflow_scheduler=True,
    # Create a soft link from the workspace/airflow to airflow_home
    # Useful when debugging the airflow conf
    link_airflow_home=True,
    # use_cache=False implies the container will be
    # recreated every time you run `phi ws up`
    use_cache=False,
    dev_mode=DevboxDevModeArgs(),
    db_connections={"dev_pg": dev_pg.get_connection_url_docker()},
)
dev_docker_config = DockerConfig(
    env="dev",
    apps=[devbox, dev_pg],
)

######################################################
## Configure the prd environment running on AWS
## Infrastructure:
##  - S3 bucket
##  - EKS cluster + nodegroup
##  - ACM certificate for awsdataplatform.com
## Applications:
##  - Databox: A containerized environment for running prod workflows.
##  - Jupyter: For analyzing prod data
##  - Airflow: For orchestrating prod workflows
##  - Postgres Database: For storing prod data
##  - Traefik: The Ingress which routes web requests to our infrastructure
##      allowing us to access the airflow dashboard and jupyter notebooks
##  - WhoAmiI: A tiny server for checking our infrastructure is working
######################################################

######################################################
## AWS Resources
######################################################

# Name your data platform
ws_name = "aws-data-platform"
# The domain for your data platform
domain = "awsdataplatform.com"
ws_dir_path = Path(__file__).parent.resolve()

certificate = AcmCertificate(
    name=domain,
    domain_name=domain,
    subject_alternative_names=[
        f"www.{domain}",
        f"traefik.{domain}",
        f"whoami.{domain}",
        f"airflow.{domain}",
        f"superset.{domain}",
        f"jupyter.{domain}",
        f"meta.{domain}",
        f"*.{domain}",
    ],
    store_cert_summary=True,
    certificate_summary_file=ws_dir_path.joinpath("aws", "acm", domain),
)
# s3 bucket for storing data
data_s3_bucket = S3Bucket(
    name=f"phi-{ws_name}",
    acl="private",
)
data_vpc_stack = CloudFormationStack(
    name=f"{ws_name}-vpc",
    template_url="https://amazon-eks.s3.us-west-2.amazonaws.com/cloudformation/2020-10-29/amazon-eks-vpc-private-subnets.yaml",
    # skip_delete=True implies this resource will NOT be deleted with `phi ws down`
    # uncomment when workspace is production-ready
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
    acm_certificates=[certificate],
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
######################################################

prd_pg_name = "aws-demo-prd-db"
# The password is created on K8s as a Secret, it needs to be in base64
# echo "prd" | base64
prd_pg_password = "cHJkCg=="
prd_pg = PostgresDb(
    name=prd_pg_name,
    postgres_user="prd",
    postgres_password=prd_pg_password,
    postgres_db="prd",
)
databox = Databox()
airflow = Airflow(enabled=False)
jupyter = Jupyter(enabled=False)

# Whoami
whoami_name = "whoami"
whoami_port = CreatePort(
    name="http",
    container_port=80,
    service_port=80,
    target_port="http",
)
whoami_container = CreateContainer(
    container_name=get_default_container_name(whoami_name),
    app_name=whoami_name,
    image_name="traefik/whoami",
    image_tag="v1.8.0",
    ports=[whoami_port],
)
whoami_deployment = CreateDeployment(
    deploy_name=get_default_deploy_name(whoami_name),
    pod_name=get_default_pod_name(whoami_name),
    app_name=whoami_name,
    containers=[whoami_container],
)
whoami_service = CreateService(
    service_name=get_default_service_name(whoami_name),
    app_name=whoami_name,
    deployment=whoami_deployment,
    ports=[whoami_port],
)
whoami_k8s_rg = CreateK8sResourceGroup(
    name=whoami_name,
    services=[whoami_service],
    deployments=[whoami_deployment],
)

# Traefik Ingress
routes = [
    {
        "match": f"Host(`whoami.{domain}`)",
        "kind": "Rule",
        "services": [
            {
                "name": whoami_service.service_name,
                "port": whoami_port.service_port,
            }
        ],
    },
]
traefik_ingress_route = IngressRoute(
    name="traefik",
    domain_name=domain,
    access_logs=True,
    web_enabled=True,
    web_routes=routes,
    # The dashboard is available at traefik.{domain.com}
    dashboard_enabled=True,
    # The dashboard is gated behind a user password, which is generated using
    #   htpasswd -nb user password | openssl base64
    dashboard_auth_users="cGFuZGE6JGFwcjEkSVYxWng4eXYkYmtFOHc4cGVSLnNzVEwyMTJINnJCLwoK",
    # Use a LOAD_BALANCER service provided by AWS
    service_type=ServiceType.LOAD_BALANCER,
    load_balancer_provider=LoadBalancerProvider.AWS,
    # Use a Network Load Balancer: recommended
    use_nlb=True,
    nlb_target_type="ip",
    load_balancer_scheme="internet-facing",
    ## You can add an ACM certificate and enable HTTPS/websecure
    # forward_web_to_websecure=True,
    websecure_enabled=True,
    websecure_routes=routes,
    ## Add your ACM certificate ARN here
    acm_certificate_summary_file=certificate.certificate_summary_file,
)

prd_k8s_config = K8sConfig(
    env="prd",
    # namespace="demo",
    apps=[prd_pg, databox, airflow, jupyter, traefik_ingress_route],
    create_resources=[whoami_k8s_rg],
    eks_cluster=data_eks_cluster,
)

######################################################
## Configure the workspace
######################################################
workspace = WorkspaceConfig(
    default_env="dev",
    docker=[dev_docker_config],
    k8s=[prd_k8s_config],
    aws=[prd_aws_config],
)
