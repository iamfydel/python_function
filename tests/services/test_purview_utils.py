"""Unit tests for the purview_utils module.

"""
import json
import os
from unittest import expectedFailure
import pytest
from unittest.mock import patch
from azure.purview.catalog import PurviewCatalogClient
from azure.identity import DefaultAzureCredential
from services import purview_utils, utils

TEST_GET_DEPENDENCIES_GUID = {
    'entity': {
        'guid': 'fa0f1fa2-6199-11ec-90d6-0242ac120003'
    }
}

TEST_GET_DEPENDENCIES_LINEAGE = {
    'guidEntityMap': {
        'fa0f1fa2-6199-11ec-90d6-0242ac120003': {
            'guid': 'fa0f1fa2-6199-11ec-90d6-0242ac120003',
            'attributes': {
                'name': 'TestTable1',
                'objectType': 'U'
            }
        },
        '93ee2f82-619a-11ec-90d6-0242ac120003': {
            'typeName': 'test_table',
            'guid': '93ee2f82-619a-11ec-90d6-0242ac120003',
            'attributes': {
                'name': 'TestTable2',
                'objectType': 'U'
            }
        },
        'b6cd821e-619a-11ec-90d6-0242ac120003': {
            'guid': 'b6cd821e-619a-11ec-90d6-0242ac120003',
            'attributes': {
                'name': 'ShouldBeExcluded'
            }
        },
        '2f7215fe-619b-11ec-90d6-0242ac120003': {
            'typeName': 'test_other_table',
            'guid': '2f7215fe-619b-11ec-90d6-0242ac120003',
            'attributes': {
                'name': 'TestTable3',
                'objectType': 'U'
            }
        }
    }
}


GET_DEPENDENCIES_TEST_ENV_VAR = [
    ("AZURE_CLIENT_ID", "3670de26-8x8f-4d21-a56c-dc2b2c1n9b7r"),
    ("AZURE_CLIENT_SECRET", "F-X7Q~oZvVA2mBiBT13r2fMRA7OJG~rHUAln-"),
    ("AZURE_TENANT_ID", "a4c0e09b-emef-4091-8ca2-475t06091n20")
]


@patch.dict(os.environ, GET_DEPENDENCIES_TEST_ENV_VAR, clear=True)
@pytest.mark.dev
def test_get_dependencies():
    """Test the get_dependencies function
    """
    expected_dependencies = [
        'TestTable2 (test_table)',
        'TestTable3 (test_other_table)']

    client = PurviewCatalogClient(
        endpoint='https://',
        credential=DefaultAzureCredential())
    client.entity.get_by_unique_attributes = (
        lambda entity_type, attr_qualified_name: TEST_GET_DEPENDENCIES_GUID
    )
    client.lineage.get_lineage_graph = (
        lambda entity_guid, direction="OUTPUT": TEST_GET_DEPENDENCIES_LINEAGE
    )

    assert purview_utils.get_dependencies(
        client, 'Qname', 'EntityType') == expected_dependencies


TEST_BUILD_PURVIEW_QNAME = [
    ('asset1',
     'dbo',
     'azure_sql_table',
     'serv.net/test',
     'mssql://serv.net/test/dbo/asset1')]


@pytest.mark.parametrize(
    'name, schema, entity_type, server_name, expected_result',
    TEST_BUILD_PURVIEW_QNAME)
@pytest.mark.dev
def test_build_purview_qname(
        name: str,
        schema: str,
        entity_type: str,
        server_name: str,
        expected_result: str):
    """Test the build_purview_qname function
    """
    assert (
        purview_utils.build_purview_qname(
            name,
            schema,
            entity_type,
            server_name) == expected_result)


@pytest.mark.dev
def test_build_purview_qname_default():
    """Test that the build_purview_qname function returns a default
        prefix if the required entity_type does not have a prefix
        mapping in ENTITY_TYPE_PREFIX_MAPPING
    """
    assert(
        purview_utils.build_purview_qname(
            'name', 'schema', 'KpO9f_bt', 'server_name')
        == 'mssql://server_name/schema/name'
    )


TEST_GET_DEPENDENCIES_LIST = r'''
{
    "run_id": "145e0760-f873-46e8-a939-e70834c396af",
    "error_message": "ErrorCode=SqlFailedToConnect",
    "entity_type": "azure_sql_table",
    "system": "Template",
    "server_name": "https://serv.com/test",
    "version": 1,
    "displayName": "Customer",
    "name": "Customer",
    "schema": "SalesLT",
    "type": "full",
    "granularity": "day"
}
'''


