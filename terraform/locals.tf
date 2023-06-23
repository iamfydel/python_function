locals {
  principal_devops_engineer_object_id = data.azuread_group.anchor_rbac["AZGRP_RBAC_PrincipalDevopsEngineer"].object_id
  devops_engineer_object_id           = data.azuread_group.anchor_rbac["AZGRP_RBAC_DevOpsEngineer"].object_id
  principal_data_engineer_object_id   = data.azuread_group.anchor_rbac["AZGRP_RBAC_PrincipalDataEngineer"].object_id
  data_engineer_object_id             = data.azuread_group.anchor_rbac["AZGRP_RBAC_DataEngineer"].object_id
  qa_data_engineer_object_id          = data.azuread_group.anchor_rbac["AZGRP_RBAC_QADataEngineer"].object_id
}