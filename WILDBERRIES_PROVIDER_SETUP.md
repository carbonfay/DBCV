# Добавление Wildberries провайдера

## Что было сделано

Создан новый провайдер **Wildberries** для управления API ключами маркетплейса.

### Файлы

- ✅ `backend/app/auth/providers/wildberries_provider.py` - Новый провайдер
- ✅ `backend/app/auth/service.py` - Обновлен для регистрации провайдера

### Структура провайдера

```python
class WildberriesProvider:
    """Провайдер для Wildberries API ключей."""
    
    async def ensure(...) -> AccessToken:
        # Получает API ключ из payload
        # Возвращает AccessToken с Bearer токеном
    
    def apply_headers(headers, token, hints):
        # Добавляет "Authorization: Bearer {api_token}" в headers
```

## Как использовать

### 1. В интеграции

```python
# Метаданные интеграции
credentials_provider="wildberries"
credentials_strategy="api_key"

# В методе execute
creds = await credentials_resolver.get_default_for(
    bot_id=bot_id,
    provider="wildberries",
    strategy="api_key"
)

# Получить API токен
payload = creds.get("payload", {})
api_token = payload.get("api_token")  # или api_key, token
```

### 2. Добавление credentials в БД

Нужно добавить credentials для бота с:

```json
{
    "provider": "wildberries",
    "strategy": "api_key",
    "payload": {
        "api_token": "your_api_key_here"
    }
}
```

### 3. В боте DBCV

Когда пользователь добавляет интеграцию Wildberries:

1. Система просит ввести API ключ
2. Сохраняет в БД с provider="wildberries", strategy="api_key"
3. При выполнении интеграции система:
   - Получает credentials через CredentialsResolver
   - Пропускает через WildberriesProvider.ensure()
   - Применяет заголовок "Authorization: Bearer {token}"
   - Выполняет HTTP запрос к Wildberries API

## Совместимость

Провайдер поддерживает несколько имен для API ключа:
- `api_token` - основное имя
- `api_key` - для обратной совместимости
- `token` - альтернативное имя

## Тестирование

Все тесты интеграций уже содержат проверку:
```python
assert metadata.credentials_provider == "wildberries"
```

Тесты используют моки и не требуют реальных credentials.

## Структура payload

При добавлении credentials в БД используйте следующую структуру:

```python
{
    "provider": "wildberries",          # Указанный провайдер
    "strategy": "api_key",              # Стратегия
    "name": "My Wildberries Store",     # Имя (опционально)
    "is_default": True,                 # Использовать по умолчанию
    "payload": {                        # Зашифрованные данные
        "api_token": "eyJ..."           # Ваш API ключ от Wildberries
    }
}
```

## API Reference

### AccessToken (возвращаемый результат)

```python
AccessToken(
    token_type: str = "Bearer",         # Тип токена
    access_token: str = "api_key",      # Сам токен
    expires_at: float = unix_timestamp   # Время истечения (год для API ключей)
)
```

### Headers при использовании

```python
{
    "Authorization": "Bearer eyJ..."
}
```

## Безопасность

- API ключ хранится в БД в зашифрованном виде
- При использовании провайдер автоматически добавляет Bearer схему
- Кешируется в памяти для оптимизации (1 год TTL для API ключей)

## Следующие шаги

1. ✅ Провайдер создан
2. ✅ Зарегистрирован в AuthService
3. ✅ Интеграции могут использовать provider="wildberries"
4. ⏳ Нужно добавить credentials в БД через админку DBCV
5. ⏳ Протестировать реальные запросы к Wildberries API
