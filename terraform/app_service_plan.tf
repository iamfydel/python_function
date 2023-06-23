resource "azurerm_app_service_plan" "default" {
  name                = module.global.resource_names.service_plan
  location            = azurerm_resource_group.default.location
  resource_group_name = azurerm_resource_group.default.name
  kind                = "Linux"
  reserved            = true

  sku {
    tier = "PremiumV3"
    size = "P1v3"
  }
  tags = merge(
    module.global.resource_tags,
    {}
  )
}