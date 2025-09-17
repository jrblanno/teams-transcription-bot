variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "location" {
  description = "Azure region for the Cognitive Services account"
  type        = string
}

variable "name_prefix" {
  description = "Name prefix for the Cognitive Services account"
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
  description = "SKU name for the Cognitive Services account"
  type        = string
  default     = "S0"
  validation {
    condition     = contains(["F0", "S0"], var.sku_name)
    error_message = "SKU name must be either F0 (free) or S0 (standard) for Speech services."
  }
}

variable "kind" {
  description = "Kind of Cognitive Services account"
  type        = string
  default     = "SpeechServices"
  validation {
    condition     = contains(["SpeechServices", "CognitiveServices"], var.kind)
    error_message = "Kind must be either SpeechServices or CognitiveServices."
  }
}

variable "custom_subdomain_name" {
  description = "Custom subdomain name for the Cognitive Services account"
  type        = string
  default     = ""
}

variable "enable_private_endpoints" {
  description = "Whether to enable private endpoints for Cognitive Services"
  type        = bool
  default     = false
}

variable "allowed_ip_ranges" {
  description = "IP ranges allowed to access Cognitive Services"
  type        = list(string)
  default     = []
}

variable "subnet_id" {
  description = "Subnet ID for private endpoint (required if enable_private_endpoints is true)"
  type        = string
  default     = null
}

variable "key_vault_id" {
  description = "Key Vault ID to store Cognitive Services keys"
  type        = string
}

variable "dynamic_throttling_enabled" {
  description = "Whether to enable dynamic throttling"
  type        = bool
  default     = true
}

variable "fqdns" {
  description = "List of FQDNs allowed for this Cognitive Services account"
  type        = list(string)
  default     = []
}

variable "outbound_network_access_restricted" {
  description = "Whether outbound network access is restricted"
  type        = bool
  default     = false
}

variable "local_auth_enabled" {
  description = "Whether local authentication is enabled"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags to apply to the Cognitive Services account"
  type        = map(string)
  default     = {}
}