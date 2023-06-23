"""Utils functions for the Cherwell service desk.

"""
import requests
from typing import List
from pathlib import Path

from services import utils


def create_incident(base_url: str, payload: str, auth_token: str) -> str:
    """Create a service desk incident.

    Args:
        base_url (str): The API base URL
        payload (str): The incident JSON payload
        auth_token (str): The authentication token

    Returns:
        string: The ID of the service desk incident created
    """
    headers = {
        "Authorization": "Bearer " + auth_token,
        "Content-Type": "application/json",
    }
    response = requests.post(
        url=f"{base_url}/api/V1/savebusinessobject",
        data=payload,
        headers=headers)

    response.raise_for_status()

    data = response.json()
    return data.get("busObPublicId")


def configure_incident(error_message: str, error_type: str) -> str:
    """Fill the incident template with relevant error details.

    Args:
        error_message (str): The full error message
        error_type (str): The type of error

    Returns:
        str: A service desk incident JSON payload
    """
    template_file = (Path(__file__).parents[1]
                     / 'resources/template_incident.json').resolve()

    with open(
        file=template_file, mode="r", encoding="utf-8"
    ) as file:
        data = file.read()

    return utils.substitute_token(
        data, (("{{description}}", error_message[0:1200]),
               ("{{error_type}}", error_type))
    )


def format_incident_description(
        affected_assets: List[str],
        affected_dependencies: List[str],
        error_messages: List[str],
        run_id: str,
        system: str) -> str:
    """Return an HTML formatted service desk incident description.

    Args:
        affected_assets (List[str]): List of affected assets
        affected_dependencies (List[str]): List of affected dependencies
        error_messages (List[str]): List of all error messages
        run_id [str]: Run ID of the Azure Data Factory Pipeline

    Returns:
        str: An HTML formatted incident description
    """
    return (
        f"<b>{system} ingestion failure</b><br><br>"
        f"<b>Azure Data Factory Run ID:</b> {run_id}<br><br>"
        f"<b>Errors occurred while ingesting:</b><br>"
        f"<br>{'<br>'.join(affected_assets)}<br>"
        "<br><b>The following dependent datasets are affected:</b><br>"
        f"<br>{'<br>'.join(affected_dependencies)}<br>"
        "<br><b>The full error messages are:</b><br>"
        f"<br>{'<br><br>'.join(error_messages)}<br>"
    )
