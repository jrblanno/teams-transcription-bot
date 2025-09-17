output "key_vault_id" {
  description = "ID of the Key Vault"
  value       = azurerm_key_vault.main.id
}

output "key_vault_name" {
  description = "Name of the Key Vault"
  value       = azurerm_key_vault.main.name
}

output "key_vault_uri" {
  description = "URI of the Key Vault"
  value       = azurerm_key_vault.main.vault_uri
}

output "key_vault_tenant_id" {
  description = "Tenant ID of the Key Vault"
  value       = azurerm_key_vault.main.tenant_id
}

output "key_vault_resource_group_name" {
  description = "Resource group name of the Key Vault"
  value       = azurerm_key_vault.main.resource_group_name
}

output "key_vault_location" {
  description = "Location of the Key Vault"
  value       = azurerm_key_vault.main.location
}

# Secret information (keys only, not values for security)
output "secret_names" {
  description = "List of secret names stored in the Key Vault"
  value       = [for secret in azurerm_key_vault_secret.secrets : secret.name]
}

output "secret_ids" {
  description = "Map of secret names to their IDs"
  value = {
    for secret in azurerm_key_vault_secret.secrets : secret.name => secret.id
  }
  sensitive = true
}

output "secret_versions" {
  description = "Map of secret names to their current versions"
  value = {
    for secret in azurerm_key_vault_secret.secrets : secret.name => secret.version
  }
  sensitive = true
}

# Private endpoint information (if enabled)
output "private_endpoint_id" {
  description = "ID of the private endpoint (if enabled)"
  value       = var.enable_private_endpoints ? azurerm_private_endpoint.key_vault[0].id : null
}

output "private_endpoint_ip" {
  description = "Private IP address of the Key Vault endpoint (if enabled)"
  value       = var.enable_private_endpoints ? azurerm_private_endpoint.key_vault[0].private_service_connection[0].private_ip_address : null
}

# Access policy information
output "terraform_access_policy_id" {
  description = "ID of the Terraform access policy"
  value       = azurerm_key_vault_access_policy.terraform.id
}

# Note: Diagnostic settings will be configured separately to avoid circular dependencies

# References for use in app configuration
output "key_vault_references" {
  description = "Key Vault references for use in App Service configuration"
  value = {
    for secret in azurerm_key_vault_secret.secrets : secret.name => "@Microsoft.KeyVault(VaultName=${azurerm_key_vault.main.name};SecretName=${secret.name})"
  }
  sensitive = true
}