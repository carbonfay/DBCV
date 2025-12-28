# 📘 Шаблон для создания новой интеграции DBCV

## 🎯 Быстрый старт

1. **Скопируйте шаблон**: `backend/app/integrations/_template.py` → `backend/app/integrations/{service}/{action}.py`
2. **Заполните плейсхолдеры** согласно инструкциям ниже
3. **Зарегистрируйте интеграцию** в `backend/app/integrations/{service}/__init__.py`
4. **Добавьте импорт** в `backend/app/integrations/__init__.py`

---

## 📝 Пример заполнения шаблона

### Пример 1: OpenAI Generate Text

**Файл**: `backend/app/integrations/openai/generate_text.py`

```python
"""OpenAI Generate Text интеграция используя openai библиотеку."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None


class OpenAIGenerateTextIntegration(BaseIntegration):
    """Интеграция для генерации текста через OpenAI GPT."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="openai_generate_text",
            version="1.0.0",
            name="OpenAI Generate Text",
            description="Генерация текста через OpenAI GPT API",
            category="ai",
            icon_s3_key="icons/integrations/openai.svg",
            color="#10a37f",
            config_schema={
                "type": "object",
                "required": ["prompt"],
                "properties": {
                    "prompt": {
                        "type": "string",
                        "title": "Prompt",
                        "description": "Текст запроса для генерации"
                    },
                    "model": {
                        "type": "string",
                        "title": "Model",
                        "enum": ["gpt-4", "gpt-3.5-turbo"],
                        "default": "gpt-3.5-turbo"
                    },
                    "max_tokens": {
                        "type": "number",
                        "title": "Max Tokens",
                        "default": 1000
                    }
                }
            },
            credentials_provider="openai",
            credentials_strategy="api_key",
            library_name="openai>=1.0.0" if OPENAI_AVAILABLE else None,
            examples=[
                {
                    "title": "Простая генерация текста",
                    "config": {
                        "prompt": "Расскажи о Python",
                        "model": "gpt-3.5-turbo"
                    }
                }
            ]
        )
    
    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger
    ) -> Dict[str, Any]:
        if not OPENAI_AVAILABLE:
            await logger.error("openai library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "openai library is not installed"
                }
            }
        
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="openai",
            strategy="api_key"
        )
        
        if not creds:
            await logger.error("OpenAI credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "OpenAI api_key not found in credentials"
                }
            }
        
        payload = creds.get("payload", {}) or creds
        api_key = payload.get("api_key") or payload.get("token")
        
        if not api_key:
            await logger.error(f"api_key not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "api_key not found in credentials"
                }
            }
        
        prompt = config.get("prompt")
        model = config.get("model", "gpt-3.5-turbo")
        max_tokens = config.get("max_tokens", 1000)
        
        if not prompt:
            await logger.error("prompt is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "prompt is required"
                }
            }
        
        try:
            client = OpenAI(api_key=api_key)
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens
            )
            
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "text": response.choices[0].message.content,
                        "model": response.model,
                        "usage": {
                            "prompt_tokens": response.usage.prompt_tokens,
                            "completion_tokens": response.usage.completion_tokens,
                            "total_tokens": response.usage.total_tokens
                        }
                    }
                }
            }
        except Exception as e:
            await logger.error(f"OpenAI error: {e}")
            error_code = 500
            if hasattr(e, 'status_code'):
                error_code = e.status_code
            
            return {
                "response": {
                    "ok": False,
                    "error_code": error_code,
                    "description": str(e)
                }
            }
```

---

### Пример 2: Stripe Create Payment

**Файл**: `backend/app/integrations/stripe/create_payment.py`

```python
"""Stripe Create Payment интеграция используя stripe библиотеку."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    stripe = None


class StripeCreatePaymentIntegration(BaseIntegration):
    """Интеграция для создания платежа через Stripe."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="stripe_create_payment",
            version="1.0.0",
            name="Stripe Create Payment",
            description="Создание платежа через Stripe Payment Intent API",
            category="payments",
            icon_s3_key="icons/integrations/stripe.svg",
            color="#635bff",
            config_schema={
                "type": "object",
                "required": ["amount", "currency"],
                "properties": {
                    "amount": {
                        "type": "number",
                        "title": "Amount",
                        "description": "Сумма платежа в центах (например, 1000 = $10.00)"
                    },
                    "currency": {
                        "type": "string",
                        "title": "Currency",
                        "enum": ["usd", "eur", "rub"],
                        "default": "usd"
                    },
                    "description": {
                        "type": "string",
                        "title": "Description",
                        "description": "Описание платежа"
                    }
                }
            },
            credentials_provider="stripe",
            credentials_strategy="api_key",
            library_name="stripe>=7.0.0" if STRIPE_AVAILABLE else None,
            examples=[
                {
                    "title": "Создать платеж на $10",
                    "config": {
                        "amount": 1000,
                        "currency": "usd",
                        "description": "Payment for service"
                    }
                }
            ]
        )
    
    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger
    ) -> Dict[str, Any]:
        if not STRIPE_AVAILABLE:
            await logger.error("stripe library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "stripe library is not installed"
                }
            }
        
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="stripe",
            strategy="api_key"
        )
        
        if not creds:
            await logger.error("Stripe credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Stripe secret_key not found in credentials"
                }
            }
        
        payload = creds.get("payload", {}) or creds
        secret_key = payload.get("secret_key") or payload.get("api_key")
        
        if not secret_key:
            await logger.error(f"secret_key not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "secret_key not found in credentials"
                }
            }
        
        amount = config.get("amount")
        currency = config.get("currency", "usd")
        description = config.get("description")
        
        if not amount:
            await logger.error("amount is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "amount is required"
                }
            }
        
        try:
            stripe.api_key = secret_key
            
            # Создаем Payment Intent
            payment_intent = stripe.PaymentIntent.create(
                amount=int(amount),
                currency=currency,
                description=description
            )
            
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "id": payment_intent.id,
                        "status": payment_intent.status,
                        "amount": payment_intent.amount,
                        "currency": payment_intent.currency,
                        "client_secret": payment_intent.client_secret
                    }
                }
            }
        except stripe.error.StripeError as e:
            await logger.error(f"Stripe error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": e.http_status if hasattr(e, 'http_status') else 500,
                    "description": str(e)
                }
            }
        except Exception as e:
            await logger.error(f"Unexpected error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }
```

