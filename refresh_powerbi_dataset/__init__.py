"""
Azure Function to refresh PowerBI Dataset.
"""
import json
import os
import logging
import azure.functions as func

from services.power_bi_utils import PowerBIClient


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Refreshes a powerbi dataset
    :param req: The request received by the endpoint
    :return: The status code of the endpoint
    """
    try:
        logging.info("start function")
        req_body = req.get_json()

        powerbi_organisation = os.environ['powerbi_organisation']
        environment = os.environ['environment']
        tenant_id = os.environ['powerbi_tenant_id']
        client_id = os.environ['powerbi_client_id']
        client_secret = os.environ['powerbi_client_secret']

        if environment.lower() == 'prod':
            powerbi_workspace_name = "Data Platform"
        else:
            powerbi_workspace_name = f"Data Platform {environment.upper()}"
        logging.info(f"powerbi_organisation: {powerbi_organisation}, environment: {environment}, powerbi_workspace_name: {powerbi_workspace_name}")

        logging.info("instantiate client")
        powerbi_client = PowerBIClient(tenant_id, client_id, client_secret)

        logging.info("refresh dataset")
        workspace_id = powerbi_client.get_workspace_id(powerbi_organisation, powerbi_workspace_name)
        dataset_id = powerbi_client.get_dataset_id(powerbi_organisation, workspace_id, req_body['dataset_name'])
        refresh_status = powerbi_client.refresh_dataset(powerbi_organisation, workspace_id, dataset_id)

        if refresh_status:
            return func.HttpResponse(status_code=200, body=json.dumps({"dataset_id": dataset_id}), mimetype="application/json")
        else:
            return func.HttpResponse(status_code=403)
    except Exception as e:
        logging.error("Error refreshing the PowerBI dataset", stack_info=e)
        return func.HttpResponse(status_code=500)
