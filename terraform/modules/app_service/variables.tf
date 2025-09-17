variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "location" {
  description = "Azure region for the App Service"
  type        = string
}

variable "name_prefix" {
  description = "Name prefix for the App Service"
  type        = string
}

variable "random_suffix" {
  description = "Random suffix for globally unique naming"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "sku_name" {
  description = "SKU name for the App Service Plan"
  type        = string
  default     = "B1"
  validation {
    condition = contains([
      "B1", "B2", "B3",       # Basic tier
      "S1", "S2", "S3",       # Standard tier
      "P1v2", "P2v2", "P3v2", # Premium tier
      "P1v3", "P2v3", "P3v3"  # Premium v3 tier
    ], var.sku_name)
    error_message = "App Service SKU must be a valid Azure App Service plan size."
  }
}

variable "os_type" {
  description = "OS type for the App Service Plan"
  type        = string
  default     = "Linux"
  validation {
    condition     = contains(["Linux", "Windows"], var.os_type)
    error_message = "OS type must be either Linux or Windows."
  }
}

variable "python_version" {
  description = "Python version for the App Service"
  type        = string
  default     = "3.11"
  validation {
    condition     = contains(["3.8", "3.9", "3.10", "3.11"], var.python_version)
    error_message = "Python version must be 3.8, 3.9, 3.10, or 3.11."
  }
}

variable "key_vault_id" {
  description = "Key Vault ID for secrets integration"
  type        = string
}

variable "storage_account_name" {
  description = "Storage account name for integration"
  type        = string
}

variable "application_insights_key" {
  description = "Application Insights instrumentation key"
  type        = string
  sensitive   = true
}

variable "always_on" {
  description = "Whether to keep the app always on"
  type        = bool
  default     = null # Will be set based on environment
}

variable "app_settings" {
  description = "Additional app settings"
  type        = map(string)
  default     = {}
}

variable "connection_strings" {
  description = "Connection strings for the app"
  type = map(object({
    type  = string
    value = string
  }))
  default = {}
}

variable "enable_client_affinity" {
  description = "Whether to enable client affinity (sticky sessions)"
  type        = bool
  default     = false # Disabled for stateless bot applications
}

variable "enable_https_only" {
  description = "Whether to enable HTTPS only"
  type        = bool
  default     = true
}

variable "minimum_tls_version" {
  description = "Minimum TLS version"
  type        = string
  default     = "1.2"
  validation {
    condition     = contains(["1.0", "1.1", "1.2"], var.minimum_tls_version)
    error_message = "Minimum TLS version must be 1.0, 1.1, or 1.2."
  }
}

variable "enable_backup" {
  description = "Whether to enable backup for the App Service"
  type        = bool
  default     = false
}

variable "backup_storage_account_url" {
  description = "Storage account URL for backups (required if enable_backup is true)"
  type        = string
  default     = ""
}

variable "backup_schedule" {
  description = "Backup schedule configuration"
  type = object({
    frequency_interval       = number
    frequency_unit           = string
    keep_at_least_one_backup = bool
    retention_period_days    = number
  })
  default = {
    frequency_interval       = 1
    frequency_unit           = "Day"
    keep_at_least_one_backup = true
    retention_period_days    = 30
  }
}

variable "subnet_id" {
  description = "Subnet ID for VNet integration"
  type        = string
  default     = null
}

variable "tags" {
  description = "Tags to apply to the App Service resources"
  type        = map(string)
  default     = {}
}