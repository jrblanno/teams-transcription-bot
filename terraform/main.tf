# Teams Transcription Bot - Simplified POC Infrastructure
# Single file for all essential resources

terraform {
  required_version = ">= 1.12"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.44.0"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 3.5.0"
    }
  }
}

# Configure providers
provider "azurerm" {
  features {}
  subscription_id = "97ad187d-8816-4f26-acd8-931a767071f0"  # Required in v4
  # Let Azure automatically register required resource providers
}

provider "azuread" {}

# =============================================================================
# VARIABLES
# =============================================================================

variable "project_name" {
  type    = string
  default = "teamsbot"
}

variable "environment" {
  type    = string
  default = "poc"
}

variable "location" {
  type    = string
  default = "westeurope"
}

variable "bot_app_id" {
  type        = string
  description = "The Application ID of the Azure Bot"
  sensitive   = true
}

variable "bot_app_password" {
  type        = string
  description = "The Application Password/Secret for the Azure Bot"
  sensitive   = true
}

# =============================================================================
# DATA SOURCES - EXISTING RESOURCES
# =============================================================================

data "azurerm_client_config" "current" {}

# Create Azure Speech Service for transcription
resource "azurerm_cognitive_account" "speech_service" {
  name                = "${var.project_name}-speech"
  location            = var.location
  resource_group_name = azurerm_resource_group.main.name
  kind                = "SpeechServices"
  sku_name            = "F0"  # Free tier

  tags = azurerm_resource_group.main.tags
}

# =============================================================================
# STORAGE ACCOUNT - Transcript storage
# =============================================================================

resource "azurerm_storage_account" "transcripts" {
  name                     = "${var.project_name}${var.environment}storage"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"

  # Enable blob features for transcript management
  blob_properties {
    versioning_enabled = true
    delete_retention_policy {
      days = 30
    }
    change_feed_enabled = true
  }

  tags = azurerm_resource_group.main.tags
}

# Blob container for storing transcripts
resource "azurerm_storage_container" "transcripts" {
  name                  = "transcripts"
  storage_account_name  = azurerm_storage_account.transcripts.name
  container_access_type = "private"
}

# Data source for Microsoft Graph (for permissions)
data "azuread_application_published_app_ids" "well_known" {}

data "azuread_service_principal" "msgraph" {
  client_id = data.azuread_application_published_app_ids.well_known.result.MicrosoftGraph
}

# Get existing app registration
data "azuread_application" "teams_bot" {
  client_id = var.bot_app_id  # Updated from application_id (deprecated)
}

# =============================================================================
# RESOURCE GROUP
# =============================================================================

resource "azurerm_resource_group" "main" {
  name     = "rg-${var.project_name}-${var.environment}"
  location = var.location

  tags = {
    Project     = var.project_name
    Environment = var.environment
    Purpose     = "Teams Transcription Bot POC"
  }
}

# =============================================================================
# KEY VAULT - Store secrets
# =============================================================================

resource "azurerm_key_vault" "main" {
  name                = "${var.project_name}${var.environment}kv"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"

  # Use RBAC for access control (best practice)
  enable_rbac_authorization = true

  tags = azurerm_resource_group.main.tags
}

# Store bot credentials in Key Vault
resource "azurerm_key_vault_secret" "bot_app_id" {
  name         = "bot-app-id"
  value        = var.bot_app_id
  key_vault_id = azurerm_key_vault.main.id
}

resource "azurerm_key_vault_secret" "bot_app_password" {
  name         = "bot-app-password"
  value        = var.bot_app_password
  key_vault_id = azurerm_key_vault.main.id
}

# Store Speech Service keys in Key Vault
resource "azurerm_key_vault_secret" "speech_key" {
  name         = "azure-speech-key"
  value        = azurerm_cognitive_account.speech_service.primary_access_key
  key_vault_id = azurerm_key_vault.main.id
}

resource "azurerm_key_vault_secret" "speech_endpoint" {
  name         = "azure-speech-endpoint"
  value        = azurerm_cognitive_account.speech_service.endpoint
  key_vault_id = azurerm_key_vault.main.id
}

resource "azurerm_key_vault_secret" "speech_region" {
  name         = "azure-speech-region"
  value        = "swedencentral"  # The existing service is in Sweden Central
  key_vault_id = azurerm_key_vault.main.id
}

# =============================================================================
# APP SERVICE - Host the bot
# =============================================================================

# App Service Plan
resource "azurerm_service_plan" "main" {
  name                = "${var.project_name}-${var.environment}-plan"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  os_type             = "Linux"
  sku_name            = "B1"  # Basic tier for POC

  tags = azurerm_resource_group.main.tags
}

