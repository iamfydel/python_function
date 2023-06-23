data "azuread_group" "anchor_rbac" {
  for_each     = var.anchor_rbac_aad_groups
  display_name = each.value
}