"""Bitrix24 интеграции."""
from .create_deal import Bitrix24CreateDealIntegration
#from .update_contact import Bitrix24UpdateContactIntegration
#from .create_contact import Bitrix24CreateContactIntegration
#from .get_deal import Bitrix24GetDealIntegration
#from .get_activity import Bitrix24GetActivityIntegration
#from .get_contact import Bitrix24GetContactIntegration
#from .create_company import Bitrix24CreateCompanyIntegration
#from .update_deal import Bitrix24UpdateDealIntegration
from app.integrations.registry import registry

# Регистрация интеграций
#registry.register(Bitrix24CreateDealIntegration())
#registry.register(Bitrix24CreateContactIntegration())
registry.register(Bitrix24CreateDealIntegration)
# #registry.register(Bitrix24UpdateDealIntegration())
# registry.register(Bitrix24UpdateContactIntegration())
# registry.register(Bitrix24GetActivityIntegration())
# registry.register(Bitrix24GetContactIntegration())
# registry.register(Bitrix24CreateCompanyIntegration())