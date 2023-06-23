resource "databricks_secret_scope" "support_utils_function" {
  name = "support-utils-function"
}

resource "databricks_secret" "create_staging_metadata_function_url" {
  key          = "create_staging_metadata_function_url"
  string_value = "https://${azurerm_function_app.default.default_hostname}/api/create_staging_metadata?code=${data.azurerm_function_app_host_keys.default.default_function_key}"
  scope        = databricks_secret_scope.support_utils_function.id
}

resource "databricks_secret" "create_curated_metadata_function_url" {
  key          = "create_curated_metadata_function_url"
  string_value = "https://${azurerm_function_app.default.default_hostname}/api/create_curated_metadata?code=${data.azurerm_function_app_host_keys.default.default_function_key}"
  scope        = databricks_secret_scope.support_utils_function.id
}