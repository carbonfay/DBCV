from app.integrations.registry import registry

from .get_atc_code_rxnav import MedicineGetATCCodeIntegration

# Register only the ATC code integration in this branch
registry.register(MedicineGetATCCodeIntegration())

