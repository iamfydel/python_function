"""Unit tests for the cherwell_utils module.

"""
from unittest.mock import Mock, patch, mock_open
from services import cherwell_utils

import pytest

TEST_CONFIGURE_INCIDENT_FILE = """
{
    "busObId": "6dd53665c0c24cab86870a21cf6434ae",
    "busObPublicId": "",
    "busObRecId": "",
    "cacheKey": "",
    "cacheScope": "Tenant",
    "fields": [
        {
            "dirty": true,
            "displayName": "Description",
            "fieldId": "252b836fc72c4149915053ca1131d138",
            "html": null,
            "name": "Description",
            "value": "{{description}}"
        },
        {
            "dirty": true,
            "displayName": "Subcategory",
            "fieldId": "BO:6dd53665c0c24cab86870a21cf6434ae,FI:1163fda7e6a44f40bb94d2b47cc58f46",
            "html": null,
            "name": "Subcategory",
            "value": "{{error_type}}"
        }
    ],
    "persist": true
}
"""

TEST_CONFIGURE_INCIDENT_EXPECTED_RESULT = """
{
    "busObId": "6dd53665c0c24cab86870a21cf6434ae",
    "busObPublicId": "",
    "busObRecId": "",
    "cacheKey": "",
    "cacheScope": "Tenant",
    "fields": [
        {
            "dirty": true,
            "displayName": "Description",
            "fieldId": "252b836fc72c4149915053ca1131d138",
            "html": null,
            "name": "Description",
            "value": "Incident description"
        },
        {
            "dirty": true,
            "displayName": "Subcategory",
            "fieldId": "BO:6dd53665c0c24cab86870a21cf6434ae,FI:1163fda7e6a44f40bb94d2b47cc58f46",
            "html": null,
            "name": "Subcategory",
            "value": "Type of error"
        }
    ],
    "persist": true
}
"""


@patch("builtins.open", new_callable=mock_open,
       read_data=TEST_CONFIGURE_INCIDENT_FILE)
@pytest.mark.dev
def test_configure_incident(mock_file):
    """Test the configure incident function
    """
    assert (cherwell_utils.configure_incident('Incident description',
            'Type of error') ==
            TEST_CONFIGURE_INCIDENT_EXPECTED_RESULT) and mock_file.called


@patch('services.cherwell_utils.requests.post')
@pytest.mark.dev
def test_create_incident(mock_post):
    """Test the create incident function

    Args:
        mock_post (): A mocked API response
    """
    expected_incident_id = '46520'

    mock_post.return_value = Mock(
        status_code=200, json=lambda: {
            'busObPublicId': expected_incident_id})

    incident_id = cherwell_utils.create_incident('', '', '')

    assert incident_id == expected_incident_id


@pytest.mark.dev
def test_format_incident_description():
    """Test the format_incident_description function
    """
    expected_result = (
        "<b>TEST_SYSTEM ingestion failure</b><br><br>"
        "<b>Azure Data Factory Run ID:</b> TEST_RUN_ID<br><br>"
        "<b>Errors occurred while ingesting:</b><br>"
        "<br>Table1<br>Table2<br>"
        "<br><b>The following dependent datasets are affected:</b><br>"
        "<br>Table3<br>Table4<br>Table5<br>"
        "<br><b>The full error messages are:</b><br>"
        "<br>ErrorMessage1<br><br>ErrorMessage2<br>"
    )

    assert cherwell_utils.format_incident_description(
        ['Table1', 'Table2'],
        ['Table3', 'Table4', 'Table5'],
        ['ErrorMessage1', 'ErrorMessage2'],
        'TEST_RUN_ID',
        'TEST_SYSTEM'
    ) == expected_result
