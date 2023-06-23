# // Key Vault //
resource "azurerm_role_assignment" "devops_engineer_keyvault_read" {
  scope                = azurerm_key_vault.default.id
  role_definition_name = "Key Vault Reader"
  principal_id         = local.devops_engineer_object_id
}