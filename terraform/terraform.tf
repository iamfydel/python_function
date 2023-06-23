terraform {
  backend "azurerm" {
    resource_group_name  = "ap-uks-sub-nonprod-base-infra-rg"
    storage_account_name = "apukssubnpbseinfsa"
    container_name       = "tfstate"
    key                  = "adp-env-support-utils"
  }

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 2.87.0"
    }

    databricks = {
      source  = "databrickslabs/databricks"
      version = "~> 0.4.0"
    }

  }

  required_version = "~> 1.0"
}

provider "azurerm" {
  features {}
}

provider "databricks" {
  host                        = data.azurerm_databricks_workspace.core.workspace_url
  azure_workspace_resource_id = data.azurerm_databricks_workspace.core.id

  # ARM_USE_MSI environment variable is recommended
  azure_use_msi = true
}
