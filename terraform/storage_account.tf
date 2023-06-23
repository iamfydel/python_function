resource "azurerm_storage_account" "default" {
  name                     = module.global.resource_names.storage_account
  resource_group_name      = azurerm_resource_group.default.name
  location                 = azurerm_resource_group.default.location
  account_kind             = "StorageV2"
  account_tier             = "Standard"
  account_replication_type = "LRS"

  tags = merge(
    module.global.resource_tags,
    {}
  )
}

resource "azurerm_storage_container" "error_files" {
  name                 = "error-files"
  storage_account_name = azurerm_storage_account.default.name
}
