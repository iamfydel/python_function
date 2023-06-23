import os
import logging
from datetime import datetime
import azure.functions as func
from azure.identity import ManagedIdentityCredential
from azure.purview.catalog import PurviewCatalogClient
from azure.core.exceptions import ResourceExistsError
import azure.functions as func

from services import utils, purview_utils


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Create Purview metadata to track staging data ingestion lineage.

    Args:
        req (func.HttpRequest): Function inputs

    Raises:
        Exception: Log any exception

    Returns:
        func.HttpResponse: A 200 status on success or
        a 400 status code and an error description if the input is incorrect.
    """
    try:
        req_body = req.get_json()

        context = utils.DataMovement(req_body)

        credential = ManagedIdentityCredential(
            client_id=os.environ['errorlog__clientId'])

        client = PurviewCatalogClient(
            endpoint=f"https://{os.environ['purview_account_name']}"
                     ".purview.azure.com",
            credential=credential)

        collection = f'pview-collection-{context.environment}'
        adf_pl_qname = purview_utils.build_adf_pipeline_qname(
            context.data_factory,
            os.environ['azure_subscription'],
            os.environ['azure_resource_group'],
            context.pipeline_name
        )
        adf_activity_qname = purview_utils.build_adf_activity_qname(
            adf_pl_qname, 'staging_job')

        raw_qname = purview_utils.build_raw_file_qname(
            context.datalake_name, context)
        staging_qname = purview_utils.build_staging_file_qname(
            context.datalake_name, context)

        dataset_entities = {
            "entities": [
                {
                    "typeName": "adf_activity",
                    "attributes": {
                        "outputs": [],
                        "qualifiedName": adf_activity_qname,
                        "inputs": [],
                        "name": "staging_job",
                        "status": "Completed"
                    },
                    "status": "ACTIVE"
                },
                {
                    "typeName": "tabular_schema",
                    "attributes": {
                        "qualifiedName": f"{staging_qname}#tabular_schema",
                        "name": "tabular_schema",
                    },
                    "status": "ACTIVE",
                    "guid": -100
                },
                {
                    "typeName": "azure_datalake_gen2_resource_set",
                    "attributes": {
                        "qualifiedName": staging_qname,
                        "name": context.display_name,
                        "description": "Delta Table",
                        "modifiedTime": int(datetime.utcnow().timestamp()
                                            * 1000)
                    },
                    "status": "ACTIVE",
                    "relationshipAttributes": {
                        "tabular_schema": {
                            "guid": -100
                        }
                    }
                }
            ]
        }

        columns_def = purview_utils.get_purview_columns(context.structure,
                                                        staging_qname, -100)

        for col in columns_def:
            dataset_entities['entities'].append(col)

        col_mapping = [{'Source': col.name, 'Sink': col.name} for col in
                       context.structure if not
                       col.name.startswith('meta_staging')]
        col_mapping = str(col_mapping).replace("'", '"')

        operation_entity = {
            "entity": {
                "typeName": "adf_activity_operation",
                "attributes": {
                    "outputs": [
                        {
                            "typeName": "azure_datalake_gen2_resource_set",
                            "uniqueAttributes": {
                                "qualifiedName": staging_qname
                            }
                        }
                    ],
                    "qualifiedName": f"{adf_activity_qname}#{staging_qname}"
                                     "#azure_datalake_gen2_resource_set",
                    "inputs": [
                        {
                            "typeName": "azure_datalake_gen2_resource_set",
                            "uniqueAttributes": {
                                "qualifiedName": raw_qname
                            }
                        }
                    ],
                    "name": "staging_job",
                    "columnMapping": f'[{{"DatasetMapping":{{"Source":"*",'
                                     f'"Sink":"{staging_qname}"}}'
                                     f',"ColumnMapping":{col_mapping}}}]',
                },
                "status": "ACTIVE"
            }
        }

        operation_rel = {
            "typeName": "process_parent",
            "provenanceType": 0,
            "end1": {
                "typeName": "adf_activity_operation",
                "uniqueAttributes": {
                    "qualifiedName": f"{adf_activity_qname}#{staging_qname}"
                                     "#azure_datalake_gen2_resource_set",
                }
            },
            "end2": {
                "typeName": "adf_activity",
                "uniqueAttributes": {
                    "qualifiedName": adf_activity_qname
                }
            },
            "label": "r:adf_process_parent",
            "status": "ACTIVE",
            "propagatedClassifications": []
        }

        # Create the dataset entities
        client.collection.create_or_update_bulk(collection, dataset_entities)

        # Create the operation entity
        client.collection.create_or_update(collection, operation_entity)

        # Link the staging operation to the staging activity
        # There is not upsert logic for relationship
        try:
            client.relationship.create(operation_rel)
        except ResourceExistsError:
            pass

        return func.HttpResponse(status_code=200)

    except (ValueError, KeyError) as ex:
        error_message = f'Input format error: {repr(ex)}'
        logging.error(str(error_message))
        raise ex
