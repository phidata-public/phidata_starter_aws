from phidata.asset.file import File
from phidata.asset.s3 import S3Object
from phidata.product.chain import WorkflowChain
from phidata.workflow.download.url_to_file import DownloadUrlToFile
from phidata.workflow.upload.file_to_s3 import UploadFileToS3Object

from data.workspace.config import data_s3_bucket

##############################################################################
## This example shows how to build a data pipeline for calculating
## daily user count using s3, athena and glue.
## Steps:
##  1. Download user_activity data from a URL.
##  2. Upload user_activity data to a S3 bucket.
##  3. Create a glue crawler for this table
##  4. Run an athena query to calculate dauly user count
##############################################################################

# Step 1: Download user_activity data from a URL.
# Define a File object which points to workspace_root/storage/dau/user_activity.csv
user_activity_csv = File(name="user_activity.csv", file_dir="dau")
# Create a Workflow to download URL into the file
download_file = DownloadUrlToFile(
    file=user_activity_csv,
    url="https://raw.githubusercontent.com/phidata-public/demo-data/main/dau_2021_10_01.csv",
)

# Step 2: Upload user_activity data to a S3 bucket.
# Define a S3 object for this file.
# We use the s3 bucket defined in the workspace config
user_activity_s3 = S3Object(bucket=data_s3_bucket.name, name="dau/user_activity.csv")
# Create a Workflow to upload the file downloaded above to our S3 object
upload_file = UploadFileToS3Object(
    file=user_activity_csv,
    s3_object=user_activity_s3,
)

# Step 3: Create a glue crawler for this table
# Step 4: Run an athena query to calculate daily user count

# Create a workflow-chain
chain = WorkflowChain(name="dau", workflows=[download_file, upload_file])

# Create the airflow DAG
dag = chain.create_airflow_dag()
