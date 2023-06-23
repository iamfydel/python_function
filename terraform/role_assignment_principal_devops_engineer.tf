# // Key Vault //
resource "azurerm_role_assignment" "principal_devops_engineer_keyvault_admin" {
  scope                = azurerm_key_vault.default.id
  role_definition_name = "Key Vault Administrator"
  principal_id         = local.principal_devops_engineer_object_id
}
