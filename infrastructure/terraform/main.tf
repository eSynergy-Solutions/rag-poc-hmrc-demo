terraform {
  required_version = ">= 1.4.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# Call modules (fill in source paths and inputs later)
module "vnet" {
  source = "./modules/vnet"
  # TODO: pass subnet ranges, address spaces, resource group
}

module "keyvault" {
  source = "./modules/keyvault"
  # TODO: pass name, resource group, access policies
}

module "db" {
  source = "./modules/db"
  # TODO: pass sku, capacity, resource group
}

module "containerapps" {
  source = "./modules/containerapps"
  # TODO: pass image tag, environment variables, resource group
}
