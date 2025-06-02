# infrastructure/terraform/modules/db/main.tf

variable "resource_group_name" {
  description = "Name of the resource group."
  type        = string
}

variable "location" {
  description = "Azure region."
  type        = string
}

variable "db_server_name" {
  description = "Name of the Azure SQL server."
  type        = string
}

variable "db_sku" {
  description = "SKU for the Azure SQL server."
  type        = string
}

# Create Azure SQL server
resource "azurerm_mssql_server" "this" {
  name                         = var.db_server_name
  resource_group_name          = var.resource_group_name
  location                     = var.location
  version                      = "12.0"
  administrator_login          = "sqladminuser"
  administrator_login_password = random_password.pw.result

  sku_name = var.db_sku

  tags = {
    environment = "production"
  }
}

# Generate a random password for the admin if not provided
resource "random_password" "pw" {
  length  = 16
  special = true
}

# Example: Create a sample database within the server
resource "azurerm_mssql_database" "this" {
  name           = "${var.db_server_name}-db"
  server_id      = azurerm_mssql_server.this.id
  sku_name       = "Basic"
  collation      = "SQL_Latin1_General_CP1_CI_AS"
  creation_source = "Default"
}

# Output server FQDN
output "server_fqdn" {
  value = azurerm_mssql_server.this.fully_qualified_domain_name
}