@patch.dict(os.environ, GET_DEPENDENCIES_TEST_ENV_VAR, clear=True)
@pytest.mark.dev
def test_get_dependencies_list():
    """Test the get_dependencies_list function
    """
    expected_dependencies = {
        'TestTable2 (test_table)',
        'TestTable3 (test_other_table)'}

    client = PurviewCatalogClient(
        endpoint='https://',
        credential=DefaultAzureCredential())

    client.entity.get_by_unique_attributes = (
        lambda entity_type, attr_qualified_name: TEST_GET_DEPENDENCIES_GUID
    )
    client.lineage.get_lineage_graph = (
        lambda entity_guid, direction="OUTPUT": TEST_GET_DEPENDENCIES_LINEAGE
    )

    test_input = [utils.ErrorContext(json.loads(TEST_GET_DEPENDENCIES_LIST))]

    assert purview_utils.get_dependencies_list(
        client, test_input) == expected_dependencies


@pytest.mark.dev
def test_build_adf_qname():
    """Test the build_adf_qname function
    """
    expected_result = ('/subscriptions/sub/resourceGroups/rg/'
                       'providers/Microsoft.DataFactory/factories/test')
    assert (purview_utils.build_adf_qname('test', 'sub', 'rg')
            == expected_result)


@pytest.mark.dev
def test_build_adf_pipeline_qname():
    """Test the build_adf_qname function
    """
    expected_result = ('/subscriptions/sub/resourceGroups/rg/'
                       'providers/Microsoft.DataFactory/factories/test/'
                       'pipelines/pl')
    assert (purview_utils.build_adf_pipeline_qname('test', 'sub', 'rg', 'pl')
            == expected_result)


TEST_CONFIG = {
    'displayName': 'asset',
    'version': 1,
    'system': 'test'
}


@pytest.mark.dev
def test_build_raw_file_qname():
    """Test the build_adf_qname function
    """
    config = utils.DataEntity(TEST_CONFIG)

    expected_result = ('https://datalake.dfs.core.windows.net/raw/test/asset/'
                       'v1/{Year}/{Month}/{Day}/asset')
    assert (purview_utils.build_raw_file_qname('datalake', config)
            == expected_result)


@pytest.mark.dev
def test_build_staging_file_qname():
    """Test the build_adf_qname function
    """
    config = utils.DataEntity(TEST_CONFIG)

    expected_result = ('https://datalake.dfs.core.windows.net/staging/test'
                       '/asset/v1/')
    assert (purview_utils.build_staging_file_qname('datalake', config)
            == expected_result)


@pytest.mark.dev
def test_build_curated_file_qname():
    """Test the build_curated_file_qname function
    """
    expected_result = ('https://datalake.dfs.core.windows.net/curated/test/')
    assert (purview_utils.build_curated_file_qname('datalake', 'test')
            == expected_result)


@pytest.mark.dev
def test_build_adf_activity_qname():
    """Test the build_adf_qname function
    """
    adf_pipeline = ('/subscriptions/sub/resourceGroups/rg/'
                    'providers/Microsoft.DataFactory/factories/test/'
                    'pipelines/pl')

    expected_result = f'{adf_pipeline}/activities/activity'
    assert (purview_utils.build_adf_activity_qname(adf_pipeline, 'activity')
            == expected_result)


TEST_PURVIEW_PREFIX = [
    ('azure_sql_table', 'mssql'),
    ('oracle_table', 'oracle'),
    ('other', 'mssql'),
    (None, 'mssql')
]


@pytest.mark.parametrize('entity_type, expected_result', TEST_PURVIEW_PREFIX)
@pytest.mark.dev
def test_get_server_prefix(entity_type: str, expected_result: str):
    """Test the get_server_prefix function
    """
    assert purview_utils.get_server_prefix(entity_type) == expected_result


TEST_PURVIEW_DATATYPE = [
    ('string', 'String'),
    ('int', 'Int32'),
    ('integer', 'Int32'),
    ('long', 'Int64'),
    ('decimal', 'Decimal'),
    ('bigint', 'Int64'),
    ('timestamp', 'DateTime'),
    ('date', 'DateTime'),
    ('boolean', 'Boolean'),
    ('double', 'Double')
]


@pytest.mark.parametrize('data_type, expected_result', TEST_PURVIEW_DATATYPE)
@pytest.mark.dev
def test_get_purview_data_type(data_type: str, expected_result: str):
    """Test the get_purview_data_type function
    """
    assert (
        purview_utils.get_purview_data_type(data_type) == expected_result)


@pytest.mark.dev
def test_get_purview_columns():
    """Test the get_purview_columns function
    """
    base_qname = 'https://datalake.dfs.core.windows.net/raw/test/asset/v1/'
    columns = [
        utils.DataEntity({
            "name": "id",
            "type": "int"
        }),
        utils.DataEntity({
            "name": "name",
            "type": "string"
        })
    ]
    expected_result = [
        {
            "typeName": "column",
            "attributes": {
                "qualifiedName": f"{base_qname}#tabular_schema//id",
                "name": "id",
                "type": "Int32"
            },
            "relationshipAttributes": {
                "composeSchema": {
                    "guid": -200
                }
            }
        },
        {
            "typeName": "column",
            "attributes": {
                "qualifiedName": f"{base_qname}#tabular_schema//name",
                "name": "name",
                "type": "String"
            },
            "relationshipAttributes": {
                "composeSchema": {
                    "guid": -200
                }
            }
        }
    ]

    assert (
        purview_utils.get_purview_columns(columns, base_qname, -200)
        == expected_result)


