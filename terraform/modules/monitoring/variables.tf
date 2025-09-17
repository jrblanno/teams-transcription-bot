variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "location" {
  description = "Azure region for monitoring resources"
  type        = string
}

variable "name_prefix" {
  description = "Name prefix for monitoring resources"
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

variable "app_service_name" {
  description = "Name of the App Service to monitor"
  type        = string
}

variable "key_vault_id" {
  description = "Key Vault ID to store monitoring keys"
  type        = string
}

variable "application_type" {
  description = "Type of application for Application Insights"
  type        = string
  default     = "web"
  validation {
    condition = contains([
      "web", "java", "MobileCenter", "Node.JS", "other"
    ], var.application_type)
    error_message = "Application type must be one of: web, java, MobileCenter, Node.JS, other."
  }
}

variable "retention_in_days" {
  description = "Data retention period in days for Application Insights"
  type        = number
  default     = 90
  validation {
    condition = contains([
      30, 60, 90, 120, 180, 270, 365, 550, 730
    ], var.retention_in_days)
    error_message = "Retention period must be one of: 30, 60, 90, 120, 180, 270, 365, 550, 730 days."
  }
}

variable "daily_data_cap_in_gb" {
  description = "Daily data cap in GB for Application Insights"
  type        = number
  default     = null
  validation {
    condition     = var.daily_data_cap_in_gb == null || var.daily_data_cap_in_gb >= 0.023
    error_message = "Daily data cap must be at least 0.023 GB (minimum allowed by Azure)."
  }
}

variable "daily_data_cap_notifications_disabled" {
  description = "Whether to disable daily data cap notifications"
  type        = bool
  default     = false
}

variable "sampling_percentage" {
  description = "Sampling percentage for Application Insights"
  type        = number
  default     = null
  validation {
    condition     = var.sampling_percentage == null || (var.sampling_percentage > 0 && var.sampling_percentage <= 100)
    error_message = "Sampling percentage must be between 0 and 100."
  }
}

variable "disable_ip_masking" {
  description = "Whether to disable IP masking in Application Insights"
  type        = bool
  default     = false
}

variable "workspace_sku" {
  description = "SKU for Log Analytics workspace"
  type        = string
  default     = "PerGB2018"
  validation {
    condition = contains([
      "Free", "Standard", "Premium", "PerNode", "PerGB2018", "Standalone", "CapacityReservation"
    ], var.workspace_sku)
    error_message = "Workspace SKU must be one of: Free, Standard, Premium, PerNode, PerGB2018, Standalone, CapacityReservation."
  }
}

variable "workspace_retention_in_days" {
  description = "Data retention period in days for Log Analytics workspace"
  type        = number
  default     = 30
  validation {
    condition     = var.workspace_retention_in_days >= 30 && var.workspace_retention_in_days <= 730
    error_message = "Workspace retention must be between 30 and 730 days."
  }
}

variable "workspace_daily_quota_gb" {
  description = "Daily quota in GB for Log Analytics workspace"
  type        = number
  default     = null
}

variable "enable_log_analytics_solutions" {
  description = "Whether to enable Log Analytics solutions"
  type        = bool
  default     = true
}

variable "solutions" {
  description = "Log Analytics solutions to enable"
  type        = list(string)
  default     = ["ApplicationInsights", "ContainerInsights"]
}

variable "enable_action_groups" {
  description = "Whether to create action groups for alerting"
  type        = bool
  default     = true
}

variable "notification_email" {
  description = "Email address for alert notifications"
  type        = string
  default     = ""
}

variable "webhook_url" {
  description = "Webhook URL for alert notifications (e.g., Slack, Teams)"
  type        = string
  default     = ""
}

variable "enable_availability_tests" {
  description = "Whether to enable availability tests"
  type        = bool
  default     = true
}

variable "availability_test_locations" {
  description = "Locations for availability tests"
  type        = list(string)
  default     = ["us-ca-sjc-azr", "us-tx-sn1-azr", "us-va-ash-azr"]
}

variable "tags" {
  description = "Tags to apply to monitoring resources"
  type        = map(string)
  default     = {}
}