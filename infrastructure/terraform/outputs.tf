# infrastructure/terraform/outputs.tf

# Resource Group
output "resource_group_name" {
  description = "The name of the resource group created/used."
  value       = var.resource_group_name
}

# Virtual Network
output "vnet_id" {
  description = "The ID of the Azure Virtual Network."
  value       = module.vnet.vnet_id
}

# Key Vault
output "keyvault_uri" {
  description = "The URI of the Azure Key Vault."
  value       = module.keyvault.vault_uri
}

# Database Server
output "db_server_fqdn" {
  description = "Fully qualified domain name of the database server."
  value       = module.db.server_fqdn
}

# Container Apps Environment
output "containerapp_env_id" {
  description = "The ID of the Container Apps environment."
  value       = module.containerapps.environment_id
}

# Container App
output "containerapp_url" {
  description = "The default URL of the deployed Container App."
  value       = module.containerapps.app_url
}
