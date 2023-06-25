import datetime

import pytest

from src.utils import create_range_of_year_months


def test_create_range_of_year_months_one_month():
    year_months = create_range_of_year_months(
        start_date=datetime.date(year=2022, month=1, day=1),
        end_date=datetime.date(year=2022, month=1, day=31),
    )
    assert len(year_months) == 1


def test_create_range_of_year_months_multiple_months():
    year_months = create_range_of_year_months(
        start_date=datetime.date(year=2022, month=1, day=1),
        end_date=datetime.date(year=2022, month=2, day=28),
    )
    assert len(year_months) == 2
