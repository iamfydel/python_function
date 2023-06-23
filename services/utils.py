"""Utils functions for API and I/O.

"""
import requests
import json
from typing import List
from datetime import datetime
from dataclasses import dataclass, fields, field, InitVar
from azure.storage.blob import ContainerClient


@dataclass
class DataEntity:
    """Base class mapping the data entities
    """
    payload: InitVar
    entity_type: str = 'azure_sql_table'
    name: str = 'Unknown asset'
    display_name: str = ''
    schema: str = ''
    system: str = 'Unknown system'
    server_name: str = ''
    version: int = 1
    type: str = ''
    source_dataset: str = ''
    source_name: str = ''
    mapped_name: str = ''

    def __post_init__(self, payload):
        for data_field in fields(self):
            if data_field.name in payload:
                self.__setattr__(data_field.name, payload.get(data_field.name))

        # Backward compatibility - Fix ASAP
        if not self.display_name and 'displayName' in payload:
            self.display_name = payload.get('displayName')


@dataclass
class ErrorContext(DataEntity):
    """Contains the details of an error and the concerned assets
    """
    payload: InitVar
    error_message: str = field(init=False)

    def __post_init__(self, payload):
        super().__post_init__(payload)

        self.error_message = payload.get('error_message', (
                                        'Unknown error. Is there a valid'
                                        'config.json input file?'))


@dataclass
class DataMovement(DataEntity):
    """Contains the details of a data movement
    """
    payload: InitVar
    rows_copied: int = 0
    copy_duration: int = 0
    data_read: int = 0
    data_written: int = 0
    start_date: datetime = datetime(1970, 1, 1)
    run_date: datetime = datetime(1970, 1, 1)
    status: str = ''
    pipeline_name: str = ''
    data_factory: str = ''
    environment: str = ''
    purview_prefix: str = ''
    datalake_name: str = 'unknown'
    structure: List[DataEntity] = field(default_factory=list)

    def __post_init__(self, payload):
        super().__post_init__(payload)

        # ADF outputs schemas as 'structure'
        structure = []
        for col in payload.get('structure', {}):
            structure.append(DataEntity(col))
        self.structure = structure

        self.status = payload.get('executionDetails', [{}])[0].get('status')

        start_date_str = payload.get('executionDetails', [{}])[0].get('start')
        if start_date_str:
            self.start_date = datetime.strptime(start_date_str[:-2],
                                                '%Y-%m-%dT%H:%M:%S.%f')

        run_date_str = payload.get('run_date')
        if run_date_str:
            self.run_date = datetime.strptime(run_date_str,
                                              '%Y-%m-%d %H:%M:%S')

        self.rows_copied = payload.get('rowsCopied', 0)
        self.data_written = payload.get('dataWritten', 0)
        self.purview_prefix = self.entity_type.replace('_table', '')


@dataclass
class ColMap():
    """A Column Mapping for data marts
    """
    name: str
    source_name: str
    source_dataset: str
    mapped_name_col: str = ''

    @property
    def mapped_name(self) -> str:
        return (self.mapped_name_col if self.mapped_name_col else
                self.source_name)


def get_auth_token(url: str, body: str, token_name: str) -> str:
    """Obtains an API authentication token.

    Args:
        url (str): The full URL of the authentication endpoint
        body (str): The raw body to post
        token_name (str): The name of the response body property
                            containing the authentication token

    Returns:
        str: The authentication token
    """
    response = requests.post(url=url, data=body)

    response.raise_for_status()

    data = response.json()
    return data.get(token_name)


def substitute_token(data: str, tokens: tuple) -> str:
    """[summary]

    Args:
        data (str): The text to apply tokenn substitution to
        tokens (tuple): The tokens ('old_str', 'new_str')

    Returns:
        str: A string wih tokens replaced
    """
    return_value = data

    for old_value, new_value in tokens:
        return_value = return_value.replace(old_value, new_value)
    return return_value


def get_error_type(error_message: str) -> str:
    """Determine an error type for the service desk incident
        as agreed in User Story #276
        https://dev.azure.com/anchor-it/anchor-platform/_workitems/edit/276

    Args:
        error_message (str): The incoming error message

    Returns:
        str: A standard error type for service desk incidents
    """
    if "Failure happened on 'Source' side" in error_message:
        return 'Data Source collection'
    if "ErrorCode=SqlFailedToConnect" in error_message:
        return 'Data Source connectivity'
    if "Data quality error" in error_message:
        return 'Data Quality'
    return 'Data Pipeline failure'


def load_blobs_json(blobs: iter, container: ContainerClient) -> List[object]:
    """Load a list a Blobs into a JSON list

    Args:
        blobs (iter): A list of Blobs
        container (ContainerClient): An Azure Storage Container Client

    Returns:
        List[object]: A list of JSON objects contained in the Blobs
    """
    blob_content = []

    for blob in blobs:
        data = container.download_blob(blob)
        item = json.loads(data.readall())
        blob_content.append(item)

    return blob_content


def delete_blobs(blobs: iter, container: ContainerClient):
    """Delete a list of Blobs

    Args:
        blobs (iter): A list of Blobs
        container (ContainerClient): An Azure Storage Container Client
    """
    for blob in blobs:
        container.delete_blob(blob, delete_snapshots="include")
