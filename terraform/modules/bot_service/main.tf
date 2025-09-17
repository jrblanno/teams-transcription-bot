# Local configuration values
locals {
  bot_service_name = "${var.name_prefix}-${var.environment}-bot"
  display_name     = var.display_name != "" ? var.display_name : "Teams Transcription Bot (${title(var.environment)})"
}

# Azure Bot Service (new resource type that supports single tenant)
resource "azurerm_bot_service_azure_bot" "main" {
  name                = local.bot_service_name
  location            = "global"  # Bot service is always global
  resource_group_name = var.resource_group_name
  sku                 = var.sku

  # Bot identity and authentication
  microsoft_app_id       = var.bot_app_id
  microsoft_app_type     = "SingleTenant"
  microsoft_app_tenant_id = data.azurerm_client_config.current.tenant_id

  # Bot metadata
  display_name = local.display_name
  endpoint     = var.messaging_endpoint

  # Streaming endpoint (if enabled)
  streaming_endpoint_enabled = var.streaming_endpoint_enabled

  # Developer insights configuration - simplified for now
  # Note: Will be configured post-deployment if needed

  tags = merge(var.tags, {
    Component   = "BotService"
    Environment = var.environment
    SKU         = var.sku
  })

  lifecycle {
    # Prevent changes to app registration details that might break the bot
    ignore_changes = [
      microsoft_app_id,
      microsoft_app_tenant_id,
    ]
  }
}

# Microsoft Teams Channel (primary channel for this bot)
resource "azurerm_bot_channel_ms_teams" "main" {
  count               = var.enable_teams_channel ? 1 : 0
  bot_name            = azurerm_bot_service_azure_bot.main.name
  location            = azurerm_bot_service_azure_bot.main.location
  resource_group_name = var.resource_group_name

  # Teams-specific configuration
  calling_web_hook = null  # Will be configured if calling features are needed
  enable_calling   = false # Not needed for meeting transcription

  # Note: deployment_environment is not a valid argument for azurerm_bot_channel_ms_teams

  depends_on = [azurerm_bot_service_azure_bot.main]
}

# Web Chat Channel (for testing and web integration)
resource "azurerm_bot_channel_web_chat" "main" {
  count               = var.enable_webchat_channel ? 1 : 0
  bot_name            = azurerm_bot_service_azure_bot.main.name
  location            = azurerm_bot_service_azure_bot.main.location
  resource_group_name = var.resource_group_name

  # Web Chat sites (default site is automatically created)
  site_names = ["Default Web Chat Site"]

  depends_on = [azurerm_bot_service_azure_bot.main]
}

# Direct Line Channel (for custom integrations if needed)
resource "azurerm_bot_channel_directline" "main" {
  count               = var.enable_directline_channel ? 1 : 0
  bot_name            = azurerm_bot_service_azure_bot.main.name
  location            = azurerm_bot_service_azure_bot.main.location
  resource_group_name = var.resource_group_name

  # Direct Line sites configuration
  dynamic "site" {
    for_each = var.directline_sites
    content {
      name                            = site.value.name
      enabled                         = site.value.enabled
      v1_allowed                      = site.value.v1_allowed
      v3_allowed                      = site.value.v3_allowed
      enhanced_authentication_enabled = site.value.enhanced_authentication_enabled
      trusted_origins                 = site.value.trusted_origins
    }
  }

  depends_on = [azurerm_bot_service_azure_bot.main]
}

# Bot Service Connection (if needed for Azure resources integration)
resource "azurerm_bot_connection" "main" {
  count               = 0 # Disabled for now, enable if OAuth connections are needed
  name                = "${local.bot_service_name}-connection"
  bot_name            = azurerm_bot_service_azure_bot.main.name
  location            = azurerm_bot_service_azure_bot.main.location
  resource_group_name = var.resource_group_name

  service_provider_name = "Azure Active Directory v2"
  client_id             = var.bot_app_id
  client_secret         = var.bot_app_password

  # Scopes for the connection (adjust based on requirements)
  scopes = "openid profile User.Read"

  # Parameters specific to Azure AD v2
  parameters = {
    "tenantId" = data.azurerm_client_config.current.tenant_id
  }

  depends_on = [azurerm_bot_service_azure_bot.main]
}

# Get current Azure client configuration
data "azurerm_client_config" "current" {}

# Note: Diagnostic settings will be configured separately to avoid validation issues