resource "azurerm_data_factory_linked_service_key_vault" "default" {
  name                = "ls_keyvault_${var.domain}_${var.service}"
  resource_group_name = var.env_core_infra_resource_group_name
  data_factory_name   = var.adf_account_name
  key_vault_id        = azurerm_key_vault.default.id

  depends_on = [
    azurerm_role_assignment.adf_key_vault_secrets_user
  ]
}

resource "azurerm_data_factory_linked_service_azure_function" "default" {
  name                = "ls_fapp_${var.domain}_${var.service}"
  resource_group_name = var.env_core_infra_resource_group_name
  data_factory_name   = var.adf_account_name
  url                 = "https://${azurerm_function_app.default.default_hostname}"
  key_vault_key {
    linked_service_name = azurerm_data_factory_linked_service_key_vault.default.name
    secret_name         = azurerm_key_vault_secret.default_function_key.name
  }
}