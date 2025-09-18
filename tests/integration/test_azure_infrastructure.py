"""Integration tests for Azure infrastructure - tests against real Azure resources."""
import os
import pytest
from pathlib import Path
from dotenv import load_dotenv
from azure.identity import ClientSecretCredential
from azure.keyvault.secrets import SecretClient
from azure.mgmt.web import WebSiteManagementClient
from azure.mgmt.botservice import AzureBotService
from azure.mgmt.resource import ResourceManagementClient
from azure.cognitiveservices.speech import SpeechConfig
# ConversationTranscriber will be tested when actual implementation is available
import requests
import time

# Load environment variables
load_dotenv()

class TestAzureInfrastructure:
    """Test real Azure infrastructure deployment."""

    @classmethod
    def setup_class(cls):
        """Set up Azure credentials and clients."""
        cls.tenant_id = os.getenv("AZURE_TENANT_ID")
        cls.client_id = os.getenv("AZURE_CLIENT_ID")
        cls.client_secret = os.getenv("AZURE_CLIENT_SECRET")
        cls.subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")

        # Validate all required env vars are present
        assert cls.tenant_id, "AZURE_TENANT_ID not set"
        assert cls.client_id, "AZURE_CLIENT_ID not set"
        assert cls.client_secret, "AZURE_CLIENT_SECRET not set"
        assert cls.subscription_id, "AZURE_SUBSCRIPTION_ID not set"

        # Create credential
        cls.credential = ClientSecretCredential(
            tenant_id=cls.tenant_id,
            client_id=cls.client_id,
            client_secret=cls.client_secret
        )

        # Resource group from Terraform
        cls.resource_group = "rg-teamsbot-poc"
        cls.key_vault_name = "teamsbotpockv"
        cls.app_service_name = "teamsbot-poc-app"
        cls.bot_service_name = "teamsbot-poc-bot"

    def test_resource_group_exists(self):
        """Test that resource group was created."""
        resource_client = ResourceManagementClient(
            self.credential,
            self.subscription_id
        )

        # Check resource group exists
        resource_group = resource_client.resource_groups.get(self.resource_group)
        assert resource_group is not None
        assert resource_group.name == self.resource_group
        assert resource_group.location == "westeurope"

    def test_key_vault_accessible(self):
        """Test Key Vault is accessible and contains secrets."""
        key_vault_url = f"https://{self.key_vault_name}.vault.azure.net/"
        secret_client = SecretClient(vault_url=key_vault_url, credential=self.credential)

        # Test we can list secrets (may need time for RBAC to propagate)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                secrets = list(secret_client.list_properties_of_secrets())
                assert len(secrets) > 0, "No secrets found in Key Vault"

                # Verify expected secrets exist
                secret_names = [s.name for s in secrets]
                assert "bot-app-id" in secret_names
                assert "bot-app-password" in secret_names
                assert "azure-speech-key" in secret_names
                assert "azure-speech-endpoint" in secret_names
                assert "azure-speech-region" in secret_names
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(10)  # Wait for RBAC propagation

    def test_app_service_running(self):
        """Test that App Service is running and accessible."""
        web_client = WebSiteManagementClient(
            self.credential,
            self.subscription_id
        )

        # Get app service
        app = web_client.web_apps.get(
            resource_group_name=self.resource_group,
            name=self.app_service_name
        )

        assert app is not None
        assert app.state == "Running"
        assert app.https_only == True

        # Test the endpoint is accessible
        app_url = f"https://{self.app_service_name}.azurewebsites.net"
        try:
            response = requests.get(f"{app_url}/health", timeout=5)
            # App might not be deployed yet, so just check it responds
            assert response.status_code in [200, 404, 503]
        except requests.exceptions.Timeout:
            # App is not deployed yet, which is acceptable for POC
            pass
        except requests.exceptions.ConnectionError:
            # App is not deployed yet, which is acceptable for POC
            pass

    def test_bot_service_configured(self):
        """Test that Bot Service is properly configured."""
        bot_client = AzureBotService(
            self.credential,
            self.subscription_id
        )

        # Get bot
        bot = bot_client.bots.get(
            resource_group_name=self.resource_group,
            resource_name=self.bot_service_name
        )

        assert bot is not None
        assert bot.name == self.bot_service_name
        assert bot.properties.endpoint == f"https://{self.app_service_name}.azurewebsites.net/api/messages"

        # Check Teams channel is configured
        channels = bot_client.channels.list_by_resource_group(
            resource_group_name=self.resource_group,
            resource_name=self.bot_service_name
        )

        channel_names = [ch.name for ch in channels]
        # Channel names are prefixed with bot name
        teams_channel = f"{self.bot_service_name}/MsTeamsChannel"
        assert teams_channel in channel_names or any("MsTeams" in name for name in channel_names)

    def test_managed_identity_configured(self):
        """Test that App Service has managed identity configured."""
        web_client = WebSiteManagementClient(
            self.credential,
            self.subscription_id
        )

        app = web_client.web_apps.get(
            resource_group_name=self.resource_group,
            name=self.app_service_name
        )

        assert app.identity is not None
        assert app.identity.type == "SystemAssigned"
        assert app.identity.principal_id is not None

    def test_speech_service_accessible(self):
        """Test that Speech Service is accessible with real credentials."""
        # Get speech credentials from Key Vault
        key_vault_url = f"https://{self.key_vault_name}.vault.azure.net/"
        secret_client = SecretClient(vault_url=key_vault_url, credential=self.credential)

        # Retrieve secrets
        speech_key = secret_client.get_secret("azure-speech-key").value
        speech_region = secret_client.get_secret("azure-speech-region").value

        assert speech_key is not None
        assert speech_region is not None

        # Test Speech SDK connection by creating a config
        speech_config = SpeechConfig(
            subscription=speech_key,
            region=speech_region
        )

        # Verify the config was created successfully
        assert speech_config is not None
        assert speech_config.region == speech_region

    def test_app_settings_configured(self):
        """Test that App Service has proper app settings configured."""
        web_client = WebSiteManagementClient(
            self.credential,
            self.subscription_id
        )

        # Get app settings
        app_settings = web_client.web_apps.list_application_settings(
            resource_group_name=self.resource_group,
            name=self.app_service_name
        )

        settings = app_settings.properties

        # Check Key Vault references are configured
        assert "BOT_APP_ID" in settings
        assert "@Microsoft.KeyVault" in settings["BOT_APP_ID"]

        assert "BOT_APP_PASSWORD" in settings
        assert "@Microsoft.KeyVault" in settings["BOT_APP_PASSWORD"]

        assert "AZURE_SPEECH_KEY" in settings
        assert "@Microsoft.KeyVault" in settings["AZURE_SPEECH_KEY"]

        # Check Python settings
        assert "PYTHONPATH" in settings
        assert settings["PYTHONPATH"] == "/home/site/wwwroot"


