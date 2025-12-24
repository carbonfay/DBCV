## Описание изменений

Добавлен файл фикстуры для тестов `receipt_create.json`, содержащий пример ответа API YooKassa для создания чека. Используется в тестах интеграции `youkassa_create_receipt` и демонстрациях без реальных credentials.

## Тип изменений

- [ ] Исправление бага
- [ ] Новая функция
- [ ] Изменение документации
- [ ] Рефакторинг кода
- [x] Тесты
- [ ] Другое (опишите): фикстуры для тестов

## Чеклист

- [x] Код соответствует стилю проекта
- [x] Я проверил свой код
- [x] Я добавил комментарии к коду, особенно в сложных местах (не применимо для fixtures)
- [ ] Я обновил документацию (если необходимо)
- [x] Мои изменения не генерируют новых предупреждений
- [x] Я добавил тесты, которые подтверждают мои исправления (тесты используют эту фикстуру)
- [x] Новые и существующие тесты проходят локально

## Как протестировать

1. Переключиться на ветку `feat/youkassa-receipt-create`:
   ```bash
   git checkout feat/youkassa-receipt-create
   ```
2. Убедиться, что фикстура присутствует: `backend/app/tests/fixtures/youkassa/receipt_create.json`.
3. Запустить соответствующий тест:
   ```bash
   python -m pytest backend/app/tests/integrations/test_yookassa_create_receipt.py -q
   ```
4. Или использовать демонстрационный скрипт:
   ```bash
   python scripts/test_yookassa_connection.py
   ```

## Дополнительная информация

Фикстура отражает успешный ответ от `Receipt.create`. Тесты и логика интеграции находятся в PR `feat/youkassa-tests-and-scripts`.

---

## Live run update
- Попытки создать standalone-чек (без привязки к `payment_id`) завершились ошибками в live-прогонах — см. `scripts/youkassa_create_standalone_results.json`.
- Ошибки, с которыми столкнулись: отсутствие `settlements`/`customer` → добавлены минимальные поля; требование `Idempotence-Key` → добавлено; далее — `parameter: type` не принимается для standalone-формы.
- Вывод: для надежного создания чеков используйте **реальные payment_id** (POST /receipts с `payment_id`) или уточните у YooKassa корректный payload для standalone-чеков по вашей учетной записи.

