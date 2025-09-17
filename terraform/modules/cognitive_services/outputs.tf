output "cognitive_services_id" {
  description = "ID of the Cognitive Services account"
  value       = azurerm_cognitive_account.speech.id
}

output "cognitive_services_name" {
  description = "Name of the Cognitive Services account"
  value       = azurerm_cognitive_account.speech.name
}

output "endpoint" {
  description = "Endpoint URL of the Cognitive Services account"
  value       = azurerm_cognitive_account.speech.endpoint
}

output "location" {
  description = "Location/region of the Cognitive Services account"
  value       = azurerm_cognitive_account.speech.location
}

output "kind" {
  description = "Kind of the Cognitive Services account"
  value       = azurerm_cognitive_account.speech.kind
}

output "sku_name" {
  description = "SKU name of the Cognitive Services account"
  value       = azurerm_cognitive_account.speech.sku_name
}

# Sensitive outputs for access keys
output "primary_access_key" {
  description = "Primary access key for the Cognitive Services account"
  value       = azurerm_cognitive_account.speech.primary_access_key
  sensitive   = true
}

output "secondary_access_key" {
  description = "Secondary access key for the Cognitive Services account"
  value       = azurerm_cognitive_account.speech.secondary_access_key
  sensitive   = true
}

# Key Vault secret references
output "primary_key_secret_id" {
  description = "ID of the primary key secret in Key Vault"
  value       = azurerm_key_vault_secret.speech_primary_key.id
  sensitive   = true
}

output "secondary_key_secret_id" {
  description = "ID of the secondary key secret in Key Vault"
  value       = azurerm_key_vault_secret.speech_secondary_key.id
  sensitive   = true
}

output "region_secret_id" {
  description = "ID of the region secret in Key Vault"
  value       = azurerm_key_vault_secret.speech_region.id
}

output "endpoint_secret_id" {
  description = "ID of the endpoint secret in Key Vault"
  value       = azurerm_key_vault_secret.speech_endpoint.id
}

# Key Vault references for App Service configuration
output "key_vault_references" {
  description = "Key Vault references for use in App Service configuration"
  value = {
    AZURE_SPEECH_KEY      = "@Microsoft.KeyVault(VaultName=${split("/", var.key_vault_id)[8]};SecretName=azure-speech-key)"
    AZURE_SPEECH_REGION   = "@Microsoft.KeyVault(VaultName=${split("/", var.key_vault_id)[8]};SecretName=azure-speech-region)"
    AZURE_SPEECH_ENDPOINT = "@Microsoft.KeyVault(VaultName=${split("/", var.key_vault_id)[8]};SecretName=azure-speech-endpoint)"
  }
  sensitive = true
}

# Private endpoint information (if enabled)
output "private_endpoint_id" {
  description = "ID of the private endpoint (if enabled)"
  value       = var.enable_private_endpoints ? azurerm_private_endpoint.speech[0].id : null
}

output "private_endpoint_ip" {
  description = "Private IP address of the Cognitive Services endpoint (if enabled)"
  value       = var.enable_private_endpoints ? azurerm_private_endpoint.speech[0].private_service_connection[0].private_ip_address : null
}

# Custom subdomain for private endpoint access
output "custom_subdomain_name" {
  description = "Custom subdomain name of the Cognitive Services account"
  value       = azurerm_cognitive_account.speech.custom_subdomain_name
}

# Note: Diagnostic settings will be configured separately to avoid circular dependencies

# Configuration for Python application
output "speech_service_config" {
  description = "Configuration object for Speech Service integration"
  value = {
    name                     = azurerm_cognitive_account.speech.name
    location                 = azurerm_cognitive_account.speech.location
    endpoint                 = azurerm_cognitive_account.speech.endpoint
    custom_subdomain         = azurerm_cognitive_account.speech.custom_subdomain_name
    sku_name                 = azurerm_cognitive_account.speech.sku_name
    kind                     = azurerm_cognitive_account.speech.kind
    private_endpoint_enabled = var.enable_private_endpoints
  }
  sensitive = false
}