""" Create Pydantic Configuration models """

import datetime

from pydantic import BaseModel


class IngestRawArticleDataParams(BaseModel):
    start_date = datetime.date(2000, 1, 1)
    end_date = datetime.date(2023, 6, 30)
    api_version = 1
    raw_data_bucket_name = "raw_article_data"
    intial_ingestion = True


class IngestInterimArticleDataParam(BaseModel):
    start_date = datetime.date(2000, 1, 1)
    end_date = datetime.date(2023, 6, 30)
    raw_data_bucket_name = "raw_article_data"
    interim_data_bucket_name = "interim_article_data"
    interim_data_profile_bucket_name = "interim_article_data_profile"
    is_intial_ingestion = True
    is_manual_ingestion = False


class SyncArticleDataToBigquery(BaseModel):
    dataset_id = "ny_times"
    # location = "eu"  # location where data is stored
    table_id = "interim_article"
    source_uri = "gs://interim_article_data/interim_article_data_*.parquet"
