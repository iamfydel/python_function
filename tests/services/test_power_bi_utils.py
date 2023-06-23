from contextlib import nullcontext as does_not_raise

import pytest
from requests.exceptions import RequestException

from services.power_bi_utils import PowerBIClient


@pytest.mark.dev
class MockResponse:
    def __init__(self, json_data, status_code, content):
        self.json_data = json_data
        self.status_code = status_code
        self.content = content

    def json(self):
        return self.json_data


test__get_access_token_cases = [
    (200, {"access_token": "token123"}, "content", None, does_not_raise()),
    (401, {}, "content", None, pytest.raises(Exception, match="Error getting access token for PowerBI")),
    (400, {}, "content", RequestException("Invalid URL ''"), pytest.raises(Exception, match="Error with API requests")),
]


@pytest.mark.dev
@pytest.mark.parametrize("test_input_status, test_input_response, test_input_content,"
                         "test_input_exception, test_output_exception",
                         test__get_access_token_cases)
def test__get_access_token(mocker, test_input_status, test_input_response,
                            test_input_content, test_input_exception, test_output_exception):
    response = MockResponse(test_input_response, test_input_status, test_input_content)
    mocker.patch('requests.post', return_value=response, side_effect=test_input_exception)
    powerbi_client = PowerBIClient('tenant_id', 'client_id', 'client_secret')
    with test_output_exception:
        access_token = powerbi_client._get_access_token()
        assert access_token == response.json()['access_token']


test_get_workspace_id_cases = [
    (Exception("Error with API requests"), None, None, None, "content", None, pytest.raises(Exception, match="Error getting workspace ID for PowerBI"), None),
    (None, "token123", 200, None, "content", RequestException("Invalid URL ''"), pytest.raises(Exception, match="Error with API requests"), None),
    (None, "token123", 401, None, "content", None, pytest.raises(Exception, match="Error getting workspace ID for PowerBI"), None),
    (None, "token123", 200, {"value": [{"id": "workspace_id1"}, {"id": "workspace_id2"}]}, "content", None, pytest.raises(Exception, match="Error getting workspace ID for PowerBI"), None),
    (None, "token123", 200, {"value": [{"id": "workspace_id"}]}, "content", None, does_not_raise(), "workspace_id"),
]


@pytest.mark.dev
@pytest.mark.parametrize("get_access_token_exception, get_access_token_result,"
                         "test_input_status, test_input_response, test_input_content, test_input_exception,"
                         "test_output_exception, test_output_expected",
                         test_get_workspace_id_cases)
def test_get_workspace_id(mocker, get_access_token_exception, get_access_token_result,
                          test_input_status, test_input_response, test_input_content, test_input_exception,
                                test_output_exception, test_output_expected):
    mocker.patch('services.power_bi_utils.PowerBIClient._get_access_token',
                 side_effect=get_access_token_exception,
                 return_value=get_access_token_result)
    response = MockResponse(test_input_response, test_input_status, test_input_content)
    mocker.patch('requests.get', return_value=response, side_effect=test_input_exception)
    powerbi_client = PowerBIClient('tenant_id', 'client_id', 'client_secret')
    with test_output_exception:
        result = powerbi_client.get_workspace_id("org", "workspace_name")
        assert result == test_output_expected


test_get_dataset_id_cases = [
    (Exception("Error with API requests"), None, None, None, "content", None, pytest.raises(Exception, match="Error getting Dataset ID for PowerBI"), None),
    (None, "token123", 200, None, "content", RequestException("Invalid URL ''"), pytest.raises(Exception, match="Error with API requests"), None),
    (None, "token123", 401, None, "content", None, pytest.raises(Exception, match="Error getting Dataset ID for PowerBI"), None),
    (None, "token123", 200, {"value": [{"name": "dataset_name1", "id": "dataset_id1"}, {"name": "dataset_name1", "id": "dataset_id2"}]}, "content", None, pytest.raises(Exception, match="Error getting Dataset ID for PowerBI"), None),
    (None, "token123", 200, {"value": [{"name": "dataset_name1", "id": "dataset_id1"}]}, "content", None, does_not_raise(), "dataset_id1"),
]


@pytest.mark.dev
@pytest.mark.parametrize("get_access_token_exception, get_access_token_result,"
                         "test_input_status, test_input_response, test_input_content, test_input_exception,"
                         "test_output_exception, test_output_expected",
                         test_get_dataset_id_cases)
def test_get_dataset_id(mocker, get_access_token_exception, get_access_token_result,
                          test_input_status, test_input_response, test_input_content, test_input_exception,
                          test_output_exception, test_output_expected):
    mocker.patch('services.power_bi_utils.PowerBIClient._get_access_token',
                 side_effect=get_access_token_exception,
                 return_value=get_access_token_result)
    response = MockResponse(test_input_response, test_input_status, test_input_content)
    mocker.patch('requests.get', return_value=response, side_effect=test_input_exception)
    powerbi_client = PowerBIClient('tenant_id', 'client_id', 'client_secret')
    with test_output_exception:
        result = powerbi_client.get_dataset_id("org", "workspace_id", "dataset_name1")
        assert result == test_output_expected


test_refresh_dataset_cases = [
    (Exception("Error with API requests"), None, None, None, "content", None, pytest.raises(Exception, match="Error refreshing Dataset"), None),
    (None, "token123", 200, None, "content", RequestException("Invalid URL ''"), pytest.raises(Exception, match="Error with API requests"), None),
    (None, "token123", 401, None, "content", None, does_not_raise(), False),
    (None, "token123", 202, None, "content", None, does_not_raise(), True),
]


@pytest.mark.dev
@pytest.mark.parametrize("get_access_token_exception, get_access_token_result,"
                         "test_input_status, test_input_response, test_input_content, test_input_exception,"
                         "test_output_exception, test_output_expected",
                         test_refresh_dataset_cases)
def test_refresh_dataset(mocker, get_access_token_exception, get_access_token_result,
                        test_input_status, test_input_response, test_input_content, test_input_exception,
                        test_output_exception, test_output_expected):
    mocker.patch('services.power_bi_utils.PowerBIClient._get_access_token',
                 side_effect=get_access_token_exception,
                 return_value=get_access_token_result)
    response = MockResponse(test_input_response, test_input_status, test_input_content)
    mocker.patch('requests.post', return_value=response, side_effect=test_input_exception)
    powerbi_client = PowerBIClient('tenant_id', 'client_id', 'client_secret')
    with test_output_exception:
        result = powerbi_client.refresh_dataset("org", "workspace_id", "dataset_id")
        assert result == test_output_expected
