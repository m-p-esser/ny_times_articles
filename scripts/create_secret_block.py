"""Programmatically create a Secret Block for Prefect"""

from dotenv import dotenv_values
from prefect.blocks.system import Secret

env_variables = dotenv_values(".env")

# New York Times API KEY
block = Secret(value=env_variables["NY_TIMES_API_KEY"])
block.save(name="ny-times-api-key", overwrite=True)
