variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "location" {
  description = "Azure region for the storage account"
  type        = string
}

variable "name_prefix" {
  description = "Name prefix for the storage account"
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

variable "storage_tier" {
  description = "Storage account performance tier"
  type        = string
  default     = "Standard"
  validation {
    condition     = contains(["Standard", "Premium"], var.storage_tier)
    error_message = "Storage tier must be either Standard or Premium."
  }
}

variable "storage_replication_type" {
  description = "Storage account replication type"
  type        = string
  default     = "LRS"
  validation {
    condition = contains([
      "LRS", "GRS", "RAGRS", "ZRS", "GZRS", "RAGZRS"
    ], var.storage_replication_type)
    error_message = "Invalid storage replication type."
  }
}

variable "enable_private_endpoints" {
  description = "Whether to enable private endpoints for storage"
  type        = bool
  default     = false
}

variable "allowed_ip_ranges" {
  description = "IP ranges allowed to access storage account"
  type        = list(string)
  default     = []
}

variable "subnet_id" {
  description = "Subnet ID for private endpoint (required if enable_private_endpoints is true)"
  type        = string
  default     = null
}

variable "tags" {
  description = "Tags to apply to the storage account"
  type        = map(string)
  default     = {}
}