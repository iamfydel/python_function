"""Azure Function to create service desk incidents.

"""
import os
import logging
import azure.functions as func

from azure.storage.blob import BlobServiceClient
from azure.purview.catalog import PurviewCatalogClient
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential

from services import utils, cherwell_utils, purview_utils


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Create a service desk incident for the Azure Data Factory Pipeline
        passed as a param 'pipeline_run_id'.
        The function will collect all the error files for this pipeline
        then create an incident.

    Args:
        req (func.HttpRequest): Function inputs

    Raises:
        Exception: Log any exception

    Returns:
        func.HttpResponse: A 200 status and the service desk incident id
            created, a 400 status code and an error description if the input
            is in incorrect format or a 500 status code and an error
            description for any other error.
    """
    try:
        pipeline_run_id = req.params.get('pipeline_run_id')

        if not pipeline_run_id:
            raise ValueError(("The Azure Data Factory Pipeline Run ID must be "
                             "passed as pipeline_run_id"))

        managed_credential = ManagedIdentityCredential(
            client_id=os.environ['errorlog__clientId'])
        blob_service_client = BlobServiceClient(
            os.environ['errorlog__serviceUri'],
            credential=managed_credential)

        container_client = blob_service_client.get_container_client(
            'error-files')
        blob_list = list(container_client.list_blobs(
            name_starts_with=f'{pipeline_run_id}/'))

        files = utils.load_blobs_json(blob_list, container_client)

        if not files:
            raise ValueError("No error files to process")

        error_context = [utils.ErrorContext(item) for item in files]

        purview_endpoint = (f"https://{os.environ['purview_account_name']}"
                            "purview.azure.com")

        credential = DefaultAzureCredential()
        client = PurviewCatalogClient(
            endpoint=purview_endpoint,
            credential=credential)

        error_type = utils.get_error_type(error_context[0].error_message)
        affected_assets = [asset.name for asset in error_context]
        affected_dependencies = purview_utils.get_dependencies_list(
            client, error_context)
        error_message = cherwell_utils.format_incident_description(
            affected_assets,
            affected_dependencies,
            [error.error_message for error in error_context],
            pipeline_run_id,
            error_context[0].system
        )

        auth_url = os.environ['service_desk_base_url'] + \
            os.environ['service_desk_auth_endpoint']
        body = (
            "grant_type=password&"
            f"client_id={os.environ['service_desk_client_id']}&"
            f"username={os.environ['service_desk_username']}&"
            f"password={os.environ['service_desk_password']}")

        auth_token = utils.get_auth_token(auth_url, body, 'access_token')
        payload = cherwell_utils.configure_incident(error_message, error_type)

        incident_id = cherwell_utils.create_incident(
            os.environ['service_desk_base_url'], payload, auth_token)

        logging.info('Created service desk incident #%s', incident_id)

        utils.delete_blobs(blob_list, container_client)

        return func.HttpResponse(
            incident_id,
            status_code=200
        )
    except (Exception) as ex:
        if isinstance(
            ex,
            (ValueError,
             AttributeError)):
            error_message = f'Input format error: {repr(ex)}'
            logging.error(str(error_message))
            return func.HttpResponse(
                str(error_message),
                status_code=400
            )
        else:
            raise ex
