# // Key Vault //
resource "azurerm_role_assignment" "terraform_spn_key_vault_admin" {
  scope                = azurerm_key_vault.default.id
  role_definition_name = "Key Vault Administrator"
  principal_id         = data.azurerm_client_config.current.object_id
}