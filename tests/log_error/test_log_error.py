"""Unit tests for the log_error Azure Function.

"""
from unittest.mock import patch, MagicMock
import pytest
import azure.functions as func
from typing import Mapping

from log_error import main


TEST_LOG_ERROR_INPUT = r'''
{
    "error_message": "ErrorCode=SqlFailedToConnect",
    "entity_type": "azure_sql_table",
    "system": "Test",
    "server_name": "https://serv.com/test",
    "version": 1,
    "displayName": "Customer",
    "name": "Customer",
    "schema": "SalesLT",
    "type": "full",
    "granularity": "day"
}
'''

@pytest.mark.dev
@patch('azure.functions.Out.set')
def test_log_error(mock_out):
    """Test the log error function output
    """
    expected_status = 200
    test_req = func.HttpRequest(
        method='POST',
        body=TEST_LOG_ERROR_INPUT,
        url='/api/log_error',
        params={'pipeline_run_id': 'test_run_id'})

    test_resp = main(test_req, func.Out[bytes])

    output = mock_out.call_args[0][0]

    assert (test_resp.status_code == expected_status and
            output == TEST_LOG_ERROR_INPUT)


TEST_LOG_ERROR_PARAMS_INPUTS = [
    ({'wrong_param': 'value'}, 400),
    ({}, 400),
    ({'pipeline_run_id': 'test_run_id'}, 200)
]


@pytest.mark.dev
@pytest.mark.parametrize('test_input, expected_output',
                         TEST_LOG_ERROR_PARAMS_INPUTS)
@patch('azure.functions.Out', MagicMock())
def test_log_error_invalid_input(test_input: Mapping[str, str],
                                 expected_output: int):
    """Test the log error function behaviour
        when an invalid request is passed
    """
    test_req = func.HttpRequest(
        method='POST',
        body='',
        url='/api/log_error',
        params=test_input)

    test_resp = main(test_req, func.Out[bytes])

    assert test_resp.status_code == expected_output
