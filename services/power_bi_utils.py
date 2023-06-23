"""
Utils functions for PowerBI
"""
import requests
import logging


class PowerBIClient:
    """
    Anchor's PowerBI client that allows users to interact with the API
    """
    def __init__(self, tenant_id: str, client_id: str, client_secret: str):
        self._tenant_id = tenant_id
        self._client_id = client_id
        self._client_secret = client_secret

    def _get_access_token(self) -> str:
        """
        Get the access token needed to call PowerBI APIs.

        :return: The access token
        """
        try:
            url = f"https://login.microsoftonline.com/{self._tenant_id}/oauth2/token?api-version=1.0"
            body = {
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "grant_type": "client_credentials",
                "resource": "https://analysis.windows.net/powerbi/api"
            }
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            response = requests.post(url, data=body, headers=headers)
            if response.status_code == 200:
                json_response = response.json()
                access_token = json_response['access_token']
            else:
                raise Exception("Error authenticating to microsoft to get a bearer token")
        except requests.exceptions.RequestException as request_exception:
            raise Exception("Error with API requests") from request_exception
        except Exception as e:
            raise Exception("Error getting access token for PowerBI") from e
        else:
            return access_token

    def get_workspace_id(self, powerbi_organisation: str, workspace_name: str) -> str:
        """
        Gets the workspace id from the workspace name
        :param powerbi_organisation: The organisation name used to create powerBI instance
        :param workspace_name      : The name of the workspace for which to return the ID
        :return: The ID of the workspace
        """
        try:
            url = f"https://api.powerbi.com/v1.0/{powerbi_organisation}/groups?$filter=name eq '{workspace_name}'"
            headers = {
                "Authorization": "Bearer " + self._get_access_token()
            }
            response = requests.get(url=url, headers=headers)
            if response.status_code == 200:
                json_response = response.json()
                if len(json_response['value']) == 1:
                    workspace_id = json_response['value'][0]['id']
                else:
                    raise Exception("Error finding the correct workspace")
            else:
                raise Exception("Error connecting to the PowerBI API to get the workspace ID")
        except requests.exceptions.RequestException as request_exception:
            raise Exception("Error with API requests") from request_exception
        except Exception as e:
            raise Exception("Error getting workspace ID for PowerBI") from e
        else:
            return workspace_id

    def get_dataset_id(self, powerbi_organisation: str, workspace_id: str, dataset_name: str) -> str:
        """
        Gets the dataset id from the dataset name
        :param powerbi_organisation: The organisation name used to create powerBI instance
        :param workspace_id        : The ID of the workspace where the dataset lives
        :param dataset_name        : The name of the dataset for which to return the ID
        :return: The ID of the dataset
        """
        try:
            url = f"https://api.powerbi.com/v1.0/{powerbi_organisation}/groups/{workspace_id}/datasets"
            headers = {
                "Authorization": "Bearer " + self._get_access_token()
            }
            response = requests.get(url=url, headers=headers)
            if response.status_code == 200:
                json_response = response.json()
                datasets_filtered = [dataset for dataset in json_response['value'] if dataset['name'] == dataset_name]
                if len(datasets_filtered) == 1:
                    dataset_id = datasets_filtered[0]['id']
                else:
                    raise Exception("Error finding the correct Dataset")
            else:
                raise Exception("Error connecting to the PowerBI API to get the Dataset ID")
        except requests.exceptions.RequestException as request_exception:
            raise Exception("Error with API requests") from request_exception
        except Exception as e:
            raise Exception("Error getting Dataset ID for PowerBI") from e
        else:
            return dataset_id

    def refresh_dataset(self, powerbi_organisation: str, workspace_id: str, dataset_id: str) -> bool:
        """
        Refreshes a PowerBI dataset.
        :param powerbi_organisation: The organisation name used to create powerBI instance
        :param workspace_id        : The ID of the workspace where the dataset lives
        :param dataset_id          : The ID of the dataset to refresh
        :return:
        """
        try:
            url = f"https://api.powerbi.com/v1.0/{powerbi_organisation}/groups/{workspace_id}/datasets/{dataset_id}/refreshes"
            headers = {
                "Authorization": "Bearer " + self._get_access_token()
            }
            response = requests.post(url=url, headers=headers)
            if response.status_code == 202:
                refresh_status = True
            elif response.status_code == 429:
                logging.warn("Too many requests to refresh this powerBI dataset")
                refresh_status = True
            else:
                refresh_status = False
        except requests.exceptions.RequestException as request_exception:
            raise Exception("Error with API requests") from request_exception
        except Exception as e:
            raise Exception("Error refreshing Dataset") from e
        else:
            return refresh_status
