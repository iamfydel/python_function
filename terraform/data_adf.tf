data "azurerm_data_factory" "core" {
  name                = var.adf_account_name
  resource_group_name = var.env_core_infra_resource_group_name
}