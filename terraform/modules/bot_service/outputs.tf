output "bot_service_id" {
  description = "ID of the Bot Channels Registration"
  value       = azurerm_bot_service_azure_bot.main.id
}

output "bot_service_name" {
  description = "Name of the Bot Channels Registration"
  value       = azurerm_bot_service_azure_bot.main.name
}

output "bot_display_name" {
  description = "Display name of the bot"
  value       = azurerm_bot_service_azure_bot.main.display_name
}

output "messaging_endpoint" {
  description = "Messaging endpoint of the bot"
  value       = azurerm_bot_service_azure_bot.main.endpoint
}

output "microsoft_app_id" {
  description = "Microsoft App ID of the bot"
  value       = azurerm_bot_service_azure_bot.main.microsoft_app_id
  sensitive   = true
}

output "sku" {
  description = "SKU of the Bot Service"
  value       = azurerm_bot_service_azure_bot.main.sku
}

# Teams Channel Information
output "teams_channel_enabled" {
  description = "Whether Microsoft Teams channel is enabled"
  value       = var.enable_teams_channel
}

output "teams_channel_id" {
  description = "ID of the Microsoft Teams channel (if enabled)"
  value       = var.enable_teams_channel ? azurerm_bot_channel_ms_teams.main[0].id : null
}

# Web Chat Channel Information
output "webchat_channel_enabled" {
  description = "Whether Web Chat channel is enabled"
  value       = var.enable_webchat_channel
}

output "webchat_channel_id" {
  description = "ID of the Web Chat channel (if enabled)"
  value       = var.enable_webchat_channel ? azurerm_bot_channel_web_chat.main[0].id : null
}

# Direct Line Channel Information
output "directline_channel_enabled" {
  description = "Whether Direct Line channel is enabled"
  value       = var.enable_directline_channel
}

output "directline_channel_id" {
  description = "ID of the Direct Line channel (if enabled)"
  value       = var.enable_directline_channel ? azurerm_bot_channel_directline.main[0].id : null
}

# Bot Configuration for Application
output "bot_configuration" {
  description = "Bot configuration details for application use"
  value = {
    name               = azurerm_bot_service_azure_bot.main.name
    display_name       = azurerm_bot_service_azure_bot.main.display_name
    app_id             = azurerm_bot_service_azure_bot.main.microsoft_app_id
    messaging_endpoint = azurerm_bot_service_azure_bot.main.endpoint
    sku                = azurerm_bot_service_azure_bot.main.sku
    teams_enabled      = var.enable_teams_channel
    webchat_enabled    = var.enable_webchat_channel
  }
  sensitive = true
}

# Bot Channels Summary
output "enabled_channels" {
  description = "List of enabled channels"
  value = compact([
    var.enable_teams_channel ? "msteams" : "",
    var.enable_webchat_channel ? "webchat" : "",
    var.enable_directline_channel ? "directline" : ""
  ])
}

# Resource Group and Location
output "resource_group_name" {
  description = "Resource group name of the Bot Service"
  value       = azurerm_bot_service_azure_bot.main.resource_group_name
}

output "location" {
  description = "Location of the Bot Service"
  value       = azurerm_bot_service_azure_bot.main.location
}

# Security and Access Information
output "streaming_endpoint_enabled" {
  description = "Whether streaming endpoint is enabled"
  value       = azurerm_bot_service_azure_bot.main.streaming_endpoint_enabled
}

# Note: Diagnostic settings will be configured separately to avoid circular dependencies

# Bot Testing URLs
output "testing_urls" {
  description = "URLs for testing the bot in different channels"
  value = {
    webchat_test_url       = var.enable_webchat_channel ? "https://webchat.botframework.com/embed/${azurerm_bot_service_azure_bot.main.name}" : null
    bot_framework_test_url = "https://dev.botframework.com/bots/${azurerm_bot_service_azure_bot.main.microsoft_app_id}/test"
  }
  sensitive = true
}

# Integration Information
output "integration_info" {
  description = "Information needed for bot integration"
  value = {
    # For Microsoft Graph API integration
    app_id = var.bot_app_id

    # For App Service integration
    messaging_endpoint = var.messaging_endpoint

    # For monitoring and logging
    bot_name = azurerm_bot_service_azure_bot.main.name

    # Environment identification
    environment = var.environment
  }
  sensitive = true
}