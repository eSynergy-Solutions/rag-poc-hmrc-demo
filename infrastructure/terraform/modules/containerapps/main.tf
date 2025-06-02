# infrastructure/terraform/modules/containerapps/main.tf

variable "resource_group_name" {
  description = "Name of the resource group."
  type        = string
}

variable "location" {
  description = "Azure region."
  type        = string
}

variable "containerapp_env_name" {
  description = "Name of the Container Apps environment."
  type        = string
}

variable "containerapp_name" {
  description = "Name of the Container App."
  type        = string
}

variable "containerapp_image" {
  description = "Container image to deploy."
  type        = string
}

# Log analytics workspace (needed for Container Apps environment)
resource "azurerm_log_analytics_workspace" "this" {
  name                = "${var.resource_group_name}-logs"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

# Container Apps environment
resource "azurerm_container_app_environment" "this" {
  name                = var.containerapp_env_name
  location            = var.location
  resource_group_name = var.resource_group_name

  app_logs {
    destination = "log-analytics"
    log_analytics {
      workspace_id = azurerm_log_analytics_workspace.this.id
    }
  }
}

# Container App
resource "azurerm_container_app" "this" {
  name                       = var.containerapp_name
  container_app_environment_id = azurerm_container_app_environment.this.id
  resource_group_name        = var.resource_group_name
  location                   = var.location

  configuration {
    ingress {
      external_enabled = true
      target_port      = 8000
    }
  }

  template {
    container {
      name   = var.containerapp_name
      image  = var.containerapp_image
      cpu    = 0.25
      memory = "0.5Gi"
      env {
        name  = "AZURE_OPENAI_ENDPOINT"
        value = "" # TODO: set via environment or secret
      }
      # additional env vars can be added similarly
    }
    scale {
      min_replicas = 1
      max_replicas = 3
    }
  }
}

# Outputs
output "environment_id" {
  value = azurerm_container_app_environment.this.id
}

output "app_url" {
  value = azurerm_container_app.this.configuration[0].ingress[0].fqdn
}
