""" Create Pydantic Configuration models """

from pydantic import BaseModel


class IngestRawArticleDataParams(BaseModel):
    year = 2019
    month_num = 2
    api_version = 1
    raw_data_bucket_name = "raw_article_data"
    intial_ingestion = True


class IngestInterimArticleDataParam(BaseModel):
    year = 2019
    month_num = 2
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
