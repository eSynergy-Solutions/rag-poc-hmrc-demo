# infrastructure/terraform/variables.tf

# Resource group for all resources
variable "resource_group_name" {
  description = "The name of the resource group."
  type        = string
}

# Location for resource group and resources
variable "location" {
  description = "Azure region for resources."
  type        = string
  default     = "East US"
}

# VNet module inputs
variable "vnet_address_space" {
  description = "Address space for the virtual network."
  type        = list(string)
  default     = ["10.0.0.0/16"]
}

variable "subnet_prefixes" {
  description = "List of subnet prefixes within the VNet."
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

# Key Vault module inputs
variable "keyvault_name" {
  description = "Name of the Azure Key Vault."
  type        = string
}

# Database module inputs
variable "db_server_name" {
  description = "Name of the Azure database server."
  type        = string
}
variable "db_sku" {
  description = "SKU for the Azure database."
  type        = string
  default     = "GP_Gen5_2"
}

# Container Apps module inputs
variable "containerapp_env_name" {
  description = "Name of the Container Apps environment."
  type        = string
}
variable "containerapp_name" {
  description = "Name of the Container App."
  type        = string
}
variable "containerapp_image" {
  description = "Container image for deployment."
  type        = string
}
