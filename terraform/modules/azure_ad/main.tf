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

# Update existing app registration with Graph API permissions
data "azuread_application" "teams_bot" {
  application_id = var.bot_app_id
}

# For POC: Document permissions that need to be granted manually
# The following Graph API permissions need to be granted via Azure Portal:
# - Calls.AccessMedia.All (a267235c-af32-4ed5-a2cc-9e80b6c34530)
# - Calls.JoinGroupCall.All (f6b49018-60ab-4f81-83bd-22caeabfed2d)
# - Calls.InitiateGroupCall.All (5af7b33a-8ec8-4e5a-86fc-235c38358aa6)
# - OnlineMeetings.ReadWrite (b8bb2037-6e08-44ac-a4ea-4674e010e2a4)
# - User.Read.All (df021288-bdef-4463-88db-98f22de89214)

# Create service principal for the bot application if it doesn't exist
resource "azuread_service_principal" "teams_bot" {
  client_id = var.bot_app_id

  # Enable service principal
  app_role_assignment_required = false

  tags = ["Teams", "Bot", "Transcription"]

  depends_on = [data.azuread_application.teams_bot]
}

# For POC: Service principal created successfully
# Admin consent for Graph API permissions should be granted manually via Azure Portal
# URL: https://login.microsoftonline.com/{tenant_id}/adminconsent?client_id={app_id}