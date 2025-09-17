# Generate Cognitive Services account name
locals {
  cognitive_services_name = "${var.name_prefix}-${var.random_suffix}-speech"

  # Custom subdomain name (required for private endpoints)
  custom_subdomain = var.custom_subdomain_name != "" ? var.custom_subdomain_name : "${var.name_prefix}-${var.random_suffix}-speech"
}

# Azure Cognitive Services Account for Speech-to-Text
resource "azurerm_cognitive_account" "speech" {
  name                = local.cognitive_services_name
  location            = var.location
  resource_group_name = var.resource_group_name
  kind                = var.kind
  sku_name            = var.sku_name

  # Custom subdomain for API access
  custom_subdomain_name = local.custom_subdomain

  # Security and access settings
  local_auth_enabled                 = var.local_auth_enabled
  dynamic_throttling_enabled         = var.dynamic_throttling_enabled
  outbound_network_access_restricted = var.outbound_network_access_restricted

  # Public network access
  public_network_access_enabled = true

  # Network access control - simplified, allow all
  # Can be configured later if needed

  # Note: Customer managed encryption key can be added later if needed for compliance
  # This would require additional Key Vault setup and proper key management

  tags = merge(var.tags, {
    Service = "Speech-to-Text"
    Kind    = var.kind
  })

}

# Store Cognitive Services primary key in Key Vault
resource "azurerm_key_vault_secret" "speech_primary_key" {
  name         = "azure-speech-key"
  value        = azurerm_cognitive_account.speech.primary_access_key
  key_vault_id = var.key_vault_id

  content_type = "application/x-api-key"

  tags = merge(var.tags, {
    Service     = "Speech-to-Text"
    KeyType     = "Primary"
    GeneratedBy = "terraform"
  })
}

# Store Cognitive Services secondary key in Key Vault (for key rotation)
resource "azurerm_key_vault_secret" "speech_secondary_key" {
  name         = "azure-speech-key-secondary"
  value        = azurerm_cognitive_account.speech.secondary_access_key
  key_vault_id = var.key_vault_id

  content_type = "application/x-api-key"

  tags = merge(var.tags, {
    Service     = "Speech-to-Text"
    KeyType     = "Secondary"
    GeneratedBy = "terraform"
  })
}

# Store Cognitive Services region in Key Vault
resource "azurerm_key_vault_secret" "speech_region" {
  name         = "azure-speech-region"
  value        = var.location
  key_vault_id = var.key_vault_id

  content_type = "text/plain"

  tags = merge(var.tags, {
    Service     = "Speech-to-Text"
    Type        = "Configuration"
    GeneratedBy = "terraform"
  })
}

# Store Cognitive Services endpoint in Key Vault
resource "azurerm_key_vault_secret" "speech_endpoint" {
  name         = "azure-speech-endpoint"
  value        = azurerm_cognitive_account.speech.endpoint
  key_vault_id = var.key_vault_id

  content_type = "text/uri"

  tags = merge(var.tags, {
    Service     = "Speech-to-Text"
    Type        = "Endpoint"
    GeneratedBy = "terraform"
  })
}

# Private endpoints removed for simplicity
# Note: Diagnostic settings will be configured separately to avoid validation issues