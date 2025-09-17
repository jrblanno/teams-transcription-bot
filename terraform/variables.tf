variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "East US"
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = ""
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "teamsbot"
}

variable "bot_app_id" {
  description = "Bot application ID from Azure AD app registration"
  type        = string
  sensitive   = true
}

variable "bot_app_password" {
  description = "Bot application password from Azure AD app registration"
  type        = string
  sensitive   = true
}

variable "azure_client_id" {
  description = "Azure AD application client ID for Graph API access"
  type        = string
  sensitive   = true
}

variable "azure_client_secret" {
  description = "Azure AD application client secret for Graph API access"
  type        = string
  sensitive   = true
}

variable "azure_tenant_id" {
  description = "Azure AD tenant ID"
  type        = string
  sensitive   = true
}

variable "speech_service_sku" {
  description = "SKU for Cognitive Services Speech service"
  type        = string
  default     = "S0"
  validation {
    condition     = contains(["F0", "S0"], var.speech_service_sku)
    error_message = "Speech service SKU must be either F0 (free) or S0 (standard)."
  }
}

variable "app_service_sku" {
  description = "SKU for App Service Plan"
  type        = string
  default     = "B1"
  validation {
    condition = contains([
      "B1", "B2", "B3",      # Basic tier
      "S1", "S2", "S3",      # Standard tier
      "P1v2", "P2v2", "P3v2" # Premium tier
    ], var.app_service_sku)
    error_message = "App Service SKU must be a valid Azure App Service plan size."
  }
}

variable "storage_account_tier" {
  description = "Storage account performance tier"
  type        = string
  default     = "Standard"
  validation {
    condition     = contains(["Standard", "Premium"], var.storage_account_tier)
    error_message = "Storage account tier must be either Standard or Premium."
  }
}

variable "storage_account_replication_type" {
  description = "Storage account replication type"
  type        = string
  default     = "LRS"
  validation {
    condition = contains([
      "LRS", "GRS", "RAGRS", "ZRS", "GZRS", "RAGZRS"
    ], var.storage_account_replication_type)
    error_message = "Invalid storage replication type."
  }
}

variable "enable_private_endpoints" {
  description = "Whether to enable private endpoints for services"
  type        = bool
  default     = false
}

variable "allowed_ip_ranges" {
  description = "IP ranges allowed to access resources"
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}