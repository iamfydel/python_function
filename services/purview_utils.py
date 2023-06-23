"""Utils functions for Azure Purview.

"""
import json
import re
from typing import Dict, List
from azure.purview.catalog import PurviewCatalogClient
from dataclasses import asdict

from services.utils import DataEntity

ENTITY_TYPE_PREFIX_MAPPING = {
    'azure_sql_table': 'mssql',
    'oracle_table': 'oracle'
}


PURVIEW_DATA_TYPE_MAPPING = {
    'string': 'String',
    'decimal': 'Decimal',
    'integer': 'Int32',
    'int': 'Int32',
    'bigint': 'Int64',
    'long': 'Int64',
    'timestamp': 'DateTime',
    'date': 'DateTime',
    'boolean': 'Boolean',
    'double': 'Double'
}


def get_dependencies(
        client: PurviewCatalogClient,
        entity_qname: str,
        entity_type: str) -> List[str]:
    """Get the dependencies of the input asset.

    Args:
        client (PurviewCatalogClient): An authentified Purview client object
        entity_qname (str): The qualified name of the asset
        entity_type (str): The entity type of the asset

    Returns:
        List[str]: A list of dependent assets with their type
    """
    try:
        response_get_id = client.entity.get_by_unique_attributes(
            entity_type, attr_qualified_name=entity_qname)
        entity_guid = response_get_id['entity']['guid']

        response_lineage = client.lineage.get_lineage_graph(
            entity_guid, direction="OUTPUT")

        return [f"{attr['attributes']['name']} ({attr.get('typeName')})"
                for attr in response_lineage['guidEntityMap'].values()
                if (attr['guid'] != entity_guid and
                    attr['attributes'].get('objectType') is not None)]
    except (Exception):
        return ['No affected dependencies']


def build_adf_qname(
        name: str,
        subscription: str,
        resource_group: str) -> str:
    """Build an Azure Purview fully qualified name based on input parameters.

    Args:
        name (str): The ADF instance name
        subscription (str): The Azure subscription
        resource_group (str): The Azure resource group

    Returns:
        str: An Azure Purview ADF qualified name
    """
    return (f'/subscriptions/{subscription}/resourceGroups/{resource_group}/'
            f'providers/Microsoft.DataFactory/factories/{name}')


def build_adf_pipeline_qname(
        name: str,
        subscription: str,
        resource_group: str,
        pipeline_name: str) -> str:
    """Build an Azure Purview fully qualified name based on input parameters.

    Args:
        name (str): The ADF instance name
        subscription (str): The Azure subscription
        resource_group (str): The Azure resource group
        pipeline_name (str): The name of the pipeline

    Returns:
        str: An Azure Purview ADF pipeline qualified name
    """
    adf_qname = build_adf_qname(name, subscription, resource_group)

    return (f'{adf_qname}/pipelines/{pipeline_name}')


def build_adf_activity_qname(
        pipeline_name: str,
        activity_name: str) -> str:
    """Build an Azure Purview fully qualified name based on input parameters.

    Args:
        pipeline_name (str): The name of the ADF pipeline
        activity_name (str): The name of the ADF activity

    Returns:
        str: An Azure Purview ADF Activity qualified name
    """
    return (f"{pipeline_name}/activities/{activity_name}")


def build_raw_file_qname(
        datalake_name: str,
        config: DataEntity) -> str:
    """Build an Azure Purview fully qualified name based on input parameters.

    Args:
        datalake_name (str): The name of the Azure Data Lake
        config (DataEntity): A config item for the asset

    Returns:
        str: An Azure Purview raw file qualified name
    """
    return (f"https://{datalake_name}.dfs.core.windows"
            f".net/raw/{config.system}/{config.display_name}/v"
            f"{config.version}/{{Year}}/{{Month}}/{{Day}}/"
            f"{config.display_name}")


def build_staging_file_qname(
        datalake_name: str,
        config: DataEntity) -> str:
    """Build an Azure Purview fully qualified name based on input parameters.

    Args:
        datalake_name (str): The name of the Azure Data Lake
        config (DataEntity): A config item for the asset

    Returns:
        str: An Azure Purview staging file qualified name
    """
    return (f"https://{datalake_name}.dfs.core.windows.net/staging/"
            f"{config.system}/{config.display_name}/v{config.version}/")


def build_curated_file_qname(
        datalake_name: str,
        filename: str) -> str:
    """Build an Azure Purview fully qualified name based on input parameters.

    Args:
        datalake_name (str): The name of the Azure Data Lake
        filename (str): The filename of the curated file

    Returns:
        str: An Azure Purview curated file qualified name
    """
    return (f"https://{datalake_name}.dfs.core.windows.net/curated/"
            f"{filename}/")


def get_server_prefix(entity_type: str) -> str:
    """Returns an Azure Purview server prefix.

    Args:
        entity_type (str): The entity type

    Returns:
        str: An Azure Purview server prefix name
    """
    prefix = ENTITY_TYPE_PREFIX_MAPPING.get(entity_type, 'mssql')
    if not prefix:
        raise KeyError(
            f'No prefix could be found for the entity type "{entity_type}"')

    return prefix


