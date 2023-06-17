import json

import requests
from prefect import flow, get_run_logger, task
from prefect.blocks.system import Secret

from src.etl.load import upload_blob_from_memory


@task(
    retries=0,
    retry_delay_seconds=12,
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

        data = r.json()
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
    retries=0,
    retry_delay_seconds=3,
    name="Upload article metadata as file to GCS",
    description="Upload monthly article metadata data to Google Cloud / Blob Storage",
)
def upload_to_blob_storage(bucket_name: str, data: dict, year: int, month_num: int):
    logger = get_run_logger()

    destination_blob_name = f"articles_{year}_{month_num}.json"

    data_string = json.dumps(data)

    upload_blob_from_memory(
        bucket_name=bucket_name,
        contents=data_string,
        destination_blob_name=destination_blob_name,
    )

    logger.info(
        f"Uploaded contents to Blob '{destination_blob_name}' in bucket '{bucket_name}'"
    )


@flow
def ingest_raw_article_metadata_to_gcs():
    api_key = Secret.load("ny-times-api-key").get()
    YEAR = 2019
    MONTH_NUM = 1
    VERSION = 1
    BUCKET_NAME = "raw_article"

    data = request_archive_api(
        year=YEAR, month_num=MONTH_NUM, api_key=api_key, version=VERSION
    )
    upload_to_blob_storage(
        bucket_name=BUCKET_NAME, data=data, year=YEAR, month_num=MONTH_NUM
    )


if __name__ == "__main__":
    ingest_raw_article_metadata_to_gcs()
