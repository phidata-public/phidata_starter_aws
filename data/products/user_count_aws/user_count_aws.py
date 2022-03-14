from phidata.asset.file import File
from phidata.asset.aws.s3 import S3Object
from phidata.product import DataProduct
from phidata.workflow.download.url_to_file import DownloadUrlToFile
from phidata.workflow.upload.file_to_s3 import UploadFileToS3

from data.workspace.config import data_s3_bucket

##############################################################################
## This example shows how to build a data pipeline that calculates
## daily user count using s3, athena and glue.
## Steps:
##  1. Download user_activity data from a URL.
##  2. Upload user_activity data to a S3 bucket.
##  3. Create a glue crawler for this table
##  4. Run an athena query to calculate daily user count
##############################################################################

# Step 1: Download user_activity data from a URL.
# Define a File object which points to
#   <ws_root_dir>/storage/user_count/user_activity.csv
user_activity_csv = File(name="user_activity.csv", file_dir="user_count_aws")
# Create a Workflow to download the user_activity data from a URL
download_file = DownloadUrlToFile(
    file=user_activity_csv,
    url="https://raw.githubusercontent.com/phidata-public/demo-data/main/dau_2021_10_01.csv",
)

# Step 2: Upload user_activity data to a S3 object.
# Define a S3 object for this file. Use the s3 bucket from the workspace config.
user_activity_s3 = S3Object(
    key="user_count_aws/user_activity.csv",
    bucket=data_s3_bucket,
)
# Create a Workflow to upload the file downloaded above to our S3 object
upload_file = UploadFileToS3(
    file=user_activity_csv,
    s3_object=user_activity_s3,
)

# Step 3: Create a glue crawler for this table
# Step 4: Run an athena query to calculate daily user count

# Create a DataProduct for these tasks
user_count_aws_dp = DataProduct(name="user_count_aws", workflows=[download_file, upload_file])

# Create the airflow DAG
dag = user_count_aws_dp.create_airflow_dag()
