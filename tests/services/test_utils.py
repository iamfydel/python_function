"""Unit tests for the utils module.

"""
import pytest
import os
import json
from unittest.mock import Mock, patch
from services import utils
from pathlib import Path
from azure.storage.blob import ContainerClient


@pytest.mark.dev
@patch('services.utils.requests.post')
def test_get_auth_token(mock_post):
    """Test the API authentication function

    Args:
        mock_post (): A mocked API response
    """
    token_name = 'access_token'
    expected_auth_token = 'yJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1bmlxdWVfbm'

    mock_post.return_value = Mock(
        status_code=200, json=lambda: {
            token_name: expected_auth_token})
    auth_token = utils.get_auth_token(None, None, token_name)

    assert auth_token == expected_auth_token


@pytest.mark.dev
def test_substitute_token():
    """Test the token substitution function
    """
    test_input = '{"item1":"{{token1}}","item2":"{{token2}}"}'
    expected_output = '{"item1":"value1","item2":"value2"}'

    tokens = (('{{token1}}', 'value1'), ('{{token2}}', 'value2'))

    assert utils.substitute_token(test_input, tokens) == expected_output


TEST_ERROR_TYPES = [
    ("Failure happened on 'Source' side.", "Data Source collection"),
    ("ErrorCode=SqlFailedToConnect,'Type", "Data Source connectivity"),
    ("Data quality error. blah", "Data Quality"),
    ("'Any other error", "Data Pipeline failure"),
]


@pytest.mark.dev
@pytest.mark.parametrize('test_input, expected_output', TEST_ERROR_TYPES)
def test_get_error_type(test_input: str, expected_output: str):
    """Test the get error type function

    Args:
        test_input (str): A data driven input from TEST_ERROR_TYPES
        expected_output (str): An data driven expected output
        from TEST_ERROR_TYPES
    """
    assert utils.get_error_type(test_input) == expected_output


TEST_BLOB_FILES = ['blob_test/1.json', 'blob_test/2.json']


TEST_BLOB_CONTENT = [
    {'item': 'first', 'name': 'al'},
    {'item': 'second', 'name': 'mk'}
]


@pytest.mark.dev
@pytest.fixture(scope='session')
def prepare_blob_files():
    """Create test blob files
    """
    path = Path(__file__).parents[1] / 'temp/blob_test/'

    _ = path.mkdir(parents=True, exist_ok=True)

    for index, file in enumerate(TEST_BLOB_CONTENT, start=1):
        with open(f'{path}/{index}.json', 'w+') as outfile:
            json.dump(file, outfile)


class ReadBlob():
    """A mock object to test Azure Blobs
    """
    name: str

    def __init__(self, *args, **kwargs):
        self.name = args[0]

    def readall(self) -> str:
        """A mocked function to return the content of a file

        Returns:
            str: The string content of a file
        """
        path = (Path(__file__).parents[1] / 'temp' / self.name).resolve()
        with open(path, 'r') as outfile:
            data = outfile.read()
        return data


def delete_blob_mock(*args, **kwargs):
    """A mocked function to delete a file
    """
    path = (Path(__file__).parents[1] / 'temp' / args[0]).resolve()
    os.remove(path)

@pytest.mark.serial
@pytest.mark.dev
@patch('services.utils.ContainerClient.download_blob')
def test_load_blobs_json(mock_container: Mock, prepare_blob_files):
    """Assert the read_blobs function
    """
    mock_container.side_effect = ReadBlob

    container = ContainerClient('https://testH9sMs03hkMopLs7345.com', 'TEST')

    assert (utils.load_blobs_json(TEST_BLOB_FILES, container)
            == TEST_BLOB_CONTENT)

@pytest.mark.dev
@patch('services.utils.ContainerClient.delete_blob')
def test_delete_blobs(mock_delete: Mock, prepare_blob_files):
    """Assert the read_blobs function
    """
    mock_delete.side_effect = delete_blob_mock

    container = ContainerClient('https://testH9sMs03hkMopLs7345.com', 'TEST')
    utils.delete_blobs(TEST_BLOB_FILES, container)

    arr = os.listdir((Path(__file__).parents[1] / 'temp/blob_test/').resolve())

    assert not arr
