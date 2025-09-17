# Backend configuration for Production environment
# This file configures remote state storage in Azure Storage Account with enhanced security

terraform {
  backend "azurerm" {
    resource_group_name  = "rg-teamsbot-prod-tfstate"
    storage_account_name = "teamsbotprodtfstate" # Must be globally unique - update this
    container_name       = "tfstate"
    key                  = "prod.terraform.tfstate"

    # Optional: Use these if not providing via environment variables or CLI
    # subscription_id      = "your-subscription-id"
    # tenant_id           = "your-tenant-id"
    # client_id           = "your-client-id"
    # client_secret       = "your-client-secret"

    # Enhanced security settings for production
    use_azuread_auth = true  # Use Azure AD authentication instead of access keys
    use_msi          = false # Set to true if using Managed Service Identity

    # State locking and encryption
    snapshot = true # Enable state snapshots for backup
  }
}