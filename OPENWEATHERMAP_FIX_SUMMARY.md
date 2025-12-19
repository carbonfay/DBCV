# Исправление интеграции OpenWeatherMap Get Daily Forecast

## Проблема
При вводе координат с запятой (например, `55,7558`) в веб-интерфейс получалась ошибка валидации:
```
Please enter a valid value. The two nearest valid values are 55 and 56.
```

Однако через CLI скрипт `test_openweathermap_integration.sh` (с точкой `55.7558`) всё работало корректно.

## Причина
1. **Бэкэнд**: Тип поля в schema был `"number"` (принимал только числа), не поддерживал `"string"`
2. **Фронтенд**: Компонент `IntegrationConfigModal.vue` не обрабатывал типы как массивы `["number", "string"]`, которые JSON Schema поддерживает

## Решение

### 1. Обновлён бэкэнд (`backend/app/integrations/weather/openweathermap_daily_forecast.py`)

**Изменения в config_schema:**
```python
"latitude": {
    "type": ["number", "string"],  # Теперь принимает оба типа
    "description": "... Комма (,) будет автоматически заменена на точку (.)"
}
```

**Добавлено в `execute()` - парсинг координат:**
```python
# Поддерживаем строковые значения с запятой, например "55,7558"
if isinstance(latitude, str):
    latitude = latitude.strip().replace(',', '.')
if isinstance(longitude, str):
    longitude = longitude.strip().replace(',', '.')

latitude = float(latitude)
longitude = float(longitude)
```

### 2. Обновлён фронтенд (`DBCV_Builder/frontend/app/src/components/modals/IntegrationConfigModal.vue`)

**Добавлена helper функция:**
```typescript
const isFieldType = (fieldType: any, checkType: string): boolean => {
  if (Array.isArray(fieldType)) {
    return fieldType.includes(checkType);
  }
  return fieldType === checkType;
};
```

**Обновлены все проверки типов:**
- `v-if="field.type === 'string'"` → `v-if="isFieldType(field.type, 'string')"`
- `v-else-if="field.type === 'number'"` → `v-else-if="isFieldType(field.type, 'number')"`
- И т.д. для всех типов

**Добавлена функция для приведения типов:**
```typescript
const coerceNumericField = (key: string) => {
  const value = formData.value[key];
  if (typeof value === 'string') {
    const normalized = value.trim().replace(',', '.');
    try {
      const numValue = parseFloat(normalized);
      if (!isNaN(numValue)) {
        formData.value[field.key] = numValue;
      }
    } catch (e) {}
  }
};
```

Вызывается на `@blur` числовых полей.

## Результат

Теперь можно использовать оба формата:
- ✅ `55.7558` (точка — English format)
- ✅ `55,7558` (запятая — Russian/European format)

Оба будут автоматически преобразованы в число и отправлены на бэкэнд.

## Файлы, изменённые:
1. `backend/app/integrations/weather/openweathermap_daily_forecast.py` — бэкэнд парсинг
2. `DBCV_Builder/frontend/app/src/components/modals/IntegrationConfigModal.vue` — фронтенд рендеринг

## Как проверить:
1. Перезапустите DBCV_Builder фронтенд (rebuild)
2. В веб-интерфейсе введите `55,7558` для Latitude
3. Должно приняться без ошибок валидации
