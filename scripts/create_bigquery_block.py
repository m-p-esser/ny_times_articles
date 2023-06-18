"""Programmatically create Bigquery Block"""

from dotenv import dotenv_values
from prefect_gcp import GcpCredentials
from prefect_gcp.bigquery import BigQueryWarehouse

# Load Env variables
env_variables = dotenv_values(".env")

# Load Credentials and Config
gcp_credentials = GcpCredentials.load(env_variables["GCP_CREDENTIAL_BLOCK_NAME"])
project_id = gcp_credentials.project

bigquery_block_name = env_variables["BIGQUERY_BLOCK_NAME"]

block = BigQueryWarehouse(gcp_credentials=gcp_credentials)
block.save(bigquery_block_name, overwrite=True)
