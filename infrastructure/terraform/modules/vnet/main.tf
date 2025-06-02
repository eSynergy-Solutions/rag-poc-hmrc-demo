# infrastructure/terraform/modules/vnet/main.tf

variable "resource_group_name" {
  type = string
}

variable "location" {
  type = string
}

variable "vnet_address_space" {
  type = list(string)
}

variable "subnet_prefixes" {
  type = list(string)
}

resource "azurerm_virtual_network" "this" {
  name                = "${var.resource_group_name}-vnet"
  location            = var.location
  resource_group_name = var.resource_group_name
  address_space       = var.vnet_address_space
  dns_servers         = []
  tags = {
    environment = "production"
  }
}

resource "azurerm_subnet" "this" {
  for_each             = toset(var.subnet_prefixes)
  name                 = "${azurerm_virtual_network.this.name}-${replace(each.value, "/", "-")}"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.this.name
  address_prefixes     = [each.value]
}
