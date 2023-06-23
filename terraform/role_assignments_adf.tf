# // Key Vault //
resource "azurerm_role_assignment" "adf_key_vault_secrets_user" {
  scope                = azurerm_key_vault.default.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = data.azurerm_data_factory.core.identity[0].principal_id
}