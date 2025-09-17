output "storage_account_id" {
  description = "ID of the storage account"
  value       = azurerm_storage_account.main.id
}

output "storage_account_name" {
  description = "Name of the storage account"
  value       = azurerm_storage_account.main.name
}

output "primary_blob_endpoint" {
  description = "Primary blob endpoint of the storage account"
  value       = azurerm_storage_account.main.primary_blob_endpoint
}

output "primary_blob_host" {
  description = "Primary blob host of the storage account"
  value       = azurerm_storage_account.main.primary_blob_host
}

output "primary_access_key" {
  description = "Primary access key of the storage account"
  value       = azurerm_storage_account.main.primary_access_key
  sensitive   = true
}

output "primary_connection_string" {
  description = "Primary connection string of the storage account"
  value       = azurerm_storage_account.main.primary_connection_string
  sensitive   = true
}

output "secondary_access_key" {
  description = "Secondary access key of the storage account"
  value       = azurerm_storage_account.main.secondary_access_key
  sensitive   = true
}

output "secondary_connection_string" {
  description = "Secondary connection string of the storage account"
  value       = azurerm_storage_account.main.secondary_connection_string
  sensitive   = true
}

# Container information
output "transcripts_container_name" {
  description = "Name of the transcripts container"
  value       = azurerm_storage_container.transcripts.name
}

output "audio_temp_container_name" {
  description = "Name of the temporary audio container"
  value       = azurerm_storage_container.audio_temp.name
}

output "bot_state_container_name" {
  description = "Name of the bot state container"
  value       = azurerm_storage_container.bot_state.name
}

output "terraform_state_container_name" {
  description = "Name of the terraform state container"
  value       = azurerm_storage_container.terraform_state.name
}

# Private endpoint information (if enabled)
output "private_endpoint_id" {
  description = "ID of the private endpoint (if enabled)"
  value       = var.enable_private_endpoints ? azurerm_private_endpoint.storage[0].id : null
}

output "private_endpoint_ip" {
  description = "Private IP address of the storage endpoint (if enabled)"
  value       = var.enable_private_endpoints ? azurerm_private_endpoint.storage[0].private_service_connection[0].private_ip_address : null
}