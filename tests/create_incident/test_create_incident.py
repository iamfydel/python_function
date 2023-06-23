"""Unit tests for the create_incident Azure Function.

"""
import os
from unittest.mock import patch, MagicMock
import pytest
import azure.functions as func
from typing import Mapping

from create_incident import main

TEST_CREATE_INCIDENT_INPUT = [
    {
        "error_message": "ErrorCode=SqlFailedToConnect",
        "entity_type": "azure_sql_table",
        "system": "Template",
        "server_name": "https://serv.com/test",
        "version": 1,
        "displayName": "Customer",
        "name": "Customer",
        "schema": "SalesLT",
        "type": "full",
        "granularity": "day"
    },
    {
        "error_message": "ErrorCode=SqlFailedToConnect",
        "entity_type": "azure_sql_table",
        "system": "Template",
        "server_name": "https://serv.com/test",
        "version": 1,
        "displayName": "Address",
        "name": "Address",
        "schema": "SalesLT",
        "type": "full",
        "granularity": "day"
    }
]


TEST_CREATE_INCIDENT_PARAMS_INPUTS = [
    ({'wrong_param': 'value'}, 400),
    ({}, 400)
]

@pytest.mark.dev
@pytest.mark.parametrize('test_input, expected_output',
                         TEST_CREATE_INCIDENT_PARAMS_INPUTS)
@patch('azure.functions.Out', MagicMock())
def test_create_incident_invalid_input(test_input: Mapping[str, str],
                                       expected_output: int):
    """Test the create_incident function behaviour
        when an invalid request is passed
    """
    test_req = func.HttpRequest(
        method='POST',
        body='',
        url='/api/create_incident',
        params=test_input)

    test_resp = main(test_req)

    assert test_resp.status_code == expected_output


CREATE_INCIDENT_TEST_ENV_VAR = [
    ("purview_account_name", "https://"),
    ("service_desk_base_url", "https://"),
    ("service_desk_auth_endpoint", "/token"),
    ("service_desk_client_id", "1234"),
    ("service_desk_username", "User"),
    ("service_desk_password", "Password"),
    ("errorlog__clientId", "4440"),
    ("errorlog__serviceUri", "https://test.com"),
    ("errorlog__credential", "managedidentity")
]


@pytest.mark.dev
@patch.dict(os.environ, CREATE_INCIDENT_TEST_ENV_VAR, clear=True)
@patch('services.utils.load_blobs_json')
@patch('services.cherwell_utils.create_incident')
@patch('services.utils.get_auth_token')
@patch('services.purview_utils.get_dependencies_list')
@patch('create_incident.BlobServiceClient', MagicMock())
@patch('services.utils.ContainerClient', MagicMock())
def test_create_incident(mock_dp_list, mock_auth_token, mock_incident,
                         mock_input):
    """Test the create_incident function behaviour
    """
    expected_status = 200
    expected_body = b'59600'

    mock_dp_list.return_value = {
        'TestTable2 (test_table)',
        'TestTable3 (test_other_table)'}
    mock_auth_token.return_value = 'AUTH'
    mock_incident.return_value = '59600'
    mock_input.return_value = TEST_CREATE_INCIDENT_INPUT

    test_req = func.HttpRequest(
        method='POST',
        body='',
        url='/api/create_incident',
        params={'pipeline_run_id': 'test_run_id'})

    test_resp = main(test_req)

    assert (test_resp.status_code == expected_status
            and test_resp.get_body() == expected_body)
