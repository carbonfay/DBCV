"""
AmoCRM Update Lead integration for DBCV platform.
"""
from typing import Any, Dict, Optional, List

from app.integrations.base import BaseIntegration
from app.integrations.exceptions import IntegrationException
from app.services.credentials_resolver import CredentialsResolver
from amocrm_api import AmoOAuthClient


class AmoCRMUpdateLeadIntegration(BaseIntegration):
    """
    Integration for updating a lead (deal) in AmoCRM.
    """

    id = "amocrm_update_lead"
    version = "1.0.0"
    category = "crm"
    icon_s3_key = "icons/integrations/amocrm.svg"
    config_schema = {
        "type": "object",
        "properties": {
            "lead_id": {
                "type": "integer",
                "description": "ID of the lead to update",
            },
            "name": {
                "type": "string",
                "description": "New name of the lead",
            },
            "status_id": {
                "type": "integer",
                "description": "ID of the new status (pipeline stage)",
            },
            "price": {
                "type": "number",
                "description": "New price of the lead",
            },
            "responsible_user_id": {
                "type": "integer",
                "description": "ID of the new responsible user",
            },
            "pipeline_id": {
                "type": "integer",
                "description": "ID of the new pipeline (if moving lead between pipelines)",
            },
            "date_close": {
                "type": "integer",
                "description": "Unix timestamp of the closing date",
            },
            "loss_reason_id": {
                "type": "integer",
                "description": "ID of the loss reason (if lead is lost)",
            },
            "custom_fields_values": {
                "type": "array",
                "description": "Custom fields values",
                "items": {
                    "type": "object",
                    "properties": {
                        "field_id": {"type": "integer"},
                        "values": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "value": {"type": "string"},
                                },
                            },
                        },
                    },
                },
            },
            "tags": {
                "type": "array",
                "description": "Tags to attach to the lead",
                "items": {"type": "string"},
            },
        },
        "required": ["lead_id"],
    }
    credentials_provider = "amocrm"
    credentials_strategy = "oauth"
    library_name = "amocrm-api-wrapper"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the integration with configuration.

        :param config: Integration configuration parameters.
        """
        super().__init__(config)

    def execute(self, credentials_resolver: CredentialsResolver) -> Dict[str, Any]:
        """
        Execute the lead update.

        :param credentials_resolver: Resolver for obtaining credentials.
        :return: Result of the operation.
        :raises IntegrationException: If update fails.
        """
        try:
            # Retrieve credentials for AmoCRM
            credentials = credentials_resolver.get_default_for("amocrm")
            required_keys = ["access_token", "refresh_token", "subdomain", "client_id", "client_secret", "redirect_uri"]
            for key in required_keys:
                if key not in credentials or not credentials[key]:
                    raise IntegrationException(f"Missing required credential '{key}' for AmoCRM")

            # Initialize AmoCRM OAuth client
            client = AmoOAuthClient(
                access_token=credentials["access_token"],
                refresh_token=credentials["refresh_token"],
                crm_url=f"https://{credentials['subdomain']}.amocrm.ru",
                client_id=credentials["client_id"],
                client_secret=credentials["client_secret"],
                redirect_uri=credentials["redirect_uri"],
            )

            # Prepare lead data for update
            lead_data = {
                "id": self.config["lead_id"],
            }

            # Add optional fields if present
            optional_fields = [
                "name", "status_id", "price", "responsible_user_id",
                "pipeline_id", "date_close", "loss_reason_id"
            ]
            for field in optional_fields:
                if field in self.config and self.config[field] is not None:
                    lead_data[field] = self.config[field]

            # Add custom fields if present
            if "custom_fields_values" in self.config and self.config["custom_fields_values"]:
                lead_data["custom_fields_values"] = self.config["custom_fields_values"]

            # Add tags if present
            if "tags" in self.config and self.config["tags"]:
                lead_data["_embedded"] = {"tags": [{"name": tag} for tag in self.config["tags"]]}

            # Perform the update
            result = client.update_leads([lead_data])

            # Check if update was successful
            if not result:
                raise IntegrationException("Failed to update lead: Empty response from API")

            # Return success response
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "updated": True,
                        "lead_id": self.config["lead_id"],
                        "response": result,
                    },
                }
            }

        except Exception as e:
            # Log the error and raise an IntegrationException
            self.logger.error(f"Failed to update lead in AmoCRM: {str(e)}")
            raise IntegrationException(f"Failed to update lead: {str(e)}") from e

    def get_metadata(self) -> Dict[str, Any]:
        """
        Return integration metadata.

        :return: Metadata dictionary.
        """
        return {
            "id": self.id,
            "version": self.version,
            "category": self.category,
            "icon_s3_key": self.icon_s3_key,
            "config_schema": self.config_schema,
            "credentials_provider": self.credentials_provider,
            "credentials_strategy": self.credentials_strategy,
            "library_name": self.library_name,
        }