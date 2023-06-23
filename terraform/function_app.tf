resource "azurerm_function_app" "default" {
  name                       = module.global.resource_names.function_app
  location                   = azurerm_resource_group.default.location
  resource_group_name        = azurerm_resource_group.default.name
  app_service_plan_id        = azurerm_app_service_plan.default.id
  storage_account_name       = azurerm_storage_account.default.name
  storage_account_access_key = azurerm_storage_account.default.primary_access_key
  os_type                    = "linux"
  version                    = "~4"
  https_only                 = true
  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.default.id]
  }
  key_vault_reference_identity_id = azurerm_user_assigned_identity.default.id
  app_settings = {
    APPINSIGHTS_INSTRUMENTATIONKEY  = var.app_insights_ikey
    FUNCTIONS_WORKER_RUNTIME        = "python"
    PYTHON_ENABLE_WORKER_EXTENSIONS = 1
    AzureWebJobsStorage             = ""
    environment                     = var.scope_name
    service_desk_base_url           = var.service_desk_base_url
    service_desk_auth_endpoint      = "/token?auth_mode=Internal"
    service_desk_client_id          = var.service_desk_client_id
    service_desk_username           = var.service_desk_username
    service_desk_password           = "@Microsoft.KeyVault(VaultName=${azurerm_key_vault.default.name};SecretName=${azurerm_key_vault_secret.service_desk_password.name})"
    purview_account_name            = var.purview_account_name
    errorlog__clientId              = azurerm_user_assigned_identity.default.client_id
    errorlog__credential            = "managedidentity"
    errorlog__serviceUri            = azurerm_storage_account.default.primary_blob_endpoint
    azure_resource_group            = var.env_core_infra_resource_group_name
    azure_subscription              = data.azurerm_client_config.current.subscription_id
    datalake_name                   = var.datalake_name
    service_bus_connection          = "@Microsoft.KeyVault(VaultName=${azurerm_key_vault.default.name};SecretName=${azurerm_key_vault_secret.service_bus_connection_string.name})"
    service_bus_topic               = var.service_bus_topic
    powerbi_organisation            = "myorg"
    powerbi_tenant_id               = var.powerbi_tenant_id
    powerbi_client_id               = var.powerbi_client_id
    powerbi_client_secret           = "@Microsoft.KeyVault(VaultName=${azurerm_key_vault.default.name};SecretName=${azurerm_key_vault_secret.powerbi_spn_secret.name})"
  }
  tags = merge(
    module.global.resource_tags,
    {}
  )
  site_config {
    linux_fx_version = "Python|3.8"
  }
}

resource "azurerm_user_assigned_identity" "default" {
  resource_group_name = azurerm_resource_group.default.name
  location            = azurerm_resource_group.default.location

  name = module.global.resource_names.user_assigned_identity
  tags = merge(
    module.global.resource_tags,
    {}
  )
}