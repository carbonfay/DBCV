"""Битрикс24 интеграции."""
from .B_Create_Cp import Bitrix24CreateCompanyIntegration
from app.integrations.registry import registry

registry.register(Bitrix24CreateCompanyIntegration())