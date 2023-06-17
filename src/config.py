""" Create Pydantic Configuration models """

from pydantic import BaseModel


class IngestRawArticleDataParams(BaseModel):
    year = 2019
    month_num = 1
    api_version = 1
    raw_data_bucket_name = "raw_article_data"
    intial_ingestion = True


class IngestInterimArticleDataParam(BaseModel):
    year = 2019
    month_num = 1
    raw_data_bucket_name = "raw_article_data"
    interim_data_bucket_name = "interim_article_data"
    interim_data_profile_bucket_name = "interim_article_data_profile"
    is_intial_ingestion = True
    is_manual_ingestion = False
