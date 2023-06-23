data "azurerm_databricks_workspace" "core" {
  name                = var.databricks_workspace_name
  resource_group_name = var.env_core_infra_resource_group_name
}