# Get current Azure context
data "azurerm_client_config" "current" {}

# Generate random suffix for globally unique resource names
resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

# Local values for common configurations
locals {
  # Naming convention: {service}-{project}-{environment}-{suffix}
  name_prefix = "${var.project_name}-${var.environment}"

  # Resource group name with override capability
  resource_group_name = var.resource_group_name != "" ? var.resource_group_name : "rg-${local.name_prefix}"

  # Common tags applied to all resources
  common_tags = merge(var.tags, {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "terraform"
    CreatedBy   = "teams-transcription-bot"
    CostCenter  = "IT-Operations"
    DeployedAt  = timestamp()
  })

  # Cost estimation (approximate monthly USD)
  cost_estimates = {
    app_service = var.environment == "prod" ? (
      var.app_service_sku == "P1v2" ? 81.00 :
      var.app_service_sku == "B2" ? 52.00 : 13.00
    ) : 13.00

    cognitive_services = var.speech_service_sku == "F0" ? 0.00 : 50.00

    storage = var.storage_account_replication_type == "GRS" ? 0.04 : 0.02

    key_vault = 0.03

    monitoring = 5.00

    total = (
      (var.environment == "prod" ? (
        var.app_service_sku == "P1v2" ? 81.00 :
        var.app_service_sku == "B2" ? 52.00 : 13.00
      ) : 13.00) +
      (var.speech_service_sku == "F0" ? 0.00 : 50.00) +
      (var.storage_account_replication_type == "GRS" ? 0.04 : 0.02) +
      0.03 + 5.00
    )
  }
}

# Main resource group
resource "azurerm_resource_group" "main" {
  name     = local.resource_group_name
  location = var.location
  tags     = local.common_tags

  lifecycle {
    ignore_changes = [tags["DeployedAt"]]
  }
}

# Storage Account for Terraform state and application data
module "storage" {
  source = "./modules/storage"

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  name_prefix         = local.name_prefix
  random_suffix       = random_string.suffix.result
  environment         = var.environment

  storage_tier             = var.storage_account_tier
  storage_replication_type = var.storage_account_replication_type
  enable_private_endpoints = var.enable_private_endpoints
  allowed_ip_ranges        = var.allowed_ip_ranges

  tags = local.common_tags
}

# Key Vault for secrets management
module "key_vault" {
  source = "./modules/key_vault"

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  name_prefix         = local.name_prefix
  random_suffix       = random_string.suffix.result
  environment         = var.environment

  tenant_id                = data.azurerm_client_config.current.tenant_id
  enable_private_endpoints = var.enable_private_endpoints
  allowed_ip_ranges        = var.allowed_ip_ranges

  # Store sensitive configuration
  secrets = {
    "bot-app-id"          = var.bot_app_id
    "bot-app-password"    = var.bot_app_password
    "azure-client-id"     = var.azure_client_id
    "azure-client-secret" = var.azure_client_secret
    "azure-tenant-id"     = var.azure_tenant_id
  }

  tags = local.common_tags
}

# Use existing Cognitive Services for Speech-to-Text
data "azurerm_cognitive_account" "existing_speech" {
  name                = "cog-demo-aab"
  resource_group_name = "rg-et-td-ta-ragpoc-cb"
}

# Store existing Cognitive Services keys in Key Vault
resource "azurerm_key_vault_secret" "speech_key" {
  name         = "azure-speech-key"
  value        = data.azurerm_cognitive_account.existing_speech.primary_access_key
  key_vault_id = module.key_vault.key_vault_id

  tags = local.common_tags

  depends_on = [module.key_vault]
}

resource "azurerm_key_vault_secret" "speech_endpoint" {
  name         = "azure-speech-endpoint"
  value        = data.azurerm_cognitive_account.existing_speech.endpoint
  key_vault_id = module.key_vault.key_vault_id

  tags = local.common_tags

  depends_on = [module.key_vault]
}

# Monitoring and observability (created first to avoid circular dependency)
module "monitoring" {
  source = "./modules/monitoring"

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  name_prefix         = local.name_prefix
  random_suffix       = random_string.suffix.result
  environment         = var.environment

  app_service_name = "${local.name_prefix}-${random_string.suffix.result}-app"
  key_vault_id     = module.key_vault.key_vault_id

  enable_action_groups = false # Disabled for simplified deployment

  tags = local.common_tags

  depends_on = [module.key_vault]
}

# App Service for hosting the bot application
module "app_service" {
  source = "./modules/app_service"

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  name_prefix         = local.name_prefix
  random_suffix       = random_string.suffix.result
  environment         = var.environment

  sku_name                 = var.app_service_sku
  key_vault_id             = module.key_vault.key_vault_id
  storage_account_name     = module.storage.storage_account_name
  application_insights_key = module.monitoring.instrumentation_key

  tags = local.common_tags

  depends_on = [
    module.key_vault,
    module.storage,
    module.monitoring
  ]
}

# Bot Service registration
module "bot_service" {
  source = "./modules/bot_service"

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  name_prefix         = local.name_prefix
  environment         = var.environment

  bot_app_id         = var.bot_app_id
  bot_app_password   = var.bot_app_password
  messaging_endpoint = "https://${module.app_service.app_service_hostname}/api/messages"

  tags = local.common_tags

  depends_on = [module.app_service]
}

# Grant Key Vault access to App Service managed identity
resource "azurerm_key_vault_access_policy" "app_service" {
  key_vault_id = module.key_vault.key_vault_id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = module.app_service.app_service_identity_principal_id

  secret_permissions = [
    "Get",
    "List"
  ]

  depends_on = [
    module.key_vault,
    module.app_service
  ]
}

# Grant Storage access to App Service managed identity
resource "azurerm_role_assignment" "app_service_storage" {
  scope                = module.storage.storage_account_id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = module.app_service.app_service_identity_principal_id

  depends_on = [
    module.storage,
    module.app_service
  ]
}

# Grant Cognitive Services access to App Service managed identity
resource "azurerm_role_assignment" "app_service_cognitive_services" {
  scope                = data.azurerm_cognitive_account.existing_speech.id
  role_definition_name = "Cognitive Services User"
  principal_id         = module.app_service.app_service_identity_principal_id

  depends_on = [
    module.app_service
  ]
}

# Azure AD App Registration with Graph API permissions
module "azure_ad" {
  source = "./modules/azure_ad"

  bot_app_id = var.bot_app_id
}