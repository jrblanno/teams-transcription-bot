output "app_service_plan_id" {
  description = "ID of the App Service Plan"
  value       = azurerm_service_plan.main.id
}

output "app_service_plan_name" {
  description = "Name of the App Service Plan"
  value       = azurerm_service_plan.main.name
}

output "app_service_id" {
  description = "ID of the App Service"
  value       = azurerm_linux_web_app.main.id
}

output "app_service_name" {
  description = "Name of the App Service"
  value       = azurerm_linux_web_app.main.name
}

output "app_service_hostname" {
  description = "Default hostname of the App Service"
  value       = azurerm_linux_web_app.main.default_hostname
}

output "app_service_url" {
  description = "Default URL of the App Service"
  value       = "https://${azurerm_linux_web_app.main.default_hostname}"
}

# Managed Identity information
output "app_service_identity_principal_id" {
  description = "Principal ID of the App Service managed identity"
  value       = azurerm_linux_web_app.main.identity[0].principal_id
}

output "app_service_identity_tenant_id" {
  description = "Tenant ID of the App Service managed identity"
  value       = azurerm_linux_web_app.main.identity[0].tenant_id
}

output "app_service_identity_type" {
  description = "Type of the App Service managed identity"
  value       = azurerm_linux_web_app.main.identity[0].type
}

# Network information
output "outbound_ip_addresses" {
  description = "Outbound IP addresses of the App Service"
  value       = azurerm_linux_web_app.main.outbound_ip_addresses
}

output "possible_outbound_ip_addresses" {
  description = "Possible outbound IP addresses of the App Service"
  value       = azurerm_linux_web_app.main.possible_outbound_ip_addresses
}

# Site configuration details
output "site_config" {
  description = "Site configuration details"
  value = {
    python_version      = var.python_version
    always_on           = local.always_on
    https_only          = var.enable_https_only
    minimum_tls_version = var.minimum_tls_version
  }
}

# Application settings (non-sensitive)
output "app_settings_count" {
  description = "Number of application settings configured"
  value       = length(local.final_app_settings)
}

# Bot-specific endpoints
output "bot_messaging_endpoint" {
  description = "Bot messaging endpoint URL"
  value       = "https://${azurerm_linux_web_app.main.default_hostname}/api/messages"
}

output "bot_health_endpoint" {
  description = "Bot health check endpoint URL"
  value       = "https://${azurerm_linux_web_app.main.default_hostname}/health"
}

# Deployment information
output "scm_site_hostname" {
  description = "SCM site hostname for deployments"
  value       = "https://${azurerm_linux_web_app.main.name}.scm.azurewebsites.net"
}

output "ftp_endpoint" {
  description = "FTP endpoint (if FTP is enabled)"
  value       = "ftps://${azurerm_linux_web_app.main.name}.ftp.azurewebsites.net"
}

# Publishing credentials (sensitive)
output "publishing_username" {
  description = "Publishing username for the App Service"
  value       = azurerm_linux_web_app.main.site_credential[0].name
  sensitive   = true
}

output "publishing_password" {
  description = "Publishing password for the App Service"
  value       = azurerm_linux_web_app.main.site_credential[0].password
  sensitive   = true
}

# Resource information for monitoring and scaling
output "resource_info" {
  description = "Resource information for monitoring and scaling decisions"
  value = {
    app_service_plan_sku  = var.sku_name
    app_service_plan_tier = split("_", var.sku_name)[0] # B, S, P, etc.
    worker_count          = azurerm_service_plan.main.worker_count
    environment           = var.environment
    os_type               = var.os_type
    python_version        = var.python_version
    always_on_enabled     = local.always_on
  }
}

# VNet integration status
output "vnet_integration_enabled" {
  description = "Whether VNet integration is enabled"
  value       = var.subnet_id != null
}

output "vnet_integration_subnet_id" {
  description = "Subnet ID used for VNet integration (if enabled)"
  value       = var.subnet_id
}

# Backup configuration
output "backup_enabled" {
  description = "Whether backup is enabled"
  value       = var.enable_backup
}

# Note: Diagnostic settings will be configured separately to avoid circular dependencies

# For integration with other services
output "key_vault_integration" {
  description = "Key Vault integration details"
  value = {
    key_vault_id   = var.key_vault_id
    key_vault_name = split("/", var.key_vault_id)[8]
    key_vault_uri  = "https://${split("/", var.key_vault_id)[8]}.vault.azure.net/"
  }
}