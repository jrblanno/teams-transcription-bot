# Generate storage account name (must be globally unique and 3-24 chars)
locals {
  # Remove hyphens and limit to 24 characters for storage account naming
  storage_account_name = lower(substr(
    replace("${var.name_prefix}${var.random_suffix}st", "-", ""),
    0, 24
  ))
}

# Storage Account for bot data and Terraform state
resource "azurerm_storage_account" "main" {
  name                     = local.storage_account_name
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = var.storage_tier
  account_replication_type = var.storage_replication_type

  # Security and compliance settings - simplified
  allow_nested_items_to_be_public = false
  shared_access_key_enabled       = true
  public_network_access_enabled   = true

  # Enable versioning and soft delete for data protection
  blob_properties {
    versioning_enabled       = true
    change_feed_enabled      = var.environment == "prod" ? true : false
    last_access_time_enabled = true

    delete_retention_policy {
      days = var.environment == "prod" ? 30 : 7
    }

    container_delete_retention_policy {
      days = var.environment == "prod" ? 30 : 7
    }
  }

  # Enable static website if needed for frontend hosting
  static_website {
    index_document = "index.html"
  }

  # Network access control - simplified, allow all

  tags = var.tags

}

# Container for storing meeting transcripts
resource "azurerm_storage_container" "transcripts" {
  name                  = "transcripts"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

# Container for temporary audio files during processing
resource "azurerm_storage_container" "audio_temp" {
  name                  = "audio-temp"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

# Container for bot state data
resource "azurerm_storage_container" "bot_state" {
  name                  = "bot-state"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

# Container for Terraform state (if using this storage for backend)
resource "azurerm_storage_container" "terraform_state" {
  name                  = "tfstate"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

# Lifecycle management policy for cost optimization
resource "azurerm_storage_management_policy" "lifecycle" {
  storage_account_id = azurerm_storage_account.main.id

  rule {
    name    = "transcript-lifecycle"
    enabled = true

    filters {
      prefix_match = ["transcripts/"]
      blob_types   = ["blockBlob"]
    }

    actions {
      base_blob {
        # Move to cool tier after 30 days
        tier_to_cool_after_days_since_modification_greater_than = 30
        # Move to archive tier after 90 days
        tier_to_archive_after_days_since_modification_greater_than = 90
        # Delete after 2 years (adjust based on retention policy)
        delete_after_days_since_modification_greater_than = 730
      }

      snapshot {
        delete_after_days_since_creation_greater_than = 30
      }

      version {
        delete_after_days_since_creation = 30
      }
    }
  }

  rule {
    name    = "temp-audio-cleanup"
    enabled = true

    filters {
      prefix_match = ["audio-temp/"]
      blob_types   = ["blockBlob"]
    }

    actions {
      base_blob {
        # Delete temporary audio files after 1 day
        delete_after_days_since_modification_greater_than = 1
      }
    }
  }
}

# Private endpoint for storage (if enabled)
resource "azurerm_private_endpoint" "storage" {
  count               = var.enable_private_endpoints ? 1 : 0
  name                = "${local.storage_account_name}-pe"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.subnet_id

  private_service_connection {
    name                           = "${local.storage_account_name}-psc"
    private_connection_resource_id = azurerm_storage_account.main.id
    subresource_names              = ["blob"]
    is_manual_connection           = false
  }

  tags = var.tags
}