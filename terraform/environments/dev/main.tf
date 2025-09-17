# Development Environment Configuration
# This file contains the development-specific Terraform configuration

# Configure the Terraform providers and versions
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.70.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5.0"
    }
  }
}

# Configure the Azure Provider with features
provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy          = true # Allow purging in dev for testing
      purge_soft_deleted_secrets_on_destroy = true
    }
    resource_group {
      prevent_deletion_if_contains_resources = false # Allow deletion in dev
    }
    storage {
      purge_soft_delete_on_destroy = true
    }
  }
}

provider "random" {}

# Root module - references the main infrastructure
module "teamsbot_infrastructure" {
  source = "../../"

  # Environment-specific variables
  environment         = "dev"
  location            = "East US"
  project_name        = "teamsbot"
  resource_group_name = "" # Auto-generate

  # Bot configuration
  bot_app_id          = var.bot_app_id
  bot_app_password    = var.bot_app_password
  azure_client_id     = var.azure_client_id
  azure_client_secret = var.azure_client_secret
  azure_tenant_id     = var.azure_tenant_id

  # Development-optimized SKUs and settings
  app_service_sku                  = "B1" # Basic tier for cost optimization
  speech_service_sku               = "F0" # Free tier for development
  storage_account_tier             = "Standard"
  storage_account_replication_type = "LRS" # Locally redundant for dev

  # Development settings - less restrictive security
  enable_private_endpoints = false
  allowed_ip_ranges        = [] # Open access for development

  # Development-specific tags
  tags = {
    Environment = "Development"
    Project     = "Teams Transcription Bot"
    ManagedBy   = "terraform"
    Owner       = "Development Team"
    CostCenter  = "R&D"
    Purpose     = "Development and Testing"

    # Development lifecycle tags
    AutoShutdown = "enabled"     # Enable auto-shutdown for cost savings
    BackupPolicy = "minimal"     # Minimal backup for dev
    DataClass    = "development" # Development data classification

    # Contact information
    ContactEmail = "dev-team@company.com"
    SlackChannel = "#teams-bot-dev"
  }
}

# Development-specific outputs
output "dev_environment_info" {
  description = "Development environment information"
  value = {
    resource_group_name    = module.teamsbot_infrastructure.resource_group_name
    app_service_url        = module.teamsbot_infrastructure.app_service_hostname
    bot_name               = module.teamsbot_infrastructure.bot_service_name
    key_vault_uri          = module.teamsbot_infrastructure.key_vault_uri
    storage_account_name   = module.teamsbot_infrastructure.storage_account_name
    estimated_monthly_cost = module.teamsbot_infrastructure.estimated_monthly_cost
  }
}

output "dev_testing_urls" {
  description = "URLs for testing in development environment"
  value = {
    bot_health_endpoint    = "https://${module.teamsbot_infrastructure.app_service_hostname}/health"
    bot_messaging_endpoint = "https://${module.teamsbot_infrastructure.app_service_hostname}/api/messages"
    application_insights   = "https://portal.azure.com/#@/resource${module.teamsbot_infrastructure.application_insights_name}"
  }
}

output "dev_deployment_info" {
  description = "Information needed for development deployments"
  value = {
    app_service_name = module.teamsbot_infrastructure.app_service_name
    resource_group   = module.teamsbot_infrastructure.resource_group_name
    subscription_id  = data.azurerm_client_config.current.subscription_id
    tenant_id        = data.azurerm_client_config.current.tenant_id
  }
  sensitive = false
}

# Get current Azure client configuration
data "azurerm_client_config" "current" {}