""" Google Cloud Storage JSONL to Google Cloud Storage Parquet """

import io
import pathlib

import pyarrow
from prefect import flow, get_run_logger, task
from pyarrow import json

from src.config import IngestInterimArticleDataParam
from src.etl.extract import download_blob_to_file
from src.etl.load import upload_blob_from_file, upload_blob_from_memory
from src.utils import profile_data, rmtree


@task(
    retries=0,
    retry_delay_seconds=3,
)
def download_raw_article_data_to_local_jsonl(
    bucket_name: str, destination_directory: pathlib.Path, year: int, month_num: int
):
    logger = get_run_logger()

    if not destination_directory.exists():
        logger.info(f"Creating directory '{destination_directory}'")
        destination_directory.mkdir(exist_ok=True)

    file_name = f"raw_article_data_{year}_{month_num}.json"
    source_blob_name = file_name
    destination_file_name = destination_directory / file_name

    blob = download_blob_to_file(
        bucket_name=bucket_name,
        source_blob_name=source_blob_name,
        destination_file_name=destination_file_name,
    )
    logger.info(
        f"Downloaded contents from Blob '{source_blob_name}' from bucket '{bucket_name}' in memory and wrote to file '{destination_file_name}'"
    )

    return blob


@task(
    retries=0,
    retry_delay_seconds=3,
)
def convert_local_jsonl_to_pyarrow_table(
    source_directory: pathlib.Path, year: int, month_num: int
):
    logger = get_run_logger()

    source_file_name = source_directory / f"raw_article_data_{year}_{month_num}.json"
    table = json.read_json(source_file_name)
    logger.info(f"Read file '{source_file_name}' and stored data in pyarrow table")
    logger.info(
        f"The table contains {table.num_columns} columns and {table.num_rows} rows"
    )

    return table


@task(
    retries=0,
    retry_delay_seconds=3,
)
def profile_interim_article_data(
    table: pyarrow.Table, source_directory: pathlib.Path, year: int, month_num: int
):
    logger = get_run_logger()

    df = table.to_pandas()
    file_path = source_directory / f"interim_article_data_{year}_{month_num}.html"
    report = profile_data(df=df, file_path=file_path)

    logger.info(f"Store pandas profile report here: '{file_path}'")

    return report


@task(
    retries=3,
    retry_delay_seconds=3,
)
def upload_interim_article_data_profile(
    destination_bucket_name: str,
    source_directory: pathlib.Path,
    year: int,
    month_num: int,
):
    logger = get_run_logger()

    file_name = f"interim_article_data_{year}_{month_num}.html"
    source_file_name = source_directory / file_name
    destination_blob_name = file_name

    upload_blob_from_file(
        source_file_name=source_file_name,
        bucket_name=destination_bucket_name,
        destination_blob_name=destination_blob_name,
    )

    logger.info(
        f"Uploaded contents from '{source_file_name}' to Blob '{destination_blob_name}' in bucket '{destination_bucket_name}'"
    )


@task(
    retries=3,
    retry_delay_seconds=3,
)
def upload_interim_article_data_to_blob_storage(
    bucket_name: str, table: pyarrow.Table, year: int, month_num: int
):
    logger = get_run_logger()

    destination_blob_name = f"interim_article_data_{year}_{month_num}.parquet"

    buffer = io.BytesIO()
    table.to_pandas().to_parquet(buffer, engine="auto", compression="snappy")

    upload_blob_from_memory(
        bucket_name=bucket_name,
        contents=buffer.getvalue(),
        destination_blob_name=destination_blob_name,
    )

    logger.info(
        f"Uploaded contents from pyarrow table to Blob '{destination_blob_name}' in bucket '{bucket_name}'"
    )


@task(
    retries=3,
    retry_delay_seconds=3,
)
def delete_local_temp_directory_and_files(directory: pathlib.Path):
    logger = get_run_logger()

    if directory.exists():
        logger.info(
            f"Starting to remove files in directory '{directory}' and the directory itself"
        )

        rmtree(directory)

        if not directory.exists():
            logger.info(f"Directory '{directory}' and all its files have been deleted")


@flow
def ingest_interim_article_data(params: IngestInterimArticleDataParam):
    directory = pathlib.Path.cwd() / "temp"

    download_raw_article_data_to_local_jsonl(
        bucket_name=params.raw_data_bucket_name,
        destination_directory=directory,
        year=params.year,
        month_num=params.month_num,
    )

    table = convert_local_jsonl_to_pyarrow_table(
        source_directory=directory, year=params.year, month_num=params.month_num
    )

    if params.is_manual_ingestion:
        profile_interim_article_data(
            table=table,
            source_directory=directory,
            year=params.year,
            month_num=params.month_num,
        )

        upload_interim_article_data_profile(
            destination_bucket_name=params.interim_data_profile_bucket_name,
            source_directory=directory,
            year=params.year,
            month_num=params.month_num,
        )

    upload_interim_article_data_to_blob_storage(
        bucket_name=params.interim_data_bucket_name,
        table=table,
        year=params.year,
        month_num=params.month_num,
    )

    delete_local_temp_directory_and_files(directory=directory)


if __name__ == "__main__":
    ingest_interim_article_data(IngestInterimArticleDataParam())
