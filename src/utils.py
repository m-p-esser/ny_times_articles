""" Collection of reusuable utility functions """

import datetime
import json
import pathlib

import pandas as pd
import pandas_profiling
from google.cloud import storage


def profile_data(df: pd.DataFrame, file_path) -> pandas_profiling.ProfileReport:
    report = pandas_profiling.ProfileReport(df, title="Profiling Report", minimal=True)
    report.to_file(file_path)

    return report


def convert_to_jsonl(data, file_path):
    with open(file_path, "w") as f:
        for item in data:
            json.dump(item, f)
            f.write("\n")


def rmtree(directory: pathlib.Path):
    """Remove directory and all files in it"""
    if directory.is_dir():
        for child in directory.iterdir():
            if child.is_file():
                child.unlink()
            else:
                rmtree(child)
        directory.rmdir()


def create_range_of_year_months(
    start_date: datetime.date, end_date: datetime.date
) -> list[tuple]:
    dates = pd.date_range(start_date, end_date, freq="M")
    year_months = [(d.year, d.month) for d in dates]
    return year_months
