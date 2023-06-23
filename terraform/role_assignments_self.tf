# // Key Vault //
resource "azurerm_role_assignment" "secrets_user" {
  scope                = azurerm_key_vault.default.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.default.principal_id
}

# // Storage Account - error-files container //
resource "azurerm_role_assignment" "storage_blob_contributor_access" {
  scope                = azurerm_storage_container.error_files.resource_manager_id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_user_assigned_identity.default.principal_id
}

# // Purview //
resource "null_resource" "az_function_uai_purview" {
  triggers = {
    always_run = "${timestamp()}"
  }

  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-c"]
    command     = <<-EOT
      pwsh ../../../global_infra/scripts/Set-PurviewPermissions.ps1 \
        -tenantId "$ARM_TENANT_ID" \
        -ClientId "$ARM_CLIENT_ID" -ClientSecret "$ARM_CLIENT_SECRET" \
        -accountName "${var.purview_account_name}" \
        -collectionName "${var.purview_account_name}" \
        -roleNames "collection-administrator,data-curator,data-source-administrator" \
        -objectId "${azurerm_user_assigned_identity.default.principal_id}"
    EOT
  }

  depends_on = [
    azurerm_function_app.default
  ]
}
