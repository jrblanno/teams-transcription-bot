# Staging Environment Configuration
# This file contains the staging-specific Terraform configuration

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
      purge_soft_delete_on_destroy          = false # Enable protection in staging
      purge_soft_deleted_secrets_on_destroy = false
    }
    resource_group {
      prevent_deletion_if_contains_resources = true # Prevent accidental deletion
    }
    storage {
      purge_soft_delete_on_destroy = false
    }
  }
}

provider "random" {}

# Root module - references the main infrastructure
module "teamsbot_infrastructure" {
  source = "../../"

  # Environment-specific variables
  environment         = "staging"
  location            = "East US"
  project_name        = "teamsbot"
  resource_group_name = "" # Auto-generate

  # Bot configuration
  bot_app_id          = var.bot_app_id
  bot_app_password    = var.bot_app_password
  azure_client_id     = var.azure_client_id
  azure_client_secret = var.azure_client_secret
  azure_tenant_id     = var.azure_tenant_id

  # Staging-optimized SKUs and settings (production-like but smaller)
  app_service_sku                  = "B2" # Basic tier with more resources
  speech_service_sku               = "S0" # Standard tier for testing at scale
  storage_account_tier             = "Standard"
  storage_account_replication_type = "LRS" # Locally redundant for staging

  # Staging settings - moderate security
  enable_private_endpoints = false # Can enable for security testing
  allowed_ip_ranges        = var.allowed_ip_ranges

  # Staging-specific tags
  tags = {
    Environment = "Staging"
    Project     = "Teams Transcription Bot"
    ManagedBy   = "terraform"
    Owner       = "QA Team"
    CostCenter  = "Quality Assurance"
    Purpose     = "Pre-Production Testing"

    # Staging lifecycle tags
    AutoShutdown    = "enabled"  # Enable auto-shutdown for cost savings
    BackupPolicy    = "standard" # Standard backup for staging
    DataClass       = "staging"  # Staging data classification
    MonitoringLevel = "enhanced" # Enhanced monitoring for staging

    # Contact information
    ContactEmail   = "qa-team@company.com"
    SlackChannel   = "#teams-bot-staging"
    EscalationPath = "qa-lead@company.com"

    # Testing metadata
    TestingPhase     = "pre-production"
    QAApproved       = "pending"
    ReleaseCandidate = "true"
  }
}

# Staging-specific outputs
output "staging_environment_info" {
  description = "Staging environment information"
  value = {
    resource_group_name    = module.teamsbot_infrastructure.resource_group_name
    app_service_url        = module.teamsbot_infrastructure.app_service_hostname
    bot_name               = module.teamsbot_infrastructure.bot_service_name
    key_vault_uri          = module.teamsbot_infrastructure.key_vault_uri
    storage_account_name   = module.teamsbot_infrastructure.storage_account_name
    estimated_monthly_cost = module.teamsbot_infrastructure.estimated_monthly_cost
  }
}

output "staging_testing_endpoints" {
  description = "Endpoints for staging testing"
  value = {
    bot_health_endpoint    = "https://${module.teamsbot_infrastructure.app_service_hostname}/health"
    bot_messaging_endpoint = "https://${module.teamsbot_infrastructure.app_service_hostname}/api/messages"
    application_insights   = "https://portal.azure.com/#@/resource${module.teamsbot_infrastructure.application_insights_name}"
    swagger_ui             = "https://${module.teamsbot_infrastructure.app_service_hostname}/swagger" # If enabled
  }
}

output "staging_deployment_info" {
  description = "Information needed for staging deployments"
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