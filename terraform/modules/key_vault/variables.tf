variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "location" {
  description = "Azure region for the Key Vault"
  type        = string
}

variable "name_prefix" {
  description = "Name prefix for the Key Vault"
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

variable "tenant_id" {
  description = "Azure AD tenant ID"
  type        = string
}

variable "sku_name" {
  description = "SKU name for the Key Vault"
  type        = string
  default     = "standard"
  validation {
    condition     = contains(["standard", "premium"], var.sku_name)
    error_message = "SKU name must be either standard or premium."
  }
}

variable "enable_soft_delete" {
  description = "Whether to enable soft delete for the Key Vault"
  type        = bool
  default     = true
}

variable "purge_protection_enabled" {
  description = "Whether to enable purge protection (recommended for production)"
  type        = bool
  default     = false
}

variable "soft_delete_retention_days" {
  description = "Number of days to retain soft deleted keys"
  type        = number
  default     = 90
  validation {
    condition     = var.soft_delete_retention_days >= 7 && var.soft_delete_retention_days <= 90
    error_message = "Soft delete retention days must be between 7 and 90."
  }
}

variable "enable_private_endpoints" {
  description = "Whether to enable private endpoints for Key Vault"
  type        = bool
  default     = false
}

variable "allowed_ip_ranges" {
  description = "IP ranges allowed to access Key Vault"
  type        = list(string)
  default     = []
}

variable "subnet_id" {
  description = "Subnet ID for private endpoint (required if enable_private_endpoints is true)"
  type        = string
  default     = null
}

variable "secrets" {
  description = "Map of secrets to store in Key Vault"
  type        = map(string)
  default     = {}
  sensitive   = true
}

variable "access_policies" {
  description = "List of access policies for the Key Vault"
  type = list(object({
    tenant_id = string
    object_id = string

    key_permissions         = optional(list(string), [])
    secret_permissions      = optional(list(string), [])
    certificate_permissions = optional(list(string), [])
  }))
  default = []
}

variable "tags" {
  description = "Tags to apply to the Key Vault"
  type        = map(string)
  default     = {}
}