---

## 🔧 Регистрация интеграции

### 1. Создайте `__init__.py` для сервиса

**Файл**: `backend/app/integrations/{service}/__init__.py`

```python
"""{Service} интеграции."""
from .{action} import {Service}{Action}Integration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register({Service}{Action}Integration())
```

**Пример для OpenAI**:

```python
"""OpenAI интеграции."""
from .generate_text import OpenAIGenerateTextIntegration
from app.integrations.registry import registry

registry.register(OpenAIGenerateTextIntegration())
```

### 2. Добавьте импорт в главный `__init__.py`

**Файл**: `backend/app/integrations/__init__.py`

Добавьте в конец файла:

```python
try:
    from app.integrations.{service} import *  # noqa: F401, F403
except ImportError:
    pass
```

**Пример**:

```python
try:
    from app.integrations.openai import *  # noqa: F401, F403
except ImportError:
    pass
```

---

## 📋 Чеклист создания интеграции

- [ ] Скопирован шаблон в `backend/app/integrations/{service}/{action}.py`
- [ ] Заменены все плейсхолдеры `{...}` на реальные значения
- [ ] Импортирована библиотека с обработкой `ImportError`
- [ ] Заполнены метаданные (`id`, `name`, `description`, `category`, и т.д.)
- [ ] Создан `config_schema` с JSON Schema для параметров
- [ ] Реализован метод `execute()` с получением credentials
- [ ] Реализовано использование библиотеки напрямую
- [ ] Добавлена обработка ошибок библиотеки
- [ ] Возвращается результат в формате `{"response": {"ok": True, "result": {...}}}`
- [ ] Создан файл `backend/app/integrations/{service}/__init__.py` с регистрацией
- [ ] Добавлен импорт в `backend/app/integrations/__init__.py`
- [ ] Добавлены примеры использования в `metadata.examples`
- [ ] Проверена работа интеграции

---

## 🎨 Категории интеграций

- `messaging` - Мессенджеры (Telegram, Discord, VK)
- `ai` - AI сервисы (OpenAI, YandexGPT)
- `storage` - Хранилища (Google Drive, Dropbox)
- `weather` - Погода (OpenWeatherMap, Яндекс.Погода)
- `maps` - Карты (Яндекс.Карты, Google Maps)
- `payments` - Платежи (ЮKassa, Stripe, PayPal)
- `crm` - CRM системы (Битрикс24, AmoCRM, HubSpot)
- `ecommerce` - E-commerce (Wildberries, Ozon)
- `education` - Образование (Moodle, Google Classroom)
- `medicine` - Медицина (Медицинские справочники)
- `news` - Новости (NewsAPI, Яндекс.Новости)
- `translation` - Переводы (Яндекс.Переводчик, Google Translate)

---

## 📚 Дополнительные ресурсы

- **Пример интеграции**: `backend/app/integrations/telegram/send_message.py`
- **Безопасные библиотеки**: `backend/app/integrations/SAFE_LIBRARIES.md`
- **Общая документация**: `backend/app/integrations/README.md`
- **Базовый класс**: `backend/app/integrations/base.py`

---

## ⚠️ Важные замечания

1. **Используйте библиотеки напрямую** - не делайте HTTP запросы через `httpx`, если есть официальная библиотека
2. **Обрабатывайте ошибки** - всегда обрабатывайте исключения библиотеки
3. **Проверяйте credentials** - всегда проверяйте наличие credentials перед использованием
4. **Логируйте ошибки** - используйте `logger.error()` для записи ошибок
5. **Возвращайте правильный формат** - всегда возвращайте `{"response": {"ok": True/False, ...}}`
6. **Используйте безопасные библиотеки** - см. `SAFE_LIBRARIES.md` для списка проверенных библиотек