TEST_COLUMNS_STAGING_MAPPING = [
    utils.DataEntity({
        "name": "id",
        "type": "int",
        "system": 'sys1',
        "source_name": "DV_ID",
        "source_dataset": "source1"
    }),
    utils.DataEntity({
        "name": "name",
        "type": "string",
        "system": 'sys1',
        "source_name": "DV_NAME",
        "source_dataset": "source1"
    }),
    utils.DataEntity({
        "name": "age",
        "type": "int",
        "system": 'sys2',
        "source_name": "DV_AGE",
        "source_dataset": "source2"
    })
]

TEST_COLUMNS_CURATED_MAPPING = [
    utils.DataEntity({
        "name": "id",
        "type": "int",
        "system": 'curated',
        "source_name": "DV_ID",
        "source_dataset": "source1"
    }),
    utils.DataEntity({
        "name": "name",
        "type": "string",
        "system": 'curated',
        "source_name": "DV_NAME",
        "source_dataset": "source1"
    }),
    utils.DataEntity({
        "name": "age",
        "type": "int",
        "system": 'curated',
        "source_name": "DV_AGE",
        "source_dataset": "source2"
    })
]


@pytest.mark.dev
def test_get_purview_column_mapping_staging():
    """Test the get_purview_column_mapping function
    """
    expected_result = '[{"DatasetMapping": {"Source": "https://lake.dfs.core.windows.net/staging/sys1/source1/v1/", "Sink": "sink"}, "ColumnMapping": [{"Source": "DV_ID", "Sink": "id"}, {"Source": "DV_NAME", "Sink": "name"}]}, {"DatasetMapping": {"Source": "https://lake.dfs.core.windows.net/staging/sys2/source2/v1/", "Sink": "sink"}, "ColumnMapping": [{"Source": "DV_AGE", "Sink": "age"}]}]'

    assert purview_utils.get_purview_column_mapping(
        TEST_COLUMNS_STAGING_MAPPING, 'lake', 'sink') == expected_result


@pytest.mark.dev
def test_get_purview_column_mapping_curated():
    """Test the get_purview_column_mapping function
    """
    expected_result = '[{"DatasetMapping": {"Source": "https://lake.dfs.core.windows.net/curated/source1/", "Sink": "sink"}, "ColumnMapping": [{"Source": "DV_ID", "Sink": "id"}, {"Source": "DV_NAME", "Sink": "name"}]}, {"DatasetMapping": {"Source": "https://lake.dfs.core.windows.net/curated/source2/", "Sink": "sink"}, "ColumnMapping": [{"Source": "DV_AGE", "Sink": "age"}]}]'

    assert purview_utils.get_purview_column_mapping(
        TEST_COLUMNS_CURATED_MAPPING, 'lake', 'sink') == expected_result


@pytest.mark.dev
def test_get_purview_datasets_staging():
    """Test the get_purview_datasets function
    """
    expected_result = [
        {
            'typeName': 'azure_datalake_gen2_resource_set',
            'uniqueAttributes': {
                'qualifiedName': 'https://lake.dfs.core.windows.net/staging/sys1/source1/v1/'
            }
        },
        {
            'typeName': 'azure_datalake_gen2_resource_set',
            'uniqueAttributes': {
                'qualifiedName': 'https://lake.dfs.core.windows.net/staging/sys2/source2/v1/'
            }
        }
    ]

    assert(purview_utils.get_purview_datasets(
        TEST_COLUMNS_STAGING_MAPPING, 'lake') == expected_result)


@pytest.mark.dev
def test_get_purview_datasets_curated():
    """Test the get_purview_datasets function
    """
    expected_result = [
        {
            'typeName': 'azure_datalake_gen2_resource_set',
            'uniqueAttributes': {
                'qualifiedName': 'https://lake.dfs.core.windows.net/curated/source1/'
            }
        },
        {
            'typeName': 'azure_datalake_gen2_resource_set',
            'uniqueAttributes': {
                'qualifiedName': 'https://lake.dfs.core.windows.net/curated/source2/'
            }
        }
    ]

    assert(purview_utils.get_purview_datasets(
        TEST_COLUMNS_CURATED_MAPPING, 'lake') == expected_result)


@pytest.mark.dev
def test_get_purview_search_query():
    """Test the purview_search_query function
    """
    expected_result = {
        "keywords": "key",
        "limit": 1,
        "filter": {
            "and": [
                {
                    "collectionId": "colTest"
                },
                {
                    "entityType": "azure"
                }
            ]
        }
    }

    assert(purview_utils.purview_search_query('key', 'colTest', 'azure')
           == expected_result)
