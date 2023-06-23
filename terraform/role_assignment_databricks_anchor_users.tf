# // Databricks Internal Role Assignment//
resource "databricks_secret_acl" "secret_usage_dev" {
  count = var.scope_name == "d01" ? 1 : 0

  principal  = var.databricks_internal_group_name
  permission = "READ"
  scope      = databricks_secret_scope.support_utils_function.name
}
