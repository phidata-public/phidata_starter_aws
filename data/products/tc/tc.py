from phidata.asset.file import File
from phidata.asset.s3 import S3Object
from phidata.product.chain import WorkflowChain
from phidata.workflow.upload.file_to_s3 import UploadFileToS3Object
from phidata.utils.cli_console import print_info

from workspace.config import data_s3_bucket


tech_crunch_companies_csv = File(
    name="tech_crunch_companies.csv",
    file_dir="tech_crunch",
)
tech_crunch_companies_s3 = S3Object(bucket=data_s3_bucket.name, name="tech_crunch/tech_crunch_companies.csv")

upload_file = UploadFileToS3Object(
    file=tech_crunch_companies_csv,
    s3_object=tech_crunch_companies_s3,
)

chain = WorkflowChain(
    name="tc",
    workflows=[upload_file]
)

dag = chain.create_airflow_dag()