# App Service (Web App)
resource "azurerm_linux_web_app" "main" {
  name                = "${var.project_name}-${var.environment}-app"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  service_plan_id     = azurerm_service_plan.main.id

  https_only = true

  # Managed Identity for secure access to resources
  identity {
    type = "SystemAssigned"
  }

  site_config {
    always_on        = false  # B1 doesn't support always on
    ftps_state       = "Disabled"
    http2_enabled    = true
    minimum_tls_version = "1.2"

    # Python runtime
    application_stack {
      python_version = "3.11"
    }

    # CORS for Bot Framework
    cors {
      allowed_origins = [
        "https://botframework.com",
        "https://chatbot.botframework.com"
      ]
    }
  }

  # App Settings
  app_settings = {
    # Bot Framework settings
    "BOT_APP_ID"       = "@Microsoft.KeyVault(VaultName=${azurerm_key_vault.main.name};SecretName=bot-app-id)"
    "BOT_APP_PASSWORD" = "@Microsoft.KeyVault(VaultName=${azurerm_key_vault.main.name};SecretName=bot-app-password)"

    # Azure Speech settings
    "AZURE_SPEECH_KEY"      = "@Microsoft.KeyVault(VaultName=${azurerm_key_vault.main.name};SecretName=azure-speech-key)"
    "AZURE_SPEECH_ENDPOINT" = "@Microsoft.KeyVault(VaultName=${azurerm_key_vault.main.name};SecretName=azure-speech-endpoint)"
    "AZURE_SPEECH_REGION"   = "@Microsoft.KeyVault(VaultName=${azurerm_key_vault.main.name};SecretName=azure-speech-region)"

    # Azure Storage settings
    "AZURE_STORAGE_ACCOUNT_NAME"   = azurerm_storage_account.transcripts.name
    "AZURE_STORAGE_CONTAINER_NAME" = azurerm_storage_container.transcripts.name

    # Python settings
    "PYTHONPATH"                     = "/home/site/wwwroot"
    "SCM_DO_BUILD_DURING_DEPLOYMENT" = "1"
    "ENABLE_ORYX_BUILD"              = "true"
  }

  tags = azurerm_resource_group.main.tags
}

# Grant App Service access to Key Vault secrets using RBAC
resource "azurerm_role_assignment" "app_service_keyvault_reader" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_linux_web_app.main.identity[0].principal_id

  depends_on = [azurerm_linux_web_app.main]
}

# Grant current user (Terraform) access to manage Key Vault secrets
resource "azurerm_role_assignment" "current_user_keyvault_admin" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Administrator"
  principal_id         = data.azurerm_client_config.current.object_id
}

# Grant App Service access to Cognitive Services
resource "azurerm_role_assignment" "app_service_cognitive" {
  scope                = azurerm_cognitive_account.speech_service.id
  role_definition_name = "Cognitive Services User"
  principal_id         = azurerm_linux_web_app.main.identity[0].principal_id

  depends_on = [azurerm_linux_web_app.main]
}

# Grant App Service access to Storage Account
resource "azurerm_role_assignment" "app_service_storage" {
  scope                = azurerm_storage_account.transcripts.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_linux_web_app.main.identity[0].principal_id

  depends_on = [azurerm_linux_web_app.main]
}

# =============================================================================
# BOT SERVICE - Teams bot registration
# =============================================================================

resource "azurerm_bot_service_azure_bot" "main" {
  name                = "${var.project_name}-${var.environment}-bot"
  location            = "global"  # Bot service is always global
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "F0"  # Free tier for POC

  microsoft_app_id        = var.bot_app_id
  microsoft_app_type      = "SingleTenant"
  microsoft_app_tenant_id = data.azurerm_client_config.current.tenant_id

  display_name = "Teams Transcription Bot (${upper(var.environment)})"
  endpoint     = "https://${azurerm_linux_web_app.main.default_hostname}/api/messages"

  tags = azurerm_resource_group.main.tags

  depends_on = [azurerm_linux_web_app.main]
}

# Teams Channel
resource "azurerm_bot_channel_ms_teams" "main" {
  bot_name            = azurerm_bot_service_azure_bot.main.name
  location            = azurerm_bot_service_azure_bot.main.location
  resource_group_name = azurerm_resource_group.main.name

  depends_on = [azurerm_bot_service_azure_bot.main]
}

# =============================================================================
# AZURE AD - Bot App Permissions (Graph API)
# =============================================================================

# Create service principal for the bot application
resource "azuread_service_principal" "teams_bot" {
  client_id                    = var.bot_app_id
  app_role_assignment_required = false

  tags = ["Teams", "Bot", "Transcription", "POC"]
}

# Configure Graph API permissions
resource "azuread_application_api_access" "msgraph_permissions" {
  application_id = data.azuread_application.teams_bot.id
  api_client_id  = data.azuread_application_published_app_ids.well_known.result["MicrosoftGraph"]

  # Application permissions for Teams bot
  role_ids = [
    data.azuread_service_principal.msgraph.app_role_ids["Calls.AccessMedia.All"],
    data.azuread_service_principal.msgraph.app_role_ids["Calls.JoinGroupCall.All"],
    data.azuread_service_principal.msgraph.app_role_ids["Calls.InitiateGroupCall.All"],
    data.azuread_service_principal.msgraph.app_role_ids["OnlineMeetings.ReadWrite.All"]
  ]
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "resource_group_name" {
  value = azurerm_resource_group.main.name
}

output "app_service_url" {
  value = "https://${azurerm_linux_web_app.main.default_hostname}"
}

output "bot_endpoint" {
  value = "https://${azurerm_linux_web_app.main.default_hostname}/api/messages"
}

output "key_vault_name" {
  value = azurerm_key_vault.main.name
}

output "bot_service_name" {
  value = azurerm_bot_service_azure_bot.main.name
}

output "speech_service_endpoint" {
  value = azurerm_cognitive_account.speech_service.endpoint
}

output "admin_consent_url" {
  value = "https://login.microsoftonline.com/${data.azurerm_client_config.current.tenant_id}/adminconsent?client_id=${var.bot_app_id}"
  description = "URL to grant admin consent for Graph API permissions"
  sensitive   = true
}

output "storage_account_name" {
  value = azurerm_storage_account.transcripts.name
  description = "Azure Storage Account name for transcripts"
}

output "storage_container_name" {
  value = azurerm_storage_container.transcripts.name
  description = "Azure Storage Container name for transcripts"
}