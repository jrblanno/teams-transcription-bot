output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "resource_group_location" {
  description = "Location of the resource group"
  value       = azurerm_resource_group.main.location
}

output "storage_account_name" {
  description = "Name of the storage account"
  value       = module.storage.storage_account_name
}

output "storage_account_primary_blob_endpoint" {
  description = "Primary blob endpoint of the storage account"
  value       = module.storage.primary_blob_endpoint
}

output "key_vault_name" {
  description = "Name of the Key Vault"
  value       = module.key_vault.key_vault_name
}

output "key_vault_uri" {
  description = "URI of the Key Vault"
  value       = module.key_vault.key_vault_uri
}

output "app_service_name" {
  description = "Name of the App Service"
  value       = module.app_service.app_service_name
}

output "app_service_hostname" {
  description = "Hostname of the App Service"
  value       = module.app_service.app_service_hostname
}

output "app_service_identity_principal_id" {
  description = "Principal ID of the App Service managed identity"
  value       = module.app_service.app_service_identity_principal_id
}

output "bot_service_name" {
  description = "Name of the Bot Service"
  value       = module.bot_service.bot_service_name
}

output "bot_service_messaging_endpoint" {
  description = "Messaging endpoint of the Bot Service"
  value       = module.bot_service.messaging_endpoint
}

output "cognitive_services_name" {
  description = "Name of the Cognitive Services account"
  value       = data.azurerm_cognitive_account.existing_speech.name
}

output "cognitive_services_endpoint" {
  description = "Endpoint of the Cognitive Services account"
  value       = data.azurerm_cognitive_account.existing_speech.endpoint
}

output "cognitive_services_location" {
  description = "Location of the Cognitive Services account"
  value       = data.azurerm_cognitive_account.existing_speech.location
}

output "application_insights_name" {
  description = "Name of the Application Insights instance"
  value       = module.monitoring.application_insights_name
}

output "application_insights_instrumentation_key" {
  description = "Instrumentation key for Application Insights"
  value       = module.monitoring.instrumentation_key
  sensitive   = true
}

output "application_insights_connection_string" {
  description = "Connection string for Application Insights"
  value       = module.monitoring.connection_string
  sensitive   = true
}

output "log_analytics_workspace_id" {
  description = "ID of the Log Analytics workspace"
  value       = module.monitoring.log_analytics_workspace_id
}

# Environment-specific outputs for application configuration
output "environment_variables" {
  description = "Environment variables for the application"
  value = {
    AZURE_SUBSCRIPTION_ID    = data.azurerm_client_config.current.subscription_id
    AZURE_TENANT_ID          = data.azurerm_client_config.current.tenant_id
    AZURE_RESOURCE_GROUP     = azurerm_resource_group.main.name
    AZURE_SPEECH_REGION      = data.azurerm_cognitive_account.existing_speech.location
    BOT_APP_ID               = var.bot_app_id
    STORAGE_ACCOUNT_NAME     = module.storage.storage_account_name
    KEY_VAULT_URI            = module.key_vault.key_vault_uri
    APPLICATION_INSIGHTS_KEY = module.monitoring.instrumentation_key
  }
  sensitive = true
}

# Cost tracking outputs
output "estimated_monthly_cost" {
  description = "Estimated monthly cost for the environment"
  value = {
    app_service_plan   = local.cost_estimates.app_service
    cognitive_services = local.cost_estimates.cognitive_services
    storage            = local.cost_estimates.storage
    key_vault          = local.cost_estimates.key_vault
    monitoring         = local.cost_estimates.monitoring
    total_usd          = local.cost_estimates.total
  }
}