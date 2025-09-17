output "log_analytics_workspace_id" {
  description = "ID of the Log Analytics workspace"
  value       = azurerm_log_analytics_workspace.main.id
}

output "log_analytics_workspace_name" {
  description = "Name of the Log Analytics workspace"
  value       = azurerm_log_analytics_workspace.main.name
}

output "log_analytics_workspace_workspace_id" {
  description = "Workspace ID of the Log Analytics workspace"
  value       = azurerm_log_analytics_workspace.main.workspace_id
}

output "log_analytics_primary_shared_key" {
  description = "Primary shared key of the Log Analytics workspace"
  value       = azurerm_log_analytics_workspace.main.primary_shared_key
  sensitive   = true
}

output "log_analytics_secondary_shared_key" {
  description = "Secondary shared key of the Log Analytics workspace"
  value       = azurerm_log_analytics_workspace.main.secondary_shared_key
  sensitive   = true
}

# Application Insights outputs
output "application_insights_id" {
  description = "ID of the Application Insights instance"
  value       = azurerm_application_insights.main.id
}

output "application_insights_name" {
  description = "Name of the Application Insights instance"
  value       = azurerm_application_insights.main.name
}

output "instrumentation_key" {
  description = "Instrumentation key for Application Insights"
  value       = azurerm_application_insights.main.instrumentation_key
  sensitive   = true
}

output "connection_string" {
  description = "Connection string for Application Insights"
  value       = azurerm_application_insights.main.connection_string
  sensitive   = true
}

output "app_id" {
  description = "App ID of the Application Insights instance"
  value       = azurerm_application_insights.main.app_id
}

# Key Vault secret references
output "instrumentation_key_secret_id" {
  description = "ID of the instrumentation key secret in Key Vault"
  value       = azurerm_key_vault_secret.app_insights_key.id
  sensitive   = true
}

output "connection_string_secret_id" {
  description = "ID of the connection string secret in Key Vault"
  value       = azurerm_key_vault_secret.app_insights_connection_string.id
  sensitive   = true
}

# Key Vault references for App Service configuration
output "key_vault_references" {
  description = "Key Vault references for use in App Service configuration"
  value = {
    APPLICATIONINSIGHTS_CONNECTION_STRING = "@Microsoft.KeyVault(VaultName=${split("/", var.key_vault_id)[8]};SecretName=application-insights-connection-string)"
    APPINSIGHTS_INSTRUMENTATIONKEY        = "@Microsoft.KeyVault(VaultName=${split("/", var.key_vault_id)[8]};SecretName=application-insights-instrumentation-key)"
  }
  sensitive = true
}

# Action Group outputs
output "action_group_id" {
  description = "ID of the action group (if enabled)"
  value       = var.enable_action_groups ? azurerm_monitor_action_group.main[0].id : null
}

output "action_group_name" {
  description = "Name of the action group (if enabled)"
  value       = var.enable_action_groups ? azurerm_monitor_action_group.main[0].name : null
}

# Availability Test outputs
output "availability_test_id" {
  description = "ID of the availability test (if enabled)"
  value       = var.enable_availability_tests ? azurerm_application_insights_web_test.main[0].id : null
}

output "availability_test_name" {
  description = "Name of the availability test (if enabled)"
  value       = var.enable_availability_tests ? azurerm_application_insights_web_test.main[0].name : null
}

# Metric Alert outputs
output "cpu_alert_id" {
  description = "ID of the CPU usage alert (if enabled)"
  value       = var.enable_action_groups ? azurerm_monitor_metric_alert.app_service_cpu[0].id : null
}

output "memory_alert_id" {
  description = "ID of the memory usage alert (if enabled)"
  value       = var.enable_action_groups ? azurerm_monitor_metric_alert.app_service_memory[0].id : null
}

output "response_time_alert_id" {
  description = "ID of the response time alert (if enabled)"
  value       = var.enable_action_groups ? azurerm_monitor_metric_alert.app_service_response_time[0].id : null
}

output "availability_alert_id" {
  description = "ID of the availability alert (if enabled)"
  value       = var.enable_availability_tests && var.enable_action_groups ? azurerm_monitor_metric_alert.availability_test[0].id : null
}

# Log Analytics Solutions
output "log_analytics_solutions" {
  description = "Map of enabled Log Analytics solutions"
  value = var.enable_log_analytics_solutions ? {
    for solution in var.solutions : solution => {
      id   = azurerm_log_analytics_solution.solutions[solution].id
      name = azurerm_log_analytics_solution.solutions[solution].solution_name
    }
  } : {}
}

# Monitoring Configuration Summary
output "monitoring_configuration" {
  description = "Summary of monitoring configuration"
  value = {
    workspace_name              = azurerm_log_analytics_workspace.main.name
    workspace_sku               = azurerm_log_analytics_workspace.main.sku
    workspace_retention_days    = azurerm_log_analytics_workspace.main.retention_in_days
    app_insights_name           = azurerm_application_insights.main.name
    app_insights_type           = azurerm_application_insights.main.application_type
    app_insights_retention_days = azurerm_application_insights.main.retention_in_days
    daily_data_cap_gb           = azurerm_application_insights.main.daily_data_cap_in_gb
    action_group_enabled        = var.enable_action_groups
    availability_tests_enabled  = var.enable_availability_tests
    solutions_enabled           = var.enable_log_analytics_solutions ? var.solutions : []
  }
}

# Dashboards and Queries (for future implementation)
output "monitoring_urls" {
  description = "URLs for monitoring dashboards and queries"
  value = {
    application_insights_url = "https://portal.azure.com/#@/resource${azurerm_application_insights.main.id}/overview"
    log_analytics_url        = "https://portal.azure.com/#@/resource${azurerm_log_analytics_workspace.main.id}/logs"
    availability_test_url    = var.enable_availability_tests ? "https://portal.azure.com/#@/resource${azurerm_application_insights_web_test.main[0].id}/overview" : null
  }
}

# Configuration for Python application
output "monitoring_config" {
  description = "Configuration object for monitoring integration in Python app"
  value = {
    instrumentation_key = azurerm_application_insights.main.instrumentation_key
    connection_string   = azurerm_application_insights.main.connection_string
    app_insights_name   = azurerm_application_insights.main.name
    workspace_id        = azurerm_log_analytics_workspace.main.workspace_id
    workspace_name      = azurerm_log_analytics_workspace.main.name
    environment         = var.environment
  }
  sensitive = true
}