output "bot_app_id" {
  description = "Application ID of the bot"
  value       = var.bot_app_id
}

output "permissions_configured" {
  description = "List of Graph API permissions configured"
  value = [
    "Calls.AccessMedia.All",
    "Calls.JoinGroupCall.All",
    "Calls.InitiateGroupCall.All",
    "OnlineMeetings.ReadWrite",
    "User.Read.All"
  ]
}

output "admin_consent_url" {
  description = "URL for admin consent to grant permissions"
  value       = "https://login.microsoftonline.com/${azuread_service_principal.teams_bot.application_tenant_id}/adminconsent?client_id=${var.bot_app_id}"
}

output "service_principal_id" {
  description = "Object ID of the created service principal"
  value       = azuread_service_principal.teams_bot.object_id
}