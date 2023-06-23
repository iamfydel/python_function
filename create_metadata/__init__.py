"""Azure Function to maintain Purview metadata.

"""
import os
import logging
from datetime import datetime
import azure.functions as func
from azure.identity import ManagedIdentityCredential
from azure.purview.catalog import PurviewCatalogClient
from azure.purview.administration.account import PurviewAccountClient
from azure.core.exceptions import ResourceExistsError

from services import utils, purview_utils


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Create Purview metadata to track data ingestion lineage.

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

        account_client = PurviewAccountClient(
            endpoint=f"https://{os.environ['purview_account_name']}"
                     ".purview.azure.com",
            credential=credential)

        collection = f'pview-collection-{context.environment}'
        collection_entity = {
            "name": collection
        }

        # Attempt to upsert the collection.
        # In case of a Purview concurrency exception, ignore the failure and
        # let the other instance perform the upsert.
        try:
            account_client.collections.create_or_update_collection(
                collection, collection_entity)
        except ResourceExistsError as ex:
            warning_message = f'Purview collection concurrency issue: {repr(ex)}'
            logging.warning(str(warning_message))
            pass

        adf_qname = purview_utils.build_adf_qname(
            context.data_factory,
            os.environ['azure_subscription'],
            os.environ['azure_resource_group']
        )
        adf_copy_qname = (f'{adf_qname}/pipelines/{context.pipeline_name}/'
                          'activities/copy_datalake_raw')

        source_prefix = purview_utils.get_server_prefix(context.entity_type)

        source_host = (f'{source_prefix}://{context.system}_'
                       f'{context.environment}')

        adf_entity = {
            "entity":
            {
                "typeName": "azure_data_factory",
                "attributes": {
                    "resourceGroupName": os.environ['azure_resource_group'],
                    "qualifiedName": adf_qname,
                    "name": context.data_factory,
                    "subscriptionId": os.environ['azure_subscription']
                },
                "status": "ACTIVE"
            }
        }

        adf_copy_template = {
            "typeName": "adf_copy_activity",
            "attributes": {
                "outputs": [],
                "qualifiedName": adf_copy_qname,
                "inputs": [],
                "name": "copy_datalake_raw",
                "status": "Completed"
            },
            "status": "ACTIVE"
        }
        adf_copy_template['guid'] = -50

        adf_pipeline_assets = {
            "entities": [
                {
                    "typeName": f"{context.purview_prefix}_server",
                    "attributes": {
                        "qualifiedName": source_host,
                        "name": context.system,
                        "description": f"Source server for the "
                                       f"{context.system} system"
                    },
                    "status": "ACTIVE"
                },
                {
                    "typeName": "adf_pipeline",
                    "attributes": {
                        "qualifiedName": (f"{adf_qname}/pipelines/"
                                          f"{context.pipeline_name}"),
                        "name": context.pipeline_name
                    },
                    "status": "ACTIVE"
                },
                adf_copy_template
            ]
        }

        # Create the ADF instance
        client.collection.create_or_update(collection, adf_entity)

        # Create ADF structure
        response = client.collection.create_or_update_bulk(collection,
                                                           adf_pipeline_assets)
        adf_copy_guid = response['guidAssignments']['-50']

        # Update the row count and the last run date
        response = client.entity.get_by_guid(adf_copy_guid)

        last_run_ts = response['entity']['attributes']['lastRunTime']
        last_run_date = datetime.fromtimestamp(last_run_ts / 1000)
        row_count = context.rows_copied
        data_size = context.data_written

        if last_run_date.date() == context.start_date.date():
            row_count += response['entity']['attributes']['rowCount']
            data_size += response['entity']['attributes']['dataSize']

        adf_copy_template['guid'] = adf_copy_guid
        adf_copy_template['attributes']['rowCount'] = row_count
        adf_copy_template['attributes']['dataSize'] = data_size
        adf_copy_template['attributes']['lastRunTime'] = \
            context.start_date.timestamp() * 1000
        updated_adf_copy = {
            "entity": adf_copy_template
        }

        client.collection.create_or_update(collection, updated_adf_copy)

        raw_qname = (f"https://{os.environ['datalake_name']}.dfs.core.windows"
                     f".net/raw/{context.system}/{context.display_name}/v"
                     f"{context.version}/{{Year}}/{{Month}}/{{Day}}/"
                     f"{context.display_name}")

        if context.entity_type == 'azure_sql_table':
            source_host += f'/{context.system}DB'

        dataset_entities = {
            "entities": [
                {
                    "typeName": f"{context.purview_prefix}_schema",
                    "attributes": {
                        "qualifiedName": f"{source_host}/{context.schema}",
                        "name": context.schema,
                    },
                    "status": "ACTIVE"
                },
                {
                    "typeName": "tabular_schema",
                    "attributes": {
                        "qualifiedName": f"{raw_qname}#tabular_schema",
                        "name": "tabular_schema",
                    },
                    "status": "ACTIVE",
                    "guid": -100
                },
                {
                    "typeName": context.entity_type,
                    "attributes": {
                        "qualifiedName": f"{source_host}/"
                                         f"{context.schema}/{context.name}",
                        "name": context.name,
                        "source": context.system
                    },
                    "status": "ACTIVE"
                },
                {
                    "typeName": "azure_datalake_gen2_resource_set",
                    "attributes": {
                        "qualifiedName": raw_qname,
                        "name": context.display_name,
                        "description": "Parquet Data File",
                        "modifiedTime": context.start_date.timestamp() * 1000,
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

        # Create columns
        for col in context.structure:
            col_raw = {
                "typeName": "column",
                "attributes": {
                    "qualifiedName": f"{raw_qname}#tabular_schema//{col.name}",
                    "name": col.name,
                    "type": col.type
                },
                "relationshipAttributes": {
                    "composeSchema": {
                        "guid": -100
                    }
                }
            }
            dataset_entities['entities'].append(col_raw)

        col_mapping = [{'Source': col.name, 'Sink': col.name} for col in
                       context.structure if not col.name.startswith('meta_')]
        col_mapping = str(col_mapping).replace("'", '"')

        operation_entity = {
            "entity": {
                "typeName": "adf_copy_operation",
                "attributes": {
                    "outputs": [
                        {
                            "typeName": "azure_datalake_gen2_resource_set",
                            "uniqueAttributes": {
                                "qualifiedName": raw_qname
                            }
                        }
                    ],
                    "qualifiedName": f"{adf_copy_qname}#{raw_qname}"
                                     "#azure_datalake_gen2_resource_set",
                    "inputs": [
                        {
                            "typeName": context.entity_type,
                            "uniqueAttributes": {
                                "qualifiedName": f"{source_host}/"
                                                 f"{context.schema}"
                                                 f"/{context.name}"
                            }
                        }
                    ],
                    "name": "copy_datalake_raw",
                    "columnMapping": f'[{{"DatasetMapping":{{"Source":"*",'
                                     f'"Sink":"{raw_qname}"}},"ColumnMapping"'
                                     f':{col_mapping}}}]',
                },
                "status": "ACTIVE"
            }
        }

        operation_rel = {
            "typeName": "process_parent",
            "provenanceType": 0,
            "end1": {
                "typeName": "adf_copy_operation",
                "uniqueAttributes": {
                    "qualifiedName": f"{adf_copy_qname}#{raw_qname}"
                                     "#azure_datalake_gen2_resource_set",
                }
            },
            "end2": {
                "typeName": "adf_copy_activity",
                "uniqueAttributes": {
                    "qualifiedName": adf_copy_qname
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

        # Link the copy operation to the copy activity
        # There is not upsert logic for relationship
        try:
            client.relationship.create(operation_rel)
        except ResourceExistsError:
            pass

        return func.HttpResponse(status_code=200)

    except (ValueError, KeyError) as ex:
        error_message = f'Input format error: {repr(ex)}'
        logging.error(str(error_message))
        return func.HttpResponse(
            str(error_message),
            status_code=400
        )
