"""Azure Function to maintain Synapse and Power BI Purview metadata.

"""
import os
import logging
from azure.identity import ManagedIdentityCredential
from azure.purview.catalog import PurviewCatalogClient
import azure.functions as func

from services import utils, purview_utils


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Create Purview metadata to track Synapse and Power BI
       data ingestion lineage.

    Args:
        req (func.HttpRequest): Function inputs
        dataset_id (str): The ID of the Power BI dataset
        view_name (str): The name of the Synapse source view for
            the Power BI dashboard
        datamart_name (str): The name of the source curated datamart file

    Raises:
        Exception: Log any exception

    Returns:
        func.HttpResponse: A 200 status on success or
        a 400 status code and an error description if the input is incorrect.
    """
    try:
        dataset_id = req.params.get('dataset_id')
        view_name = req.params.get('view_name')
        datamart_name = req.params.get('datamart_name')

        if not dataset_id:
            raise ValueError("Missing parameter 'dataset_id'")
        if not view_name:
            raise ValueError("Missing parameter 'view_name'")
        if not datamart_name:
            raise ValueError("Missing parameter 'datamart_name'")

        credential = ManagedIdentityCredential(
            client_id=os.environ['errorlog__clientId'])
        client = PurviewCatalogClient(
            endpoint=f"https://{os.environ['purview_account_name']}"
                     ".purview.azure.com",
            credential=credential)

        datalake_name = os.environ['datalake_name']
        collection = f"pview-collection-{os.environ['environment']}"
        curated_qname = purview_utils.build_curated_file_qname(
            datalake_name,
            datamart_name)

        curated_response = client.entity.get_by_unique_attributes(
            type_name='tabular_schema',
            attr_qualified_name=f'{curated_qname}#tabular_schema',
            min_ext_info=False, ignore_relationships=False)

        ref = curated_response['referredEntities']
        source_columns = [ref[col]['attributes']['name'] for col in ref
                         if ref[col]['typeName'] == 'column']

        query = purview_utils.purview_search_query(
            view_name,
            'pview-scan',
            'azure_synapse_serverless_sql_view')

        response = client.discovery.query(query)

        if '@search.count' not in response or response['@search.count'] == 0:
            logging.warning('The Synapse view could not be found in Purview')
            return 'The Synapse view could not be found in Purview'

        synapse_view_qname = response['value'][0]['qualifiedName']

        synapse_view_response = client.entity.get_by_unique_attributes(
            type_name='azure_synapse_serverless_sql_view',
            attr_qualified_name=synapse_view_qname,
            min_ext_info=False, ignore_relationships=False)

        ref = synapse_view_response['referredEntities']

        dest_columns = [ref[col]['attributes']['name'] for col in ref
                        if ref[col]['typeName'] == 'azure_synapse_serverless_sql_view_column']

        columns = list(set(dest_columns).intersection(source_columns))

        entities = [utils.DataEntity({'name': col, 'source_name': col,
                                      'source_dataset': datamart_name,
                                      'system': 'curated'}) for col in columns]

        col_mapping = purview_utils.get_purview_column_mapping(
            entities, datalake_name, synapse_view_qname)

        query = purview_utils.purview_search_query(
            dataset_id,
            'pview-scan',
            'powerbi_dataset')

        response = client.discovery.query(query)

        if '@search.count' not in response or response['@search.count'] == 0:
            logging.warning(
                'The PowerBI dataset could not be found in Purview')
            return 'The PowerBI dataset could not be found in Purview'

        dataset_qname = response['value'][0]['qualifiedName']

        operation_entities = {
            "entities":
            [
                {
                    "typeName": "azure_synapse_operation",
                    "attributes": {
                        "outputs": [
                            {
                                "typeName": "azure_synapse_serverless_sql_view",
                                "uniqueAttributes": {
                                    "qualifiedName": synapse_view_qname
                                }
                            },
                        ],
                        "qualifiedName": f"{synapse_view_qname}#{curated_qname}"
                                        "#azure_datalake_gen2_resource_set",
                        "inputs": [
                            {
                                "typeName": "azure_datalake_gen2_resource_set",
                                "uniqueAttributes": {
                                    "qualifiedName": curated_qname
                                }
                            },
                        ],
                        "name": "synapse_serverless",
                        "columnMapping": col_mapping
                    },
                    "status": "ACTIVE"
                },
                {
                    "typeName": "powerbi_dataset_process",
                    "attributes": {
                        "outputs": [
                            {
                                "typeName": "powerbi_dataset",
                                "uniqueAttributes": {
                                    "qualifiedName": dataset_qname
                                }
                            },
                        ],
                        "qualifiedName": f"{synapse_view_qname}#{dataset_qname}"
                                         "#powerbi_dataset",
                        "inputs": [
                            {
                                "typeName": "azure_synapse_serverless_sql_view",
                                "uniqueAttributes": {
                                    "qualifiedName": synapse_view_qname
                                }
                            },
                        ],
                        "name": "powerbi_report"
                    },
                    "status": "ACTIVE"
                }
            ]
        }

        client.collection.create_or_update_bulk(collection, operation_entities)

        return 'OK'
    except Exception as ex:
        logging.exception(ex)

        if isinstance(ex, ValueError) and 'Missing parameter' in str(ex):
            return func.HttpResponse(status_code=400, body=str(ex))
        else:
            return func.HttpResponse(status_code=500)
