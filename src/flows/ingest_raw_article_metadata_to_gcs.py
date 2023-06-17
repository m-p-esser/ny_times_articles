import json
import pathlib

import requests
from prefect import flow, get_run_logger, task
from prefect.blocks.system import Secret

from src.etl.load import upload_blob_from_file
from src.utils import convert_to_jsonl


@task(
    retries=3,
    retry_delay_seconds=15,  # 12 second delay is recommended according to API developer documentation
    name="Request Archive API",
    description="Request New York Times Archive API (https://api.nytimes.com/svc/archive)",
)
def request_archive_api(
    year: int, month_num: int, api_key: str, version: int = 1
) -> dict:
    logger = get_run_logger()

    api_url_pattern = "https://api.nytimes.com/svc/archive/v{version}/{year}/{month_num}.json?api-key={api_key}"
    api_url = api_url_pattern.format(
        version=version, year=year, month_num=month_num, api_key=api_key
    )
    logger.info(f"Constructed the following endpoint url: {api_url}")
    query_params = {}

    try:
        logger.info(f"Requesting data from '{api_url}' using params '{query_params}'")
        r = requests.get(url=api_url, params=query_params)

        headers = r.headers
        logger.info(f"Received response with following header: {headers}")

        r.raise_for_status()

        data = r.json()["response"]["docs"]  # docs are articles
        logger.info("Received data as JSON")

    except requests.exceptions.HTTPError as error:
        print(f"HTTP error occurred: {error}")
    except requests.exceptions.ConnectionError as error:
        print(f"Connection error occurred: {error}")
    except requests.exceptions.Timeout as error:
        print(f"Timeout error occurred: {error}")
    except requests.exceptions.RequestException as error:
        print(f"An Request error occurred: {error}")

    return data


@task
def compress_file():
    pass


@task(
    retries=3,
    retry_delay_seconds=3,
    name="Store article metadata as JSONL",
    description="Store data in New line delimited JSON file (JSONL)",
)
def write_data_to_local_jsonl(
    data: list[dict], destination_directory: pathlib.Path, year: int, month_num: int
):
    logger = get_run_logger()

    logger.info(f"Creating directory '{destination_directory}' if it doesn't exist yet")
    destination_directory.mkdir(exist_ok=True)

    if destination_directory.is_dir():
        logger.info(f"Directory '{destination_directory}' exists")

        file_path = destination_directory / f"article_metadata_{year}_{month_num}.json"
        convert_to_jsonl(data=data, file_path=file_path)

        if file_path.exists():
            logger.info(f"Sucessfully created file '{file_path}'")


@task(
    retries=3,
    retry_delay_seconds=3,
    name="Upload article metadata as JSON file to GCS",
    description="Upload monthly article metadata data to Google Cloud / Blob Storage",
)
def upload_to_blob_storage(
    bucket_name: str, source_directory: pathlib.Path, year: int, month_num: int
):
    logger = get_run_logger()

    file_name = f"article_metadata_{year}_{month_num}.json"
    source_file_name = source_directory / file_name
    destination_blob_name = file_name

    upload_blob_from_file(
        bucket_name=bucket_name,
        source_file_name=source_file_name,
        destination_blob_name=destination_blob_name,
    )

    logger.info(
        f"Uploaded contents from '{source_file_name}' to Blob '{destination_blob_name}' in bucket '{bucket_name}'"
    )


@task(
    retries=3,
    retry_delay_seconds=3,
    name="Cleanup temp directory",
    description="Delete temp directory and all files in it",
)
def rmtree(directory: pathlib.Path):
    logger = get_run_logger()

    if directory.is_dir():
        logger.info(
            f"Starting to remove files in directory '{directory}' and the directory itself"
        )
        for child in directory.iterdir():
            if child.is_file():
                child.unlink()
            else:
                rmtree(child)
        directory.rmdir()

        if not directory.is_dir():
            logger.info(f"Directory '{directory}' doesn't exist anymore")


@flow
def ingest_raw_article_metadata_to_gcs():
    api_key = Secret.load("ny-times-api-key").get()
    YEAR = 2019
    MONTH_NUM = 1
    VERSION = 1
    BUCKET_NAME = "raw_article_metadata"

    directory = pathlib.Path.cwd() / "temp"

    try:
        data = request_archive_api(
            year=YEAR, month_num=MONTH_NUM, api_key=api_key, version=VERSION
        )

        directory = pathlib.Path.cwd() / "temp"
        write_data_to_local_jsonl(
            data=data,
            year=YEAR,
            destination_directory=directory,
            month_num=MONTH_NUM,
        )

        upload_to_blob_storage(
            bucket_name=BUCKET_NAME,
            source_directory=directory,
            year=YEAR,
            month_num=MONTH_NUM,
        )
    except Exception as e:
        print(f"An exception occured: {e}")
        rmtree(directory)


if __name__ == "__main__":
    ingest_raw_article_metadata_to_gcs()
