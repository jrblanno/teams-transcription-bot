# Backend configuration for Staging environment
# This file configures remote state storage in Azure Storage Account

terraform {
  backend "azurerm" {
    resource_group_name  = "rg-teamsbot-staging-tfstate"
    storage_account_name = "teamsbotstagingstfstate" # Must be globally unique - update this
    container_name       = "tfstate"
    key                  = "staging.terraform.tfstate"

    # Optional: Use these if not providing via environment variables or CLI
    # subscription_id      = "your-subscription-id"
    # tenant_id           = "your-tenant-id"
    # client_id           = "your-client-id"
    # client_secret       = "your-client-secret"

    # Security settings
    use_azuread_auth = true # Use Azure AD authentication instead of access keys
  }
}