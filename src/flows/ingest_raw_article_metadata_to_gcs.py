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
def store_data_as_jsonl(data: list[dict], year: int, month_num: int):
    logger = get_run_logger()

    root_dir = pathlib.Path.cwd()
    temp_dir = root_dir / "temp"

    logger.info(f"Creating directory '{temp_dir}' if it doesn't exist yet")
    temp_dir.mkdir(exist_ok=True)

    if temp_dir.is_dir():
        logger.info(f"Directory '{temp_dir}' exists")

        file_path = temp_dir / f"article_metadata_{year}_{month_num}.json"
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
    bucket_name: str, directory: pathlib.Path, year: int, month_num: int
):
    logger = get_run_logger()

    file_name = f"article_metadata_{year}_{month_num}.json"
    source_file_name = directory / file_name
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
def rmtree():
    logger = get_run_logger()

    root_dir = pathlib.Path.cwd()
    temp_dir = root_dir / "temp"

    if temp_dir.is_dir():
        logger.info(
            f"Starting to remove files in directory '{temp_dir}' and the directory itself"
        )
        for child in temp_dir.iterdir():
            if child.is_file():
                child.unlink()
            else:
                rmtree(child)
        temp_dir.rmdir()

        if not temp_dir.is_dir():
            logger.info(f"Directory '{temp_dir}' doesn't exist anymore")


@flow
def ingest_raw_article_metadata_to_gcs():
    api_key = Secret.load("ny-times-api-key").get()
    YEAR = 2019
    MONTH_NUM = 1
    VERSION = 1
    BUCKET_NAME = "raw_article_metadata"

    try:
        data = request_archive_api(
            year=YEAR, month_num=MONTH_NUM, api_key=api_key, version=VERSION
        )
        store_data_as_jsonl(data=data, year=YEAR, month_num=MONTH_NUM)

        temp_directory = pathlib.Path.cwd() / "temp"

        upload_to_blob_storage(
            bucket_name=BUCKET_NAME,
            directory=temp_directory,
            year=YEAR,
            month_num=MONTH_NUM,
        )
    except Exception as e:
        print(f"An exception occured: {e}")
        rmtree()


if __name__ == "__main__":
    ingest_raw_article_metadata_to_gcs()
