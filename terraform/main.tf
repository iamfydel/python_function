module "global" {
  source         = "git::https://dev.azure.com/anchor-it/anchor-platform/_git/platform-terraform-modules//global"
  platform_scope = var.platform_scope
  resource_scope = var.resource_scope
  scope_name     = var.scope_name
  domain         = var.domain
  service        = var.service
  region         = var.region
  resource_tags  = var.resource_tags
}

resource "azurerm_resource_group" "default" {
  name     = module.global.resource_names.resource_group
  location = module.global.region

  tags = merge(
    module.global.resource_tags,
    {}
  )
}
