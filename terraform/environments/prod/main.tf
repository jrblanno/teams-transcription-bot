# Production Environment Configuration
# This file contains the production-specific Terraform configuration with enhanced security

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

# Configure the Azure Provider with production security features
provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy          = false # Enable protection in production
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
  environment         = "prod"
  location            = var.location
  project_name        = "teamsbot"
  resource_group_name = var.resource_group_name

  # Bot configuration
  bot_app_id          = var.bot_app_id
  bot_app_password    = var.bot_app_password
  azure_client_id     = var.azure_client_id
  azure_client_secret = var.azure_client_secret
  azure_tenant_id     = var.azure_tenant_id

  # Production-grade SKUs and settings
  app_service_sku                  = var.app_service_sku
  speech_service_sku               = "S0" # Standard tier for production
  storage_account_tier             = "Standard"
  storage_account_replication_type = var.storage_account_replication_type

  # Production security settings
  enable_private_endpoints = var.enable_private_endpoints
  allowed_ip_ranges        = var.allowed_ip_ranges

  # Production-specific tags
  tags = {
    Environment = "Production"
    Project     = "Teams Transcription Bot"
    ManagedBy   = "terraform"
    Owner       = "Operations Team"
    CostCenter  = "IT Operations"
    Purpose     = "Production Service"

    # Production lifecycle tags
    AutoShutdown    = "disabled"   # Never auto-shutdown production
    BackupPolicy    = "enterprise" # Enterprise backup requirements
    DataClass       = "production" # Production data classification
    MonitoringLevel = "critical"   # Critical monitoring for production

    # Contact information
    ContactEmail   = "ops-team@company.com"
    SlackChannel   = "#teams-bot-prod"
    EscalationPath = "ops-manager@company.com"
    OnCallRotation = "teams-bot-oncall"

    # Compliance and security
    ComplianceLevel = "enterprise"
    SecurityReview  = "approved"
    DataRetention   = "7years"
    EncryptionLevel = "enterprise"

    # Service level
    ServiceLevel     = "production"
    SLA              = "99.9%"
    BusinessCritical = "true"
    DisasterRecovery = "required"

    # Change management
    ChangeControl     = "required"
    ApprovalRequired  = "true"
    MaintenanceWindow = "sunday-2am-4am-utc"
  }
}

# Production-specific outputs
output "production_environment_info" {
  description = "Production environment information"
  value = {
    resource_group_name    = module.teamsbot_infrastructure.resource_group_name
    app_service_url        = module.teamsbot_infrastructure.app_service_hostname
    bot_name               = module.teamsbot_infrastructure.bot_service_name
    key_vault_uri          = module.teamsbot_infrastructure.key_vault_uri
    storage_account_name   = module.teamsbot_infrastructure.storage_account_name
    estimated_monthly_cost = module.teamsbot_infrastructure.estimated_monthly_cost
  }
}

output "production_service_endpoints" {
  description = "Production service endpoints"
  value = {
    bot_health_endpoint    = "https://${module.teamsbot_infrastructure.app_service_hostname}/health"
    bot_messaging_endpoint = "https://${module.teamsbot_infrastructure.app_service_hostname}/api/messages"
    application_insights   = "https://portal.azure.com/#@/resource${module.teamsbot_infrastructure.application_insights_name}"
    # Note: Swagger/debug endpoints should be disabled in production
  }
  sensitive = true # Production endpoints are sensitive
}

output "production_monitoring_info" {
  description = "Production monitoring and alerting information"
  value = {
    application_insights_name = module.teamsbot_infrastructure.application_insights_name
    log_analytics_workspace   = module.teamsbot_infrastructure.log_analytics_workspace_id
    action_group_enabled      = true
    availability_test_enabled = true
    sla_target                = "99.9%"
  }
}

output "production_security_info" {
  description = "Production security configuration"
  value = {
    private_endpoints_enabled  = var.enable_private_endpoints
    key_vault_purge_protection = true
    storage_encryption_enabled = true
    network_restrictions       = length(var.allowed_ip_ranges) > 0
    managed_identity_enabled   = true
  }
}

output "production_deployment_info" {
  description = "Information needed for production deployments"
  value = {
    app_service_name = module.teamsbot_infrastructure.app_service_name
    resource_group   = module.teamsbot_infrastructure.resource_group_name
    subscription_id  = data.azurerm_client_config.current.subscription_id
    tenant_id        = data.azurerm_client_config.current.tenant_id
    deployment_slots = ["staging"] # Production should use deployment slots
  }
  sensitive = true
}

# Get current Azure client configuration
data "azurerm_client_config" "current" {}