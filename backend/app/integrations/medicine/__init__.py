"""Package for Medicine-related integration modules."""
from .get_icd10 import MedicineGetIcd10Integration
from app.integrations.registry import registry

__all__ = ["MedicineGetIcd10Integration"]

# Register integration on import so it's available to the platform
try:
	registry.register(MedicineGetIcd10Integration())
except Exception:
	# Don't fail import if registration fails
	pass
