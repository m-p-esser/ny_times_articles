""" Sync Google Cloud Storage (Parquet) with Bigquery. PUSH Pattern that needs to be setup just for once for each Bigquery Table """

from google.cloud import bigquery
from google.cloud.exceptions import NotFound
from prefect import flow, get_run_logger, task
from prefect_gcp import GcpCredentials

from src.config import SyncArticleDataToBigquery


@task
def create_dataset(project_id: str, dataset_id: str):
    logger = get_run_logger()

    client = bigquery.Client(location="eu")

    dataset_reference = bigquery.DatasetReference(
        project=project_id, dataset_id=dataset_id
    )
    try:
        client.get_dataset(dataset_reference)
        logger.info(f"Dataset {dataset_reference} already exists")
        dataset_exists = True
    except NotFound:
        dataset_exists = False
        logger.info(f"Dataset {dataset_reference} is not found")

    if not dataset_exists:
        client.create_dataset(dataset_reference)
        logger.info(f"Created dataset '{dataset_reference}'")


@task
def sync_gcs_and_bigquery_table(
    project_id: str,
    dataset_id: str,
    table_id: str,
    source_uri: str,
    file_format: str = "PARQUET",
):
    logger = get_run_logger()

    client = bigquery.Client(location="eu")

    dataset_reference = bigquery.DatasetReference(
        project=project_id,
        dataset_id=dataset_id,
    )

    table_reference = bigquery.TableReference(
        dataset_ref=dataset_reference, table_id=table_id
    )

    table = bigquery.Table(table_ref=table_reference)

    external_config = bigquery.ExternalConfig(file_format)
    external_config.source_uris = [source_uri]
    table.external_data_configuration = external_config

    # Create a permanent table linked to the GCS file
    table = client.create_table(table)
    logger.info(f"Synced Bigquery table '{table}' with '{source_uri}'")


@flow
def sync_bigquery_article_data(params: SyncArticleDataToBigquery):
    gcp_credentials = GcpCredentials.load("ny-times-prefect-sa")

    create_dataset(
        project_id=gcp_credentials.project,
        dataset_id=params.dataset_id,
    )
    sync_gcs_and_bigquery_table(
        project_id=gcp_credentials.project,
        dataset_id=params.dataset_id,
        table_id=params.table_id,
        source_uri=params.source_uri,
    )


if __name__ == "__main__":
    sync_bigquery_article_data(params=SyncArticleDataToBigquery())