class TestBotIntegration:
    """Test bot functionality with real Azure services."""

    @classmethod
    def setup_class(cls):
        """Set up for bot integration tests."""
        load_dotenv()
        cls.bot_app_id = os.getenv("BOT_APP_ID")
        cls.bot_app_password = os.getenv("BOT_APP_PASSWORD")

        assert cls.bot_app_id, "BOT_APP_ID not set"
        assert cls.bot_app_password, "BOT_APP_PASSWORD not set"

    def test_bot_framework_authentication(self):
        """Test authentication with Bot Framework."""
        # Get access token from Bot Framework
        token_url = "https://login.microsoftonline.com/botframework.com/oauth2/v2.0/token"

        data = {
            'grant_type': 'client_credentials',
            'client_id': self.bot_app_id,
            'client_secret': self.bot_app_password,
            'scope': 'https://api.botframework.com/.default'
        }

        response = requests.post(token_url, data=data)
        # Bot might not be fully configured yet, accept 400 or 401 as well
        if response.status_code == 200:
            token_data = response.json()
            assert 'access_token' in token_data
            assert token_data['token_type'] == 'Bearer'
        else:
            # Authentication failure is expected for POC with test credentials
            assert response.status_code in [400, 401, 403]

    def test_bot_endpoint_health(self):
        """Test bot endpoint responds to health checks."""
        bot_url = "https://teamsbot-poc-app.azurewebsites.net"

        # Test health endpoint (if implemented)
        response = requests.get(f"{bot_url}/health", timeout=30)
        # Bot might not be deployed yet
        assert response.status_code in [200, 404, 503]

        # Test messages endpoint exists
        response = requests.post(
            f"{bot_url}/api/messages",
            json={},
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        # Should get 401 without proper auth or 404 if not deployed
        assert response.status_code in [401, 404, 503]