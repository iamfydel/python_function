"""Azure Function to apply scanned Purview classifications.

"""
import os
import azure.functions as func
from azure.identity import ManagedIdentityCredential
from azure.purview.catalog import PurviewCatalogClient
from azure.core.exceptions import HttpResponseError
import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Apply the Purview classifications.

    Args:
        req (func.HttpRequest): Function inputs

    Raises:
        Exception: Log any exception

    Returns:
        func.HttpResponse: A 200 status on success or a 500 status on failure
    """
    credential = ManagedIdentityCredential(
        client_id=os.environ['errorlog__clientId'])

    client = PurviewCatalogClient(
        endpoint=f"https://{os.environ['purview_account_name']}"
                 ".purview.azure.com",
        credential=credential)

    query = {
        "keywords": None,
        "limit": 1000,
        "filter": {
            "and": [
                {
                    "collectionId": "pview-scan"
                },
                {
                    "entityType": "azure_datalake_gen2_resource_set"
                }
            ]
        },
        "facets": [
            {
                "facet": "classification"
            }
        ]
    }

    response = client.discovery.query(query)

    classifications = [{"classification": item['value']} for item
                       in response['@search.facets']['classification']]

    query['filter']['and'].append(
        {'or': classifications}
    )
    response = client.discovery.query(query)

    assets = [item['qualifiedName'] for item in response['value']
              if '/curated/data_quality/' not in item['qualifiedName']]

    for qname in assets:
        response = client.entity.get_by_unique_attributes(
            type_name='tabular_schema', attr_qualified_name=qname +
            '#__tabular_schema', min_ext_info=True, ignore_relationships=False)

        columns = {}

        for entity in response['referredEntities']:
            col = response['referredEntities'][entity]
            classifications = col.get('classifications')

            if classifications:
                cl_types = [item['typeName'] for item in classifications]
                cl_name = col['attributes']['name']

                columns[cl_name] = cl_types

        # Get the actual schema. Different matching for raw and staging/curated
        if (('/staging/' in qname or '/curated/' in qname) and
           '{SparkPartitions}' in qname):
            schema_qname = qname.replace('{SparkPartitions}',
                                         '#tabular_schema').replace('{Date}/',
                                                                    '')
        else:
            schema_qname = qname.replace('.parquet', '#tabular_schema')

        response = client.entity.get_by_unique_attributes(
            type_name='tabular_schema', attr_qualified_name=schema_qname,
            min_ext_info=True, ignore_relationships=False)

        for entity in response['referredEntities']:
            col = response['referredEntities'][entity]
            cl_name = col['attributes']['name']

            if cl_name in columns:
                # There is not upsert logic for classifications
                # Existing classifications are always preserved
                try:
                    client.entity.add_classifications(entity, columns[cl_name])
                except HttpResponseError:
                    client.entity.update_classifications(entity,
                                                         columns[cl_name])
                    pass

    return func.HttpResponse(status_code=200)
