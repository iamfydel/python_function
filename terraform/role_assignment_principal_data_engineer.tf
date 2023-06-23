# // Resource Group //
resource "azurerm_role_assignment" "principal_data_engineer_resource_group_read" {
  count = var.scope_name != "d01" ? 1 : 0

  scope                = azurerm_resource_group.default.id
  role_definition_name = "Reader"
  principal_id         = local.principal_data_engineer_object_id
}

resource "azurerm_role_assignment" "principal_data_engineer_resource_group_contributor" {
  count = var.scope_name == "d01" ? 1 : 0

  scope                = azurerm_resource_group.default.id
  role_definition_name = "Contributor"
  principal_id         = local.principal_data_engineer_object_id
}

# // Key Vault //
resource "azurerm_role_assignment" "principal_data_engineer_keyvault_read" {
  scope                = azurerm_key_vault.default.id
  role_definition_name = "Key Vault Reader"
  principal_id         = local.principal_data_engineer_object_id
}