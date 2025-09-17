# Azure AD App Registration with Graph API permissions
terraform {
  required_providers {
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 2.47.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.70.0"
    }
  }
}

# Data source for Microsoft Graph
data "azuread_application_published_app_ids" "well_known" {}

data "azuread_service_principal" "msgraph" {
  client_id = data.azuread_application_published_app_ids.well_known.result.MicrosoftGraph
}

# Get existing app registration
data "azuread_application" "teams_bot" {
  application_id = var.bot_app_id
}

# Create service principal for the bot application if it doesn't exist
resource "azuread_service_principal" "teams_bot" {
  client_id = var.bot_app_id

  # Enable service principal
  app_role_assignment_required = false

  tags = ["Teams", "Bot", "Transcription"]

  depends_on = [data.azuread_application.teams_bot]
}

# Configure Graph API permissions using azuread_application_api_access
resource "azuread_application_api_access" "msgraph_permissions" {
  application_id = data.azuread_application.teams_bot.id
  api_client_id  = data.azuread_application_published_app_ids.well_known.result["MicrosoftGraph"]

  # Application permissions (roles) for Teams bot
  role_ids = [
    data.azuread_service_principal.msgraph.app_role_ids["Calls.AccessMedia.All"],
    data.azuread_service_principal.msgraph.app_role_ids["Calls.JoinGroupCall.All"],
    data.azuread_service_principal.msgraph.app_role_ids["Calls.InitiateGroupCall.All"],
    data.azuread_service_principal.msgraph.app_role_ids["OnlineMeetings.ReadWrite.All"],
    data.azuread_service_principal.msgraph.app_role_ids["User.Read.All"]
  ]
}

# Note: Admin consent will still need to be granted after permissions are applied
# This can be done via the Azure Portal or using the admin consent URL