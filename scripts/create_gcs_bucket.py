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
    bucket_or_name="raw_article",
    # https://cloud.google.com/storage/docs/locations#location_recommendations
    location="eu",  # Multiregion
)

# Create Data Profile Bucket for stage data
gcs_bucket = client.create_bucket(
    bucket_or_name="stage_article_profile",
    # https://cloud.google.com/storage/docs/locations#location_recommendations
    location="eu",  # Multiregion
)
