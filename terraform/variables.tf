###########################
# Global
###########################

variable "platform_scope" {
  type        = string
  description = "The target platform for the resource."
}

variable "resource_scope" {
  type        = string
  description = "The resource scope."
}

variable "scope_name" {
  type        = string
  description = "The full resource scope name, this will change based on the resource_scope input"
}

variable "domain" {
  type        = string
  description = "The business domain the resource is associated with."
}

variable "service" {
  type        = string
  description = "The service name within the domain."
}

variable "region" {
  type        = string
  description = "The Azure region full name."
}

variable "resource_tags" {
  type        = map(string)
  description = "Tag map with default values."
}

###########################
# Function app
##########################
variable "service_desk_base_url" {
  type        = string
  description = "service_desk_base_url for function app settings"
}

variable "service_desk_client_id" {
  type        = string
  description = "service_desk_client_id for function app settings"
}

variable "service_desk_username" {
  type        = string
  description = "service_desk_username for function app settings"
}

variable "service_desk_password" {
  type        = string
  description = "service_desk_password for function app settings"
}

variable "app_insights_ikey" {
  type        = string
  description = "Application insights instrumentation key"
}

variable "purview_account_name" {
  type        = string
  description = "Purview account name"
}

variable "env_core_infra_resource_group_name" {
  type        = string
  description = "Environment Core infra resource group name"
}

variable "adf_account_name" {
  type        = string
  description = "ADF account name"
}

variable "databricks_workspace_name" {
  type        = string
  description = "Databricks Workspace name"
}

variable "datalake_name" {
  type        = string
  description = "The name of the landing Data Lake"
}

variable "service_bus_connection" {
  type        = string
  description = "The connection string of the Service Bus"
}

variable "service_bus_topic" {
  type        = string
  description = "The topic name of the Service Bus"
}

###########################
# RBAC ROLE ASSIGNMENTS
###########################

variable "anchor_rbac_aad_groups" {
  type        = set(string)
  description = "Anchor RBAC AAD groups to data lookup"
  default = [
    "AZGRP_RBAC_PrincipalDevopsEngineer",
    "AZGRP_RBAC_DevOpsEngineer",
    "AZGRP_RBAC_PrincipalDataEngineer",
    "AZGRP_RBAC_DataEngineer",
    "AZGRP_RBAC_QADataEngineer"
  ]
}

variable "databricks_internal_group_name" {
  type        = string
  description = "The name of the internal group in databricks used to give DEng permissions"
}

###########################
# RBAC ROLE ASSIGNMENTS
###########################
variable "powerbi_tenant_id" {
  type        = string
  description = "The PowerBI tenant ID"
}

variable "powerbi_client_id" {
  type        = string
  description = "The PowerBI SPN's client id"
}

variable "powerbi_client_secret" {
  type        = string
  description = "The PowerBI SPN's client secret"
}
