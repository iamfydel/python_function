resource "azurerm_key_vault_secret" "service_desk_password" {
  name         = "service-desk-password"
  value        = var.service_desk_password
  key_vault_id = azurerm_key_vault.default.id

  depends_on = [
    azurerm_role_assignment.terraform_spn_key_vault_admin
  ]
}

resource "azurerm_key_vault_secret" "service_bus_connection_string" {
  name         = "service-bus-connection-string"
  value        = var.service_bus_connection
  key_vault_id = azurerm_key_vault.default.id

  depends_on = [
    azurerm_role_assignment.terraform_spn_key_vault_admin
  ]
}

resource "azurerm_key_vault_secret" "powerbi_spn_secret" {
  name         = "powerbi-spn-secret"
  value        = var.powerbi_client_secret
  key_vault_id = azurerm_key_vault.default.id

  depends_on = [
    azurerm_role_assignment.terraform_spn_key_vault_admin
  ]
}

resource "azurerm_key_vault_secret" "default_function_key" {
  name         = "support-utils-function-default-key"
  value        = data.azurerm_function_app_host_keys.default.default_function_key
  key_vault_id = azurerm_key_vault.default.id

  depends_on = [
    azurerm_role_assignment.terraform_spn_key_vault_admin
  ]
}