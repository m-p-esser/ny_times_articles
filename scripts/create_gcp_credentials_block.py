"""Programmatically create GCP Credentials block for Prefect"""

from prefect_gcp import GcpCredentials
from dotenv import dotenv_values

env_variables = dotenv_values(".env")

GCP_CREDENTIAL_BLOCK_NAME = env_variables["GCP_CREDENTIAL_BLOCK_NAME"]

with open("credentials/prefect_service_account.json", "r") as f:
    service_account = f.read()

GcpCredentials(service_account_info=service_account).save(
    GCP_CREDENTIAL_BLOCK_NAME, overwrite=True
)
