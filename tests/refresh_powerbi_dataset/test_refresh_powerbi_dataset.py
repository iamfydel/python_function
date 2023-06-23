import os
import json
from unittest.mock import patch, MagicMock
import pytest
import azure.functions as func

from refresh_powerbi_dataset import main


TEST_CREATE_INCIDENT_PARAMS_INPUTS = [
    ({"dataset_name": "my_dataset"}, Exception("Error getting workspace ID for PowerBI"), None, "dataset_id", None, None, True, 500),
    ({"dataset_name": "my_dataset"}, None, "workspace_id", Exception("Error getting Dataset ID for PowerBI"), None, None, True, 500),
    ({'wrong_param': 'value'}, None, None, None, None, None, None, 500),
    ({}, None, None, None, None, None, True, 500),
    ({"dataset_name": "my_dataset"}, None, "workspace_id", None, "dataset_id", None, False, 403),
    ({'dataset_name': 'my_dataset'}, None, "workspace_id", None, "dataset_id", None, True, 200),
]

@pytest.mark.dev
@pytest.mark.parametrize('test_input,'
                         'get_workspace_id_exception, get_workspace_id_result,'
                         'get_dataset_id_exception, get_dataset_id_result,'
                         'refresh_dataset_exception, refresh_dataset_result,'
                         'expected_output',
                         TEST_CREATE_INCIDENT_PARAMS_INPUTS)
@patch('azure.functions.Out', MagicMock())
def test_refresh_powerbi_dataset_invalid_input(mocker, test_input,
                                               get_workspace_id_exception, get_workspace_id_result,
                                               get_dataset_id_exception, get_dataset_id_result,
                                               refresh_dataset_exception, refresh_dataset_result,
                                               expected_output):
    mocker.patch('services.power_bi_utils.PowerBIClient.get_workspace_id',
                 side_effect=get_workspace_id_exception,
                 return_value=get_workspace_id_result)
    mocker.patch('services.power_bi_utils.PowerBIClient.get_dataset_id',
                 side_effect=get_dataset_id_exception,
                 return_value=get_dataset_id_result)
    mocker.patch('services.power_bi_utils.PowerBIClient.refresh_dataset',
                 side_effect=refresh_dataset_exception,
                 return_value=refresh_dataset_result)
    os.environ['powerbi_organisation'] = "myorg"
    os.environ['environment'] = "d01"
    os.environ['powerbi_tenant_id'] = "tenant_id"
    os.environ['powerbi_client_id'] = "client_id"
    os.environ['powerbi_client_secret'] = "client_secret"
    test_req = func.HttpRequest(
        method='POST',
        body=json.dumps(test_input).encode('utf8'),
        url='/api/refresh_powerbi_dataset',
        params='')

    test_resp = main(test_req)

    assert test_resp.status_code == expected_output