def build_purview_qname(
        name: str,
        schema: str,
        entity_type: str,
        server_name: str) -> str:
    """Build an Azure Purview fully qualified name based on input parameters.

    Args:
        name (str): The asset name
        schema (str): The asset schema
        entity_type (str): The entity type
        server_name (str): The qualified server name (e.g xxx.net/db)

    Raises:
        Exception: If the mapping between entity type and prefix
        cannot be found
        in ENTITY_TYPE_PREFIX_MAPPING.

    Returns:
        str: An Azure Purview asset fully qualified name
    """
    prefix = get_server_prefix(entity_type)

    return f'{prefix}://{server_name}/{schema}/{name}'


def get_dependencies_list(
        client: PurviewCatalogClient,
        error_context) -> List[str]:
    """Get a list of dependencies based on the input error context.

    Args:
        client (PurviewCatalogClient): An authentified Purview client object
        error_context ([type]): The error context

    Returns:
        List[str]: A list of distinct dependent assets with their type
    """
    affected_dependencies = set()

    for asset in error_context:
        asset_qname = build_purview_qname(asset.name, asset.schema,
                                          asset.entity_type, asset.server_name)
        dependencies = get_dependencies(client, asset_qname, asset.entity_type)

        for dependency in dependencies:
            if dependency not in affected_dependencies:
                affected_dependencies.add(dependency)

    return affected_dependencies


def get_purview_data_type(data_type: str) -> str:
    """Get the Purview data type based on the input data type.

    Args:
        data_type (str): The data type

    Returns:
        str: The Purview data type
    """
    type = re.sub(r'\(.*\)', '', data_type)

    purview_data_type = PURVIEW_DATA_TYPE_MAPPING.get(type)
    if not purview_data_type:
        raise KeyError(
            f'No Purview type could be found for the data type "{data_type}"')

    return purview_data_type


def get_purview_columns(columns: List[DataEntity], base_qname: str,
                        guid: int) -> Dict:
    """Get a list Purview columns definition.

    Args:
        columns (List[DataEntity]): A list of columns.
        base_qname (str): The base qualified name of the asset
        guid (int): The parent GUID

    Returns:
        Dict: The list of Purview columns definition
    """
    columns_def = []

    for col in columns:
        col_def = {
            "typeName": "column",
            "attributes": {
                "qualifiedName": f"{base_qname}#tabular_schema//{col.name}",
                "name": col.name,
                "type": get_purview_data_type(col.type)
            },
            "relationshipAttributes": {
                "composeSchema": {
                    "guid": guid
                }
            }
        }
        columns_def.append(col_def)

    return columns_def


def get_purview_column_mapping(columns: List[DataEntity],
                               datalake_name: str,
                               sink_qname: str) -> str:
    """Get a list of Purview column mapping definition.

    Args:
        columns (List[DataEntity]): A list of columns to map
        datalake_name (str): The name of the Azure Data Lake
        sink_qname (str): The qualified name of the sink file

    Returns:
        str: The Purview columns definition
    """
    seen = set()
    sources = [col.source_dataset for col in columns if not
               (col.source_dataset in seen or seen.add(col.source_dataset))]
    mapping = []

    for source in sources:
        items = [col for col in columns if col.source_dataset == source]

        payload = asdict(items[0])
        payload['display_name'] = items[0].source_dataset
        config = DataEntity(payload)

        if config.system == 'curated':
            qname = build_curated_file_qname(datalake_name,
                                             config.source_dataset)
        else:
            qname = build_staging_file_qname(datalake_name, config)

        mapping.append({
            "DatasetMapping": {
                "Source": qname,
                "Sink": sink_qname
            },
            "ColumnMapping": [{"Source": item.source_name, "Sink": item.name}
                              for item in items]
        })

    return json.dumps(mapping)


def get_purview_datasets(columns: List[DataEntity],
                         datalake_name: str) -> Dict:
    """Get a list of Purview datasets.

    Args:
        columns (List[DataEntity]): A list of columns to map
        datalake_name (str): The name of the Azure Data Lake

    Returns:
        str: The Purview datasets definition
    """
    # sources = set(col.source_dataset for col in columns)
    seen = set()
    sources = [col.source_dataset for col in columns if not
               (col.source_dataset in seen or seen.add(col.source_dataset))]
    datasets = []

    for source in sources:
        items = [col for col in columns if col.source_dataset == source]

        payload = asdict(items[0])
        payload['display_name'] = items[0].source_dataset
        config = DataEntity(payload)

        if config.system == 'curated':
            qname = build_curated_file_qname(datalake_name,
                                             config.source_dataset)
        else:
            qname = build_staging_file_qname(datalake_name, config)

        datasets.append({
            "typeName": "azure_datalake_gen2_resource_set",
            "uniqueAttributes": {
                "qualifiedName": qname
            }
        })

    return datasets


def purview_search_query(keyword: str, collection: str,
                         entity_type: str) -> Dict:
    """Return a single Purview search query

    Args:
        keyword (str): A search keyword
        collection (str): The collection to search
        entity_type (str): The entity type to search

    Returns:
        Dict: The Purview search query
    """
    return {
        "keywords": keyword,
        "limit": 1,
        "filter": {
            "and": [
                {
                    "collectionId": collection
                },
                {
                    "entityType": entity_type
                }
            ]
        }
    }
