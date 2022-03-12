import sys
from phidata.asset.file import File
from phidata.asset.s3 import S3Object
from phidata.product.chain import WorkflowChain
from phidata.workflow.download.url_to_file import DownloadUrlToFile
from phidata.workflow.upload.file_to_s3 import UploadFileToS3Object
from phidata.utils.cli_console import print_info

# sys.path.append("/usr/local/devbox")
print_info("syspath: {}".format(sys.path))
from aws_data_platform.workspace.config import data_s3_bucket

user_activity_csv = File(
    name="user_activity.csv",
    file_dir="dau",
)
s3_object = S3Object(bucket=data_s3_bucket.name, name="dau/user_activity.csv")

download_file = DownloadUrlToFile(
    file=user_activity_csv,
    url="https://raw.githubusercontent.com/phidata-public/demo-data/main/dau_2021_10_01.csv",
)
upload_file = UploadFileToS3Object(
    file=user_activity_csv,
    s3_object=s3_object,
)

chain = WorkflowChain(
    name="dau",
    workflows=[download_file, upload_file]
)

dag = chain.create_airflow_dag()
