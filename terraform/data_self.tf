data "azurerm_function_app_host_keys" "default" {
  name                = azurerm_function_app.default.name
  resource_group_name = azurerm_resource_group.default.name
}