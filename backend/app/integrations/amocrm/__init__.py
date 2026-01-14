from .create_contact import AmoCrmCreateContactIntegration
from .update_contact import AmoCrmUpdateContactIntegration
from .get_pipeline import AmoCrmGetPipelineIntegration
from .get_status import AmoCrmGetStatusIntegration
from app.integrations.registry import registry

# Register integrations
registry.register(AmoCrmCreateContactIntegration())
registry.register(AmoCrmUpdateContactIntegration())
registry.register(AmoCrmGetPipelineIntegration())
registry.register(AmoCrmGetStatusIntegration())
