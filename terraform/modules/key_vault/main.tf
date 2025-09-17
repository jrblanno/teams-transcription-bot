# Get current Azure client configuration
data "azurerm_client_config" "current" {}

# Generate Key Vault name (must be globally unique and 3-24 chars)
locals {
  # Remove hyphens and ensure naming compliance for Key Vault
  key_vault_name = lower(substr(
    replace("${var.name_prefix}-${var.random_suffix}-kv", "--", "-"),
    0, 24
  ))
}

# Azure Key Vault for secure secrets management
resource "azurerm_key_vault" "main" {
  name                = local.key_vault_name
  location            = var.location
  resource_group_name = var.resource_group_name
  tenant_id           = var.tenant_id
  sku_name            = var.sku_name

  # Security and compliance settings - simplified
  enabled_for_deployment          = false
  enabled_for_disk_encryption     = false
  enabled_for_template_deployment = false
  enable_rbac_authorization       = false # Using access policies instead
  purge_protection_enabled        = false # Simplified for dev
  soft_delete_retention_days      = 7

  # Network access control - simplified to allow all
  public_network_access_enabled = true

  tags = var.tags

}

# Access policy for current service principal (Terraform)
resource "azurerm_key_vault_access_policy" "terraform" {
  key_vault_id = azurerm_key_vault.main.id
  tenant_id    = var.tenant_id
  object_id    = data.azurerm_client_config.current.object_id

  key_permissions = [
    "Get",
    "List",
    "Create",
    "Delete",
    "Update",
    "Recover",
    "Purge"
  ]

  secret_permissions = [
    "Get",
    "List",
    "Set",
    "Delete",
    "Recover",
    "Restore",
    "Purge"
  ]

  certificate_permissions = [
    "Get",
    "List",
    "Create",
    "Import",
    "Delete",
    "Update",
    "Recover",
    "Purge"
  ]
}

# Additional access policies from variables
resource "azurerm_key_vault_access_policy" "additional" {
  for_each = {
    for idx, policy in var.access_policies : idx => policy
  }

  key_vault_id = azurerm_key_vault.main.id
  tenant_id    = each.value.tenant_id
  object_id    = each.value.object_id

  key_permissions         = each.value.key_permissions
  secret_permissions      = each.value.secret_permissions
  certificate_permissions = each.value.certificate_permissions

  depends_on = [azurerm_key_vault.main]
}

# Store secrets in Key Vault using local variable to avoid sensitive for_each issue
locals {
  # Convert sensitive map to non-sensitive keys for iteration
  secret_keys = keys(var.secrets)
}

resource "azurerm_key_vault_secret" "secrets" {
  count = length(local.secret_keys)

  name         = local.secret_keys[count.index]
  value        = var.secrets[local.secret_keys[count.index]]
  key_vault_id = azurerm_key_vault.main.id

  # Content type for better organization
  content_type = "application/x-configuration"

  tags = merge(var.tags, {
    SecretType = "configuration"
    ManagedBy  = "terraform"
  })

  depends_on = [
    azurerm_key_vault_access_policy.terraform
  ]

  lifecycle {
    # Don't recreate secrets unnecessarily
    ignore_changes = [
      tags["CreatedDate"]
    ]
  }
}

# Private endpoint for Key Vault (if enabled)
resource "azurerm_private_endpoint" "key_vault" {
  count               = var.enable_private_endpoints ? 1 : 0
  name                = "${local.key_vault_name}-pe"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.subnet_id

  private_service_connection {
    name                           = "${local.key_vault_name}-psc"
    private_connection_resource_id = azurerm_key_vault.main.id
    subresource_names              = ["vault"]
    is_manual_connection           = false
  }

  tags = var.tags
}

# Note: Diagnostic settings will be configured later when monitoring module is available
# This avoids circular dependencies and validation issues