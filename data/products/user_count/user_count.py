from phidata.asset.file import File
from phidata.asset.table.sql.postgres import PostgresTable
from phidata.product import DataProduct
from phidata.workflow.download.url_to_file import DownloadUrlToFile
from phidata.workflow.upload.file_to_sql import UploadFileToSql

from data.workspace.config import dev_pg, dev_pg_conn_id

##############################################################################
## This example shows how to build a data pipeline that calculates
## daily user count using postgres.
## Steps:
##  1. Download user_activity data from a URL.
##  2. Upload user_activity data to postgres table
##  3. Run a SQL query to calculate daily user count
##############################################################################

# Step 1: Download user_activity data from a URL.
# Define a File object which points to
#   <ws_root_dir>/storage/user_count/user_activity.csv
user_activity_csv = File(name="user_activity.csv", file_dir="user_count")
# Create a Workflow to download the user_activity data from a URL
download_file = DownloadUrlToFile(
    file=user_activity_csv,
    url="https://raw.githubusercontent.com/phidata-public/demo-data/main/dau_2021_10_01.csv",
)

# Step 2: Upload user_activity data to postgres table
# Define a postgres table named `user_activity`. Use the conn_id for dev_pg from the workspace config
user_activity_table = PostgresTable(
    name="user_activity",
    db_conn_id=dev_pg_conn_id,
    db_conn_url=dev_pg.get_connection_url_local(),
)
# Create a Workflow to load the file downloaded above to the PostgresTable
upload_file = UploadFileToSql(
    file=user_activity_csv,
    sql_table=user_activity_table,
)

# Step 3: Run a SQL query to calculate daily user count

# Create a DataProduct for these tasks
user_count_dp = DataProduct(name="user_count", workflows=[download_file, upload_file])

# Create the airflow DAG
dag = user_count_dp.create_airflow_dag()
