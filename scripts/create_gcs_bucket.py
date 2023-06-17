"""Programmatically create Google Cloud Storage (Bucket)"""

from dotenv import dotenv_values
from google.cloud import storage
from prefect.filesystems import GCS
from prefect_gcp import GcpCredentials

# Load Env variables
env_variables = dotenv_values(".env")

# Load Credentials and Config
gcp_credentials = GcpCredentials.load(env_variables["GCP_CREDENTIAL_BLOCK_NAME"])
project_id = gcp_credentials.project

# Init Client
client = storage.Client(project=project_id)

# Create Bucket for raw data
gcs_bucket = client.create_bucket(
    bucket_or_name="raw_article_data",
    # https://cloud.google.com/storage/docs/locations#location_recommendations
    location="eu",  # Multiregion
)

# Create Bucket for interim data (= structured data)
gcs_bucket = client.create_bucket(
    bucket_or_name="interim_article_data",
    # https://cloud.google.com/storage/docs/locations#location_recommendations
    location="eu",  # Multiregion
)

# Create Data Profile Bucket for interim data (= structured data)
gcs_bucket = client.create_bucket(
    bucket_or_name="interim_article_data_profile",
    # https://cloud.google.com/storage/docs/locations#location_recommendations
    location="eu",  # Multiregion
)
