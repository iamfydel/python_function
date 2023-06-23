resource "azurerm_key_vault" "default" {
  name                = module.global.resource_names.key_vault
  location            = azurerm_resource_group.default.location
  resource_group_name = azurerm_resource_group.default.name

  sku_name                   = "standard"
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  soft_delete_retention_days = 7
  enable_rbac_authorization  = true

  tags = merge(
    module.global.resource_tags,
    {}
  )
}

