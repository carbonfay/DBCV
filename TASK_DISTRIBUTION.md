# Распределение задач по интеграциям

Этот документ содержит полный список интеграций для реализации и таблицу для распределения задач между студентами.

## Быстрая навигация

- **[Документация API по категориям](#документация-api-по-категориям)** — ссылки на официальную документацию всех API
- **[Полный список интеграций](#полный-список-интеграций)** — таблицы с задачами для студентов
- **[Пресеты для реализации](#пресеты-для-реализации)** — готовые заготовки для типовых шагов


## Легенда статусов

- ⬜ - Не начато
- 🔄 - В работе
- ✅ - Завершено
- ❌ - Отменено

## Легенда сложности

- **Низкая**: 2-3 дня (простые API запросы, базовые операции)
- **Средняя**: 3-5 дней (OAuth, сложные запросы, обработка файлов)
- **Высокая**: 5-7 дней (сложная логика, множественные шаги, интеграция с несколькими API)

---

## Инструкции для менеджера

### Как заполнять таблицу

1. Когда студент берет задачу:
   - Указать имя студента в колонке "Студент"
   - Изменить статус на "🔄 В работе"
   - Записать дату начала

2. Когда задача завершена:
   - Изменить статус на "✅ Завершено"
   - Записать дату завершения
   - Проверить наличие MR и видео

### Приоритеты распределения

1. **Начать с простых**: Telegram, OpenWeatherMap (низкая сложность)
2. **Затем средние**: Платежи, CRM (средняя сложность)
3. **Сложные в конце**: OAuth интеграции, сложные платежи (высокая сложность)

### Группировка задач

Студенты могут взять несколько интеграций одной категории для более эффективной работы.

---

## Полезные ссылки

- **[Документация GitVerse Wiki](https://gitverse.ru/carbonfay/DBCV/wiki/WIKIDBCV1-12)** — полная документация проекта на GitVerse
- [STUDENT_GUIDE.md](./STUDENT_GUIDE.md) - полное руководство для студентов со всеми шагами работы
- [STUDENT_AI_PROMPT.md](./STUDENT_AI_PROMPT.md) - примеры промптов
- [INSTALLATION.md](./INSTALLATION.md) - установка окружения

---

## Статистика

- **Всего интеграций**: 225
- **Категорий**: 11
- **Оценка времени на интеграцию**: 3-5 дней

---

## Документация API по категориям

Перед началом работы с интеграцией обязательно ознакомьтесь с официальной документацией API соответствующего сервиса.

### Категория: Погода

#### OpenWeatherMap
- **Официальная документация**: [OpenWeatherMap API Documentation](https://openweathermap.org/api)
- **Текущая погода**: [Current Weather Data](https://openweathermap.org/current)
- **Прогноз**: [5 Day / 3 Hour Forecast](https://openweathermap.org/forecast5)
- **One Call API**: [One Call API 3.0](https://openweathermap.org/api/one-call-3)

#### Яндекс.Погода
- **Официальная документация**: [Яндекс.Погода API](https://yandex.ru/dev/weather/doc/dg/concepts/about.html)
- **Информаторы**: [Информаторы погоды](https://yandex.ru/dev/weather/doc/dg/concepts/informers.html)
- **Прогноз**: [Прогноз погоды](https://yandex.ru/dev/weather/doc/dg/concepts/forecast.html)

---

### Категория: Карты

#### Яндекс.Карты
- **Официальная документация**: [Яндекс.Карты API](https://yandex.ru/dev/maps/doc/ru/)
- **HTTP Геокодер**: [HTTP Геокодер](https://yandex.ru/dev/maps/geocoder/)
- **JavaScript API**: [JavaScript API и HTTP Геокодер](https://yandex.ru/dev/maps/jsapi/doc/2.1/quick-start/index.html)
- **Маршрутизация**: [Построение маршрутов](https://yandex.ru/dev/maps/jsapi/doc/2.1/dg/concepts/route.html)

#### Google Maps
- **Официальная документация**: [Google Maps Platform](https://developers.google.com/maps/documentation)
- **Geocoding API**: [Geocoding API](https://developers.google.com/maps/documentation/geocoding)
- **Directions API**: [Directions API](https://developers.google.com/maps/documentation/directions)
- **Places API**: [Places API](https://developers.google.com/maps/documentation/places)

---

### Категория: Платежи

#### ЮKassa (Яндекс.Касса)
- **Официальная документация**: [ЮKassa API](https://yookassa.ru/developers/api)
- **Создание платежа**: [Создание платежа](https://yookassa.ru/developers/api#create_payment)
- **Возвраты**: [Возвраты](https://yookassa.ru/developers/api#refund)
- **Чеки**: [Чеки](https://yookassa.ru/developers/api#receipt)

#### Stripe
- **Официальная документация**: [Stripe API Reference](https://stripe.com/docs/api)
- **Payment Intents**: [Payment Intents API](https://stripe.com/docs/api/payment_intents)
- **Charges**: [Charges API](https://stripe.com/docs/api/charges)
- **Customers**: [Customers API](https://stripe.com/docs/api/customers)

#### PayPal
- **Официальная документация**: [PayPal API](https://developer.paypal.com/docs/api/overview/)
- **Orders API**: [Orders API v2](https://developer.paypal.com/docs/api/orders/v2/)
- **Payments API**: [Payments API](https://developer.paypal.com/docs/api/payments/v2/)
- **Subscriptions API**: [Subscriptions API](https://developer.paypal.com/docs/api/subscriptions/v1/)

---

### Категория: Социальные сети

#### Telegram Bot API
- **Официальная документация**: [Telegram Bot API](https://core.telegram.org/bots/api)
- **Методы бота**: [Available Methods](https://core.telegram.org/bots/api#available-methods)
- **Типы данных**: [Available Types](https://core.telegram.org/bots/api#available-types)

#### VK API
- **Официальная документация**: [VK API](https://dev.vk.com/ru/api)
- **Методы API**: [Методы API](https://dev.vk.com/ru/method)
- **Авторизация**: [Авторизация пользователей](https://dev.vk.com/ru/api/access-token/authcode-flow-user)

---

### Категория: CRM

#### Битрикс24
- **Официальная документация**: [REST API Битрикс24](https://dev.1c-bitrix.ru/rest_help/)
- **CRM**: [CRM REST API](https://dev.1c-bitrix.ru/rest_help/crm/index.php)
- **Задачи**: [Задачи REST API](https://dev.1c-bitrix.ru/rest_help/tasks/index.php)
- **Сделки**: [Сделки REST API](https://dev.1c-bitrix.ru/rest_help/crm/crm_deal/index.php)

#### AmoCRM
- **Официальная документация**: [AmoCRM API v4](https://www.amocrm.ru/developers/content/api/overview)
- **Контакты**: [Контакты API](https://www.amocrm.ru/developers/content/api/contacts)
- **Сделки**: [Сделки API](https://www.amocrm.ru/developers/content/api/leads)
- **Задачи**: [Задачи API](https://www.amocrm.ru/developers/content/api/tasks)

#### HubSpot
- **Официальная документация**: [HubSpot API](https://developers.hubspot.com/docs/api/overview)
- **CRM API**: [CRM API](https://developers.hubspot.com/docs/api/crm/understanding-the-crm)
- **Contacts API**: [Contacts API](https://developers.hubspot.com/docs/api/crm/contacts)
- **Deals API**: [Deals API](https://developers.hubspot.com/docs/api/crm/deals)

---

### Категория: E-commerce
#### Ozon API
#### Wildberries API
 - **Официальная документация**: [Wildberries API для поставщиков](https://openapi.wildberries.ru/)
 - **Контент**: [Контент API](https://openapi.wildberries.ru/content/api/v1/)
 - **Поставки**: [Поставки API](https://openapi.wildberries.ru/supplies/api/v1/)
 - **Аналитика**: [Аналитика API](https://openapi.wildberries.ru/analytics/api/v1/)
#### Ozon API

---

### Категория: Образование

#### Moodle API
- **Официальная документация**: [Moodle Web Services API](https://docs.moodle.org/dev/Web_services_API)
- **REST API**: [REST protocol](https://docs.moodle.org/dev/Web_services_API#REST_protocol)
- **Функции API**: [Available functions](https://docs.moodle.org/dev/Web_services_API_functions)

#### Google Classroom API
- **Официальная документация**: [Google Classroom API](https://developers.google.com/classroom)
- **Courses API**: [Courses API](https://developers.google.com/classroom/reference/rest/v1/courses)
- **CourseWork API**: [CourseWork API](https://developers.google.com/classroom/reference/rest/v1/courses.courseWork)
- **Students API**: [Students API](https://developers.google.com/classroom/reference/rest/v1/courses.students)

---

### Категория: Медицина

#### Медицинские справочники API
- **Рекомендация**: Используйте открытые медицинские API, такие как:
  - **FHIR**: [FHIR API](https://www.hl7.org/fhir/http.html)
  - **RxNorm**: [RxNorm API](https://www.nlm.nih.gov/research/umls/rxnorm/docs/rxnormrestfulapi.html)
  - **MedlinePlus**: [MedlinePlus API](https://medlineplus.gov/connect/service.html)

**Примечание**: Для российских медицинских API обратитесь к официальным источникам Минздрава и региональных систем здравоохранения.

---

### Категория: Новости

#### NewsAPI
- **Официальная документация**: [NewsAPI Documentation](https://newsapi.org/docs)
- **Top Headlines**: [Top Headlines Endpoint](https://newsapi.org/docs/endpoints/top-headlines)
- **Everything**: [Everything Endpoint](https://newsapi.org/docs/endpoints/everything)
- **Sources**: [Sources Endpoint](https://newsapi.org/docs/endpoints/sources)

#### Яндекс.Новости
- **Официальная документация**: [Яндекс.Новости API](https://yandex.ru/dev/news/doc/ru/)
- **Поиск новостей**: [Поиск новостей](https://yandex.ru/dev/news/doc/ru/concepts/search)

---

### Категория: Переводы

#### Яндекс.Переводчик
- **Официальная документация**: [Яндекс.Переводчик API](https://yandex.ru/dev/translate/doc/ru/)
- **Перевод текста**: [Перевод текста](https://yandex.ru/dev/translate/doc/ru/translate)
- **Определение языка**: [Определение языка](https://yandex.ru/dev/translate/doc/ru/detect)
- **Список языков**: [Список языков](https://yandex.ru/dev/translate/doc/ru/getLangs)

#### Google Translate API
- **Официальная документация**: [Google Cloud Translation API](https://cloud.google.com/translate/docs)
- **Translation API**: [Translation API v2](https://cloud.google.com/translate/docs/reference/rest/v2)
- **Advanced API**: [Advanced API v3](https://cloud.google.com/translate/docs/reference/rest/v3)

---

### Категория: Контроль версий

#### GitHub API
- **Официальная документация**: [GitHub REST API](https://docs.github.com/en/rest)
- **Issues API**: [Issues API](https://docs.github.com/en/rest/issues)
- **Pull Requests API**: [Pull Requests API](https://docs.github.com/en/rest/pulls)
- **Repositories API**: [Repositories API](https://docs.github.com/en/rest/repos)

#### GitVerse API (GitLab API)
- **Официальная документация**: [GitLab API](https://docs.gitlab.com/ee/api/)
- **Projects API**: [Projects API](https://docs.gitlab.com/ee/api/projects.html)
- **Issues API**: [Issues API](https://docs.gitlab.com/ee/api/issues.html)
- **Merge Requests API**: [Merge Requests API](https://docs.gitlab.com/ee/api/merge_requests.html)

**Примечание**: GitVerse использует API, совместимое с GitLab API v4.

---

**⚠️ Важно**: Ссылки на документацию API могут изменяться со временем. Если ссылка не работает, поищите актуальную документацию на официальном сайте сервиса. Все ссылки проверены на момент последнего обновления документа.

---

## Полный список интеграций

### Категория: Погода - ~15 интеграций

#### OpenWeatherMap (httpx) - 8 интеграций

| № | Интеграция | Файл | API Метод | Сложность | Статус | Студент |
|---|-----------|------|-----------|-----------|--------|---------|
| 1 | OpenWeatherMap Get Current Weather | `openweathermap/get_current.py` | `GET /data/2.5/weather` | Низкая | ⬜ | |
| 2 | OpenWeatherMap Get Forecast | `openweathermap/get_forecast.py` | `GET /data/2.5/forecast` | Низкая | ⬜ | |
| 3 | OpenWeatherMap Get Hourly Forecast | `openweathermap/get_hourly_forecast.py` | `GET /data/2.5/forecast/hourly` | Средняя | ⬜ | |
| 4 | OpenWeatherMap Get Daily Forecast | `openweathermap/get_daily_forecast.py` | `GET /data/2.5/forecast/daily` | Средняя | ⬜ | |
| 5 | OpenWeatherMap Get Weather History | `openweathermap/get_history.py` | `GET /data/2.5/onecall/timemachine` | Средняя | ⬜ | |
| 6 | OpenWeatherMap Get Weather Alerts | `openweathermap/get_alerts.py` | `GET /data/2.5/onecall` (alerts) | Средняя | ⬜ | |
| 7 | OpenWeatherMap Get Air Pollution | `openweathermap/get_air_pollution.py` | `GET /data/2.5/air_pollution` | Средняя | ⬜ | |
| 8 | OpenWeatherMap Get UV Index | `openweathermap/get_uv_index.py` | `GET /data/2.5/uvi` | Низкая | ⬜ | |

#### Яндекс.Погода (httpx) - 7 интеграций

| № | Интеграция | Файл | API Метод | Сложность | Статус | Студент |
|---|-----------|------|-----------|-----------|--------|---------|
| 9 | Yandex Weather Get Current | `yandex/weather_current.py` | `GET /v2/informers` | Низкая | ⬜ | |
| 10 | Yandex Weather Get Forecast | `yandex/weather_forecast.py` | `GET /v2/forecast` | Низкая | ⬜ | |
| 11 | Yandex Weather Get Hourly Forecast | `yandex/weather_hourly.py` | `GET /v2/forecast` (hourly) | Средняя | ⬜ | |
| 12 | Yandex Weather Get Daily Forecast | `yandex/weather_daily.py` | `GET /v2/forecast` (daily) | Средняя | ⬜ | |
| 13 | Yandex Weather Get Informers | `yandex/weather_informers.py` | `GET /v2/informers` | Средняя | ⬜ | |
| 14 | Yandex Weather Get Fact | `yandex/weather_fact.py` | `GET /v2/fact` | Низкая | ⬜ | |
| 15 | Yandex Weather Get Parts | `yandex/weather_parts.py` | `GET /v2/forecast` (parts) | Средняя | ⬜ | |

---

### Категория: Карты - ~20 интеграций

#### Яндекс.Карты (httpx) - 10 интеграций

| № | Интеграция | Файл | API Метод | Сложность | Статус | Студент |
|---|-----------|------|-----------|-----------|--------|---------|
| 16 | Yandex Maps Geocode | `yandex/maps_geocode.py` | `GET /1.x/?geocode=` | Низкая | ⬜ | |
| 17 | Yandex Maps Reverse Geocode | `yandex/maps_reverse_geocode.py` | `GET /1.x/?geocode=` (reverse) | Низкая | ⬜ | |
| 18 | Yandex Maps Route | `yandex/maps_route.py` | `GET /2.1/?routingMode=` | Средняя | ⬜ | |
| 19 | Yandex Maps Search | `yandex/maps_search.py` | `GET /search/?text=` | Средняя | ⬜ | |
| 20 | Yandex Maps Get Organization Info | `yandex/maps_organization.py` | `GET /search/?text=` (org) | Средняя | ⬜ | |
| 21 | Yandex Maps Get Address | `yandex/maps_address.py` | `GET /1.x/?geocode=` (address) | Низкая | ⬜ | |
| 22 | Yandex Maps Calculate Distance | `yandex/maps_distance.py` | `GET /2.1/?routingMode=` (distance) | Средняя | ⬜ | |
| 23 | Yandex Maps Get Static Map | `yandex/maps_static.py` | `GET /1.x/?ll=` (static) | Средняя | ⬜ | |
| 24 | Yandex Maps Suggest | `yandex/maps_suggest.py` | `GET /suggest/?text=` | Средняя | ⬜ | |
| 25 | Yandex Maps Get Timezone | `yandex/maps_timezone.py` | `GET /1.x/?geocode=` (timezone) | Низкая | ⬜ | |

#### Google Maps API (googlemaps>=4.10.0) - 10 интеграций

| № | Интеграция | Файл | API Метод | Сложность | Статус | Студент |
|---|-----------|------|-----------|-----------|--------|---------|
| 26 | Google Maps Geocode | `google/maps_geocode.py` | `GET /maps/api/geocode/json` | Низкая | ⬜ | |
| 27 | Google Maps Reverse Geocode | `google/maps_reverse_geocode.py` | `GET /maps/api/geocode/json` (latlng) | Низкая | ⬜ | |
| 28 | Google Maps Route | `google/maps_route.py` | `GET /maps/api/directions/json` | Средняя | ⬜ | |
| 29 | Google Maps Place Search | `google/maps_place_search.py` | `GET /maps/api/place/nearbysearch/json` | Средняя | ⬜ | |
| 30 | Google Maps Distance Matrix | `google/maps_distance_matrix.py` | `GET /maps/api/distancematrix/json` | Средняя | ⬜ | |
| 31 | Google Maps Get Place Details | `google/maps_place_details.py` | `GET /maps/api/place/details/json` | Средняя | ⬜ | |
| 32 | Google Maps Get Place Photos | `google/maps_place_photos.py` | `GET /maps/api/place/photo` | Средняя | ⬜ | |
| 33 | Google Maps Autocomplete | `google/maps_autocomplete.py` | `GET /maps/api/place/autocomplete/json` | Средняя | ⬜ | |
| 34 | Google Maps Get Directions | `google/maps_directions.py` | `GET /maps/api/directions/json` | Средняя | ⬜ | |
| 35 | Google Maps Get Elevation | `google/maps_elevation.py` | `GET /maps/api/elevation/json` | Низкая | ⬜ | |

---

### Категория: Платежи - ~30 интеграций

#### ЮKassa (yookassa>=2.3.0) - 10 интеграций

| № | Интеграция | Файл | API Метод | Сложность | Статус | Студент |
|---|-----------|------|-----------|-----------|--------|---------|
| 36 | YooKassa Create Payment | `yookassa/create_payment.py` | `POST /v3/payments` | Средняя | ⬜ | |
| 37 | YooKassa Get Payment | `yookassa/get_payment.py` | `GET /v3/payments/{payment_id}` | Низкая | ⬜ | |
| 38 | YooKassa Cancel Payment | `yookassa/cancel_payment.py` | `POST /v3/payments/{payment_id}/cancel` | Средняя | ⬜ | |
| 39 | YooKassa Refund | `yookassa/refund.py` | `POST /v3/refunds` | Средняя | ⬜ | |
| 40 | YooKassa Create Refund | `yookassa/create_refund.py` | `POST /v3/refunds` | Средняя | ⬜ | |
| 41 | YooKassa Get Refund | `yookassa/get_refund.py` | `GET /v3/refunds/{refund_id}` | Низкая | ⬜ | |
| 42 | YooKassa Capture Payment | `yookassa/capture_payment.py` | `POST /v3/payments/{payment_id}/capture` | Средняя | ⬜ | |
| 43 | YooKassa Create Receipt | `yookassa/create_receipt.py` | `POST /v3/receipts` | Высокая | ⬜ | |
| 44 | YooKassa Get Receipt | `yookassa/get_receipt.py` | `GET /v3/receipts/{receipt_id}` | Низкая | ⬜ | |
| 45 | YooKassa Get Payment List | `yookassa/get_payment_list.py` | `GET /v3/payments` | Средняя | ⬜ | |

#### Stripe (stripe>=7.0.0) - 10 интеграций

| № | Интеграция | Файл | API Метод | Сложность | Статус | Студент |
|---|-----------|------|-----------|-----------|--------|---------|
| 46 | Stripe Create Payment | `stripe/create_payment.py` | `POST /v1/charges` | Средняя | ⬜ | |
| 47 | Stripe Create Payment Intent | `stripe/create_payment_intent.py` | `POST /v1/payment_intents` | Средняя | ⬜ | |
| 48 | Stripe Get Payment | `stripe/get_payment.py` | `GET /v1/charges/{id}` | Низкая | ⬜ | |
| 49 | Stripe Refund | `stripe/refund.py` | `POST /v1/refunds` | Средняя | ⬜ | |
| 50 | Stripe Create Customer | `stripe/create_customer.py` | `POST /v1/customers` | Низкая | ⬜ | |
| 51 | Stripe Get Customer | `stripe/get_customer.py` | `GET /v1/customers/{id}` | Низкая | ⬜ | |
| 52 | Stripe Update Customer | `stripe/update_customer.py` | `POST /v1/customers/{id}` | Низкая | ⬜ | |
| 53 | Stripe Create Subscription | `stripe/create_subscription.py` | `POST /v1/subscriptions` | Высокая | ⬜ | |
| 54 | Stripe Cancel Subscription | `stripe/cancel_subscription.py` | `DELETE /v1/subscriptions/{id}` | Средняя | ⬜ | |
| 55 | Stripe Get Invoice | `stripe/get_invoice.py` | `GET /v1/invoices/{id}` | Низкая | ⬜ | |

#### PayPal (httpx) - 10 интеграций

| № | Интеграция | Файл | API Метод | Сложность | Статус | Студент |
|---|-----------|------|-----------|-----------|--------|---------|
| 56 | PayPal Create Order | `paypal/create_order.py` | `POST /v2/checkout/orders` | Средняя | ⬜ | |
| 57 | PayPal Capture Order | `paypal/capture_order.py` | `POST /v2/checkout/orders/{id}/capture` | Средняя | ⬜ | |
| 58 | PayPal Get Order | `paypal/get_order.py` | `GET /v2/checkout/orders/{id}` | Низкая | ⬜ | |
| 59 | PayPal Refund | `paypal/refund.py` | `POST /v2/payments/captures/{id}/refund` | Средняя | ⬜ | |
| 60 | PayPal Create Payout | `paypal/create_payout.py` | `POST /v1/payments/payouts` | Высокая | ⬜ | |
| 61 | PayPal Get Payout | `paypal/get_payout.py` | `GET /v1/payments/payouts/{id}` | Низкая | ⬜ | |
| 62 | PayPal Create Subscription | `paypal/create_subscription.py` | `POST /v1/billing/subscriptions` | Высокая | ⬜ | |
| 63 | PayPal Cancel Subscription | `paypal/cancel_subscription.py` | `POST /v1/billing/subscriptions/{id}/cancel` | Средняя | ⬜ | |
| 64 | PayPal Get Transaction | `paypal/get_transaction.py` | `GET /v1/reporting/transactions` | Низкая | ⬜ | |
| 65 | PayPal Verify Webhook | `paypal/verify_webhook.py` | `POST /v1/notifications/verify-webhook-signature` | Высокая | ⬜ | |

---

### Категория: Социальные сети - ~30 интеграций

#### Telegram Bot API (python-telegram-bot>=20.0) - 20 интеграций

| № | Интеграция | Файл | API Метод | Сложность | Статус | Студент |
|---|-----------|------|-----------|-----------|--------|---------|
| 66 | Telegram Get Updates | `telegram/get_updates.py` | `GET /bot{token}/getUpdates` | Низкая | ⬜ | |
| 67 | Telegram Send Message | `telegram/send_message.py` | `POST /bot{token}/sendMessage` | Низкая | ✅ | УЖЕ РЕАЛИЗОВАНО |
| 68 | Telegram Send Photo | `telegram/send_photo.py` | `POST /bot{token}/sendPhoto` | Низкая | ⬜ | |
| 69 | Telegram Send Document | `telegram/send_document.py` | `POST /bot{token}/sendDocument` | Низкая | ⬜ | |
| 70 | Telegram Send Video | `telegram/send_video.py` | `POST /bot{token}/sendVideo` | Низкая | ⬜ | |
| 71 | Telegram Send Audio | `telegram/send_audio.py` | `POST /bot{token}/sendAudio` | Низкая | ⬜ | |
| 72 | Telegram Send Voice | `telegram/send_voice.py` | `POST /bot{token}/sendVoice` | Низкая | ⬜ | |
| 73 | Telegram Send Location | `telegram/send_location.py` | `POST /bot{token}/sendLocation` | Низкая | ⬜ | |
| 74 | Telegram Edit Message | `telegram/edit_message.py` | `POST /bot{token}/editMessageText` | Низкая | ⬜ | |
| 75 | Telegram Delete Message | `telegram/delete_message.py` | `POST /bot{token}/deleteMessage` | Низкая | ⬜ | |
| 76 | Telegram Get Chat | `telegram/get_chat.py` | `GET /bot{token}/getChat` | Низкая | ⬜ | |
| 77 | Telegram Get User | `telegram/get_user.py` | `GET /bot{token}/getMe` | Низкая | ⬜ | |
| 78 | Telegram Forward Message | `telegram/forward_message.py` | `POST /bot{token}/forwardMessage` | Низкая | ⬜ | |
| 79 | Telegram Send Poll | `telegram/send_poll.py` | `POST /bot{token}/sendPoll` | Средняя | ⬜ | |
| 80 | Telegram Answer Callback Query | `telegram/answer_callback_query.py` | `POST /bot{token}/answerCallbackQuery` | Низкая | ⬜ | |
| 81 | Telegram Send Sticker | `telegram/send_sticker.py` | `POST /bot{token}/sendSticker` | Низкая | ⬜ | |
| 82 | Telegram Send Video Note | `telegram/send_video_note.py` | `POST /bot{token}/sendVideoNote` | Низкая | ⬜ | |
| 83 | Telegram Pin Message | `telegram/pin_message.py` | `POST /bot{token}/pinChatMessage` | Низкая | ⬜ | |
| 84 | Telegram Unpin Message | `telegram/unpin_message.py` | `POST /bot{token}/unpinChatMessage` | Низкая | ⬜ | |
| 85 | Telegram Get Chat Members Count | `telegram/get_chat_members_count.py` | `GET /bot{token}/getChatMemberCount` | Низкая | ⬜ | |

#### VK API (vk-api>=11.9.9 или httpx) - 10 интеграций

| № | Интеграция | Файл | API Метод | Сложность | Статус | Студент |
|---|-----------|------|-----------|-----------|--------|---------|
| 86 | VK Send Message | `vk/send_message.py` | `POST /method/messages.send` | Средняя | ⬜ | |
| 87 | VK Send Photo | `vk/send_photo.py` | `POST /method/photos.getMessagesUploadServer` | Средняя | ⬜ | |
| 88 | VK Get User | `vk/get_user.py` | `GET /method/users.get` | Низкая | ⬜ | |
| 89 | VK Get Group | `vk/get_group.py` | `GET /method/groups.getById` | Низкая | ⬜ | |
| 90 | VK Post Wall | `vk/post_wall.py` | `POST /method/wall.post` | Средняя | ⬜ | |
| 91 | VK Get Wall | `vk/get_wall.py` | `GET /method/wall.get` | Средняя | ⬜ | |
| 92 | VK Create Comment | `vk/create_comment.py` | `POST /method/wall.createComment` | Средняя | ⬜ | |
| 93 | VK Get Comments | `vk/get_comments.py` | `GET /method/wall.getComments` | Средняя | ⬜ | |
| 94 | VK Upload Photo | `vk/upload_photo.py` | `POST /method/photos.getMessagesUploadServer` | Высокая | ⬜ | |
| 95 | VK Get Friends | `vk/get_friends.py` | `GET /method/friends.get` | Средняя | ⬜ | |

---

### Категория: CRM - ~35 интеграций

#### Битрикс24 (httpx) - 12 интеграций

| № | Интеграция | Файл | API Метод | Сложность | Статус | Студент |
|---|-----------|------|-----------|-----------|--------|---------|
| 96 | Битрикс24 Create Task | `bitrix24/create_task.py` | `POST /rest/tasks.task.add` | Средняя | ⬜ | |
| 97 | Битрикс24 Update Task | `bitrix24/update_task.py` | `POST /rest/tasks.task.update` | Средняя | ⬜ | |
| 98 | Битрикс24 Get Task | `bitrix24/get_task.py` | `GET /rest/tasks.task.get` | Низкая | ⬜ | |
| 99 | Битрикс24 Create Deal | `bitrix24/create_deal.py` | `POST /rest/crm.deal.add` | Средняя | ⬜ | |
| 100 | Битрикс24 Update Deal | `bitrix24/update_deal.py` | `POST /rest/crm.deal.update` | Средняя | ⬜ | |
| 101 | Битрикс24 Get Deal | `bitrix24/get_deal.py` | `GET /rest/crm.deal.get` | Низкая | ⬜ | |
| 102 | Битрикс24 Create Contact | `bitrix24/create_contact.py` | `POST /rest/crm.contact.add` | Средняя | ⬜ | |
| 103 | Битрикс24 Update Contact | `bitrix24/update_contact.py` | `POST /rest/crm.contact.update` | Средняя | ⬜ | |
| 104 | Битрикс24 Get Contact | `bitrix24/get_contact.py` | `GET /rest/crm.contact.get` | Низкая | ⬜ | |
| 105 | Битрикс24 Create Company | `bitrix24/create_company.py` | `POST /rest/crm.company.add` | Средняя | ⬜ | |
| 106 | Битрикс24 Add Comment | `bitrix24/add_comment.py` | `POST /rest/crm.timeline.comment.add` | Низкая | ⬜ | |
| 107 | Битрикс24 Get Activity | `bitrix24/get_activity.py` | `GET /rest/crm.activity.get` | Средняя | ⬜ | |

#### AmoCRM (httpx) - 12 интеграций

| № | Интеграция | Файл | API Метод | Сложность | Статус | Студент |
|---|-----------|------|-----------|-----------|--------|---------|
| 108 | AmoCRM Create Contact | `amocrm/create_contact.py` | `POST /api/v4/contacts` | Средняя | ⬜ | |
| 109 | AmoCRM Update Contact | `amocrm/update_contact.py` | `PATCH /api/v4/contacts/{id}` | Средняя | ⬜ | |
| 110 | AmoCRM Get Contact | `amocrm/get_contact.py` | `GET /api/v4/contacts/{id}` | Низкая | ⬜ | |
| 111 | AmoCRM Create Lead | `amocrm/create_lead.py` | `POST /api/v4/leads` | Средняя | ⬜ | |
| 112 | AmoCRM Update Lead | `amocrm/update_lead.py` | `PATCH /api/v4/leads/{id}` | Средняя | ⬜ | |
| 113 | AmoCRM Get Lead | `amocrm/get_lead.py` | `GET /api/v4/leads/{id}` | Низкая | ⬜ | |
| 114 | AmoCRM Create Task | `amocrm/create_task.py` | `POST /api/v4/tasks` | Средняя | ⬜ | |
| 115 | AmoCRM Update Task | `amocrm/update_task.py` | `PATCH /api/v4/tasks/{id}` | Средняя | ⬜ | |
| 116 | AmoCRM Create Note | `amocrm/create_note.py` | `POST /api/v4/notes` | Низкая | ⬜ | |
| 117 | AmoCRM Create Company | `amocrm/create_company.py` | `POST /api/v4/companies` | Средняя | ⬜ | |
| 118 | AmoCRM Get Pipeline | `amocrm/get_pipeline.py` | `GET /api/v4/leads/pipelines` | Низкая | ⬜ | |
| 119 | AmoCRM Get Status | `amocrm/get_status.py` | `GET /api/v4/leads/pipelines/{id}/statuses` | Низкая | ⬜ | |

#### HubSpot (hubspot-api-client>=7.0.0) - 11 интеграций

| № | Интеграция | Файл | API Метод | Сложность | Статус | Студент |
|---|-----------|------|-----------|-----------|--------|---------|
| 120 | HubSpot Create Contact | `hubspot/create_contact.py` | `POST /crm/v3/objects/contacts` | Средняя | ⬜ | |
| 121 | HubSpot Update Contact | `hubspot/update_contact.py` | `PATCH /crm/v3/objects/contacts/{id}` | Средняя | ⬜ | |
| 122 | HubSpot Get Contact | `hubspot/get_contact.py` | `GET /crm/v3/objects/contacts/{id}` | Низкая | ⬜ | |
| 123 | HubSpot Delete Contact | `hubspot/delete_contact.py` | `DELETE /crm/v3/objects/contacts/{id}` | Низкая | ⬜ | |
| 124 | HubSpot Create Deal | `hubspot/create_deal.py` | `POST /crm/v3/objects/deals` | Средняя | ⬜ | |
| 125 | HubSpot Update Deal | `hubspot/update_deal.py` | `PATCH /crm/v3/objects/deals/{id}` | Средняя | ⬜ | |
| 126 | HubSpot Get Deal | `hubspot/get_deal.py` | `GET /crm/v3/objects/deals/{id}` | Низкая | ⬜ | |
| 127 | HubSpot Create Company | `hubspot/create_company.py` | `POST /crm/v3/objects/companies` | Средняя | ⬜ | |
| 128 | HubSpot Update Company | `hubspot/update_company.py` | `PATCH /crm/v3/objects/companies/{id}` | Средняя | ⬜ | |
| 129 | HubSpot Create Ticket | `hubspot/create_ticket.py` | `POST /crm/v3/objects/tickets` | Средняя | ⬜ | |
| 130 | HubSpot Get Pipeline | `hubspot/get_pipeline.py` | `GET /crm/v3/pipelines/deals` | Низкая | ⬜ | |

---

### Категория: E-commerce - ~25 интеграций

#### Wildberries API (httpx) - 13 интеграций

| № | Интеграция | Файл | API Метод | Сложность | Статус | Студент |
|---|-----------|------|-----------|-----------|--------|---------|
| 131 | Wildberries Get Product Info | `wildberries/get_product_info.py` | `GET /content/v1/cards/filter` | Средняя | ⬜ | |
| 132 | Wildberries Get Orders | `wildberries/get_orders.py` | `GET /api/v1/supplier/orders` | Средняя | ⬜ | |
| 133 | Wildberries Get Order | `wildberries/get_order.py` | `GET /api/v1/supplier/orders/{id}` | Низкая | ⬜ | |
| 134 | Wildberries Update Stock | `wildberries/update_stock.py` | `PUT /api/v1/supplier/stocks` | Высокая | ⬜ | |
| 135 | Wildberries Get Analytics | `wildberries/get_analytics.py` | `GET /api/v1/supplier/reportDetailByPeriod` | Средняя | ⬜ | |
| 136 | Wildberries Get Sales Report | `wildberries/get_sales_report.py` | `GET /api/v1/supplier/reportDetailByPeriod` | Средняя | ⬜ | |
| 137 | Wildberries Get Finance Report | `wildberries/get_finance_report.py` | `GET /api/v1/supplier/finances` | Средняя | ⬜ | |
| 138 | Wildberries Get Warehouse Stocks | `wildberries/get_warehouse_stocks.py` | `GET /api/v1/supplier/stocks` | Средняя | ⬜ | |
| 139 | Wildberries Get Supplier Orders | `wildberries/get_supplier_orders.py` | `GET /api/v1/supplier/orders` | Средняя | ⬜ | |
| 140 | Wildberries Get Supplier Sales | `wildberries/get_supplier_sales.py` | `GET /api/v1/supplier/sales` | Средняя | ⬜ | |
| 141 | Wildberries Get Supplier Returns | `wildberries/get_supplier_returns.py` | `GET /api/v1/supplier/returns` | Средняя | ⬜ | |
| 142 | Wildberries Get Supplier Stickers | `wildberries/get_supplier_stickers.py` | `POST /api/v1/supplier/stickers` | Средняя | ⬜ | |
| 143 | Wildberries Get Supplier Warehouses | `wildberries/get_supplier_warehouses.py` | `GET /api/v1/supplier/warehouses` | Низкая | ⬜ | |

#### Ozon API (httpx) - 12 интеграций

| № | Интеграция | Файл | API Метод | Сложность | Статус | Студент |
|---|-----------|------|-----------|-----------|--------|---------|
| 144 | Ozon Get Product Info | `ozon/get_product_info.py` | `POST /v2/product/info` | Средняя | ⬜ | |
| 145 | Ozon Get Orders | `ozon/get_orders.py` | `POST /v2/posting/fbs/list` | Средняя | ⬜ | |
| 146 | Ozon Get Order | `ozon/get_order.py` | `POST /v2/posting/fbs/get` | Низкая | ⬜ | |
| 147 | Ozon Update Stock | `ozon/update_stock.py` | `POST /v1/product/import/stocks` | Высокая | ⬜ | |
| 148 | Ozon Create FBO Order | `ozon/create_fbo_order.py` | `POST /v2/posting/fbs/create` | Высокая | ⬜ | |
| 149 | Ozon Get Product List | `ozon/get_product_list.py` | `POST /v2/product/list` | Средняя | ⬜ | |
| 150 | Ozon Get Analytics | `ozon/get_analytics.py` | `POST /v1/analytics/data` | Средняя | ⬜ | |
| 151 | Ozon Get Finance Report | `ozon/get_finance_report.py` | `POST /v3/finance/transaction/list` | Средняя | ⬜ | |
| 152 | Ozon Get Warehouse Stocks | `ozon/get_warehouse_stocks.py` | `POST /v1/product/info/stocks` | Средняя | ⬜ | |
| 153 | Ozon Get Returns | `ozon/get_returns.py` | `POST /v2/returns/company/fbo` | Средняя | ⬜ | |
| 154 | Ozon Get Posting | `ozon/get_posting.py` | `POST /v2/posting/fbs/get` | Средняя | ⬜ | |
| 155 | Ozon Update Posting | `ozon/update_posting.py` | `POST /v2/posting/fbs/update` | Средняя | ⬜ | |

---

### Категория: Образование - ~20 интеграций

#### Moodle API (httpx) - 10 интеграций

| № | Интеграция | Файл | API Метод | Сложность | Статус | Студент |
|---|-----------|------|-----------|-----------|--------|---------|
| 156 | Moodle Get Courses | `moodle/get_courses.py` | `GET /webservice/rest/server.php?wsfunction=core_course_get_courses` | Средняя | ⬜ | |
| 157 | Moodle Get Course | `moodle/get_course.py` | `GET /webservice/rest/server.php?wsfunction=core_course_get_courses_by_field` | Низкая | ⬜ | |
| 158 | Moodle Create Course | `moodle/create_course.py` | `GET /webservice/rest/server.php?wsfunction=core_course_create_courses` | Высокая | ⬜ | |
| 159 | Moodle Update Course | `moodle/update_course.py` | `GET /webservice/rest/server.php?wsfunction=core_course_update_courses` | Средняя | ⬜ | |
| 160 | Moodle Get Users | `moodle/get_users.py` | `GET /webservice/rest/server.php?wsfunction=core_user_get_users` | Средняя | ⬜ | |
| 161 | Moodle Get User | `moodle/get_user.py` | `GET /webservice/rest/server.php?wsfunction=core_user_get_users_by_field` | Низкая | ⬜ | |
| 162 | Moodle Enroll User | `moodle/enroll_user.py` | `GET /webservice/rest/server.php?wsfunction=enrol_manual_enrol_users` | Средняя | ⬜ | |
| 163 | Moodle Get Assignments | `moodle/get_assignments.py` | `GET /webservice/rest/server.php?wsfunction=mod_assign_get_assignments` | Средняя | ⬜ | |
| 164 | Moodle Get Grades | `moodle/get_grades.py` | `GET /webservice/rest/server.php?wsfunction=gradereport_user_get_grades_table` | Средняя | ⬜ | |
| 165 | Moodle Create Forum | `moodle/create_forum.py` | `GET /webservice/rest/server.php?wsfunction=mod_forum_add_discussion` | Средняя | ⬜ | |

#### Google Classroom (google-api-python-client) - 10 интеграций

| № | Интеграция | Файл | API Метод | Сложность | Статус | Студент |
|---|-----------|------|-----------|-----------|--------|---------|
| 166 | Google Classroom Get Courses | `google/classroom_get_courses.py` | `GET /v1/courses` | Средняя | ⬜ | |
| 167 | Google Classroom Create Course | `google/classroom_create_course.py` | `POST /v1/courses` | Высокая | ⬜ | |
| 168 | Google Classroom Update Course | `google/classroom_update_course.py` | `PATCH /v1/courses/{id}` | Средняя | ⬜ | |
| 169 | Google Classroom Get Students | `google/classroom_get_students.py` | `GET /v1/courses/{id}/students` | Средняя | ⬜ | |
| 170 | Google Classroom Add Student | `google/classroom_add_student.py` | `POST /v1/courses/{id}/students` | Средняя | ⬜ | |
| 171 | Google Classroom Get Assignments | `google/classroom_get_assignments.py` | `GET /v1/courses/{id}/courseWork` | Средняя | ⬜ | |
| 172 | Google Classroom Create Assignment | `google/classroom_create_assignment.py` | `POST /v1/courses/{id}/courseWork` | Высокая | ⬜ | |
| 173 | Google Classroom Get Submissions | `google/classroom_get_submissions.py` | `GET /v1/courses/{id}/courseWork/{id}/studentSubmissions` | Средняя | ⬜ | |
| 174 | Google Classroom Grade Submission | `google/classroom_grade_submission.py` | `PATCH /v1/courses/{id}/courseWork/{id}/studentSubmissions/{id}` | Средняя | ⬜ | |
| 175 | Google Classroom Get Announcements | `google/classroom_get_announcements.py` | `GET /v1/courses/{id}/announcements` | Средняя | ⬜ | |

---

### Категория: Медицина - ~15 интеграций

#### Медицинские справочники API (httpx) - 15 интеграций

| № | Интеграция | Файл | API Метод | Сложность | Статус | Студент |
|---|-----------|------|-----------|-----------|--------|---------|
| 176 | Медицина Get Drug Info | `medicine/get_drug_info.py` | `GET /api/v1/drugs/{id}` | Средняя | ⬜ | |
| 177 | Медицина Search Drugs | `medicine/search_drugs.py` | `GET /api/v1/drugs/search` | Средняя | ⬜ | |
| 178 | Медицина Get Drug Interactions | `medicine/get_drug_interactions.py` | `GET /api/v1/drugs/{id}/interactions` | Высокая | ⬜ | |
| 179 | Медицина Get Disease Info | `medicine/get_disease_info.py` | `GET /api/v1/diseases/{id}` | Средняя | ⬜ | |
| 180 | Медицина Search Diseases | `medicine/search_diseases.py` | `GET /api/v1/diseases/search` | Средняя | ⬜ | |
| 181 | Медицина Get Symptoms | `medicine/get_symptoms.py` | `GET /api/v1/symptoms` | Средняя | ⬜ | |
| 182 | Медицина Get ICD-10 Code | `medicine/get_icd10.py` | `GET /api/v1/icd10/{code}` | Средняя | ⬜ | |
| 183 | Медицина Get ATC Code | `medicine/get_atc_code.py` | `GET /api/v1/atc/{code}` | Средняя | ⬜ | |
| 184 | Медицина Get Medical Articles | `medicine/get_articles.py` | `GET /api/v1/articles` | Средняя | ⬜ | |
| 185 | Медицина Get Clinical Trials | `medicine/get_trials.py` | `GET /api/v1/trials` | Средняя | ⬜ | |
| 186 | Медицина Get Pharmacy Info | `medicine/get_pharmacy_info.py` | `GET /api/v1/pharmacies/{id}` | Низкая | ⬜ | |
| 187 | Медицина Search Pharmacies | `medicine/search_pharmacies.py` | `GET /api/v1/pharmacies/search` | Средняя | ⬜ | |
| 188 | Медицина Get Doctor Info | `medicine/get_doctor_info.py` | `GET /api/v1/doctors/{id}` | Низкая | ⬜ | |
| 189 | Медицина Search Doctors | `medicine/search_doctors.py` | `GET /api/v1/doctors/search` | Средняя | ⬜ | |
| 190 | Медицина Get Hospital Info | `medicine/get_hospital_info.py` | `GET /api/v1/hospitals/{id}` | Низкая | ⬜ | |

---

### Категория: Новости - ~10 интеграций

#### NewsAPI (httpx) - 5 интеграций

| № | Интеграция | Файл | API Метод | Сложность | Статус | Студент |
|---|-----------|------|-----------|-----------|--------|---------|
| 191 | NewsAPI Get Top Headlines | `newsapi/get_top_headlines.py` | `GET /v2/top-headlines` | Низкая | ⬜ | |
| 192 | NewsAPI Search | `newsapi/search.py` | `GET /v2/everything` | Низкая | ⬜ | |
| 193 | NewsAPI Get Sources | `newsapi/get_sources.py` | `GET /v2/sources` | Низкая | ⬜ | |
| 194 | NewsAPI Get Everything | `newsapi/get_everything.py` | `GET /v2/everything` | Средняя | ⬜ | |
| 195 | NewsAPI Get Categories | `newsapi/get_categories.py` | `GET /v2/sources?category=` | Низкая | ⬜ | |

#### Яндекс.Новости (httpx) - 5 интеграций

| № | Интеграция | Файл | API Метод | Сложность | Статус | Студент |
|---|-----------|------|-----------|-----------|--------|---------|
| 196 | Yandex News Get Top | `yandex/news_top.py` | `GET /v1/news` | Низкая | ⬜ | |
| 197 | Yandex News Search | `yandex/news_search.py` | `GET /v1/news/search` | Низкая | ⬜ | |
| 198 | Yandex News Get Categories | `yandex/news_categories.py` | `GET /v1/news/categories` | Низкая | ⬜ | |
| 199 | Yandex News Get Trending | `yandex/news_trending.py` | `GET /v1/news/trending` | Средняя | ⬜ | |
| 200 | Yandex News Get Article | `yandex/news_article.py` | `GET /v1/news/{id}` | Низкая | ⬜ | |

---

### Категория: Переводы - ~10 интеграций

#### Яндекс.Переводчик (httpx) - 5 интеграций

| № | Интеграция | Файл | API Метод | Сложность | Статус | Студент |
|---|-----------|------|-----------|-----------|--------|---------|
| 201 | Yandex Translate Text | `yandex/translate_text.py` | `POST /v1.5/tr.json/translate` | Низкая | ⬜ | |
| 202 | Yandex Translate Detect Language | `yandex/translate_detect.py` | `POST /v1.5/tr.json/detect` | Низкая | ⬜ | |
| 203 | Yandex Translate Get Languages | `yandex/translate_languages.py` | `GET /v1.5/tr.json/getLangs` | Низкая | ⬜ | |
| 204 | Yandex Translate Translate Document | `yandex/translate_document.py` | `POST /v1.5/tr.json/translate` (document) | Высокая | ⬜ | |
| 205 | Yandex Translate Get Translation History | `yandex/translate_history.py` | `GET /v1.5/tr.json/getHistory` | Средняя | ⬜ | |

#### Google Translate (googletrans>=4.0.0 или httpx) - 5 интеграций

| № | Интеграция | Файл | API Метод | Сложность | Статус | Студент |
|---|-----------|------|-----------|-----------|--------|---------|
| 206 | Google Translate Text | `google/translate_text.py` | `POST /language/translate/v2` | Низкая | ⬜ | |
| 207 | Google Translate Detect Language | `google/translate_detect.py` | `POST /language/translate/v2/detect` | Низкая | ⬜ | |
| 208 | Google Translate Get Languages | `google/translate_languages.py` | `GET /language/translate/v2/languages` | Низкая | ⬜ | |
| 209 | Google Translate Translate Document | `google/translate_document.py` | `POST /v3/{parent}:translateDocument` | Высокая | ⬜ | |
| 210 | Google Translate Get Supported Languages | `google/translate_supported_languages.py` | `GET /language/translate/v2/languages` | Низкая | ⬜ | |

---

### Категория: Контроль версий - ~15 интеграций

#### GitHub (httpx или PyGithub) - 8 интеграций

| № | Интеграция | Файл | API Метод | Сложность | Статус | Студент |
|---|-----------|------|-----------|-----------|--------|---------|
| 211 | GitHub Create Issue | `github/create_issue.py` | `POST /repos/{owner}/{repo}/issues` | Средняя | ⬜ | |
| 212 | GitHub Update Issue | `github/update_issue.py` | `PATCH /repos/{owner}/{repo}/issues/{issue_number}` | Средняя | ⬜ | |
| 213 | GitHub Get Issue | `github/get_issue.py` | `GET /repos/{owner}/{repo}/issues/{issue_number}` | Низкая | ⬜ | |
| 214 | GitHub Create Pull Request | `github/create_pull_request.py` | `POST /repos/{owner}/{repo}/pulls` | Высокая | ⬜ | |
| 215 | GitHub Get Pull Request | `github/get_pull_request.py` | `GET /repos/{owner}/{repo}/pulls/{pull_number}` | Низкая | ⬜ | |
| 216 | GitHub Get Repository | `github/get_repository.py` | `GET /repos/{owner}/{repo}` | Низкая | ⬜ | |
| 217 | GitHub Create Repository | `github/create_repository.py` | `POST /user/repos` | Средняя | ⬜ | |
| 218 | GitHub Get Commits | `github/get_commits.py` | `GET /repos/{owner}/{repo}/commits` | Средняя | ⬜ | |

#### GitVerse (httpx) - 7 интеграций

| № | Интеграция | Файл | API Метод | Сложность | Статус | Студент |
|---|-----------|------|-----------|-----------|--------|---------|
| 219 | GitVerse Create Repository | `gitverse/create_repository.py` | `POST /api/v4/projects` | Средняя | ⬜ | |
| 220 | GitVerse Get Repository | `gitverse/get_repository.py` | `GET /api/v4/projects/{id}` | Низкая | ⬜ | |
| 221 | GitVerse Create Issue | `gitverse/create_issue.py` | `POST /api/v4/projects/{id}/issues` | Средняя | ⬜ | |
| 222 | GitVerse Get Issue | `gitverse/get_issue.py` | `GET /api/v4/projects/{id}/issues/{issue_iid}` | Низкая | ⬜ | |
| 223 | GitVerse Create Merge Request | `gitverse/create_merge_request.py` | `POST /api/v4/projects/{id}/merge_requests` | Высокая | ⬜ | |
| 224 | GitVerse Get Merge Request | `gitverse/get_merge_request.py` | `GET /api/v4/projects/{id}/merge_requests/{merge_request_iid}` | Низкая | ⬜ | |
| 225 | GitVerse Get Commits | `gitverse/get_commits.py` | `GET /api/v4/projects/{id}/repository/commits` | Средняя | ⬜ | |

---

## Пресеты для реализации

Помимо интеграций, студенты могут также реализовывать пресеты - готовые заготовки для типовых шагов.

### Список пресетов

| № | Preset | Файл | Описание | Сложность | Статус | Студент |
|---|--------|------|----------|-----------|--------|---------|
| P1 | IF/ELSE | `presets/conditional.py` | Условный переход IF/ELSE | Средняя | ✅ | УЖЕ РЕАЛИЗОВАНО |
| P2 | Switch | `presets/switch.py` | Множественное ветвление (SWITCH/CASE) | Средняя | ⬜ | |
| P3 | Loop | `presets/loop.py` | Цикл по элементам | Высокая | ⬜ | |
| P4 | Message | `presets/message.py` | Простой шаг с сообщением | Низкая | ⬜ | |
| P5 | Code | `presets/code.py` | Шаг с произвольным кодом | Средняя | ⬜ | |
| P6 | Integration Step | `presets/integration.py` | Шаг с интеграцией | Средняя | ⬜ | |
| P7 | Parallel | `presets/parallel.py` | Параллельное выполнение | Высокая | ⬜ | |
| P8 | Retry | `presets/retry.py` | Повтор при ошибке | Средняя | ⬜ | |
| P9 | Timeout | `presets/timeout.py` | Таймаут выполнения | Средняя | ⬜ | |

### Требования к пресетам

1. Класс наследуется от `BasePreset`
2. Метод `build()` генерирует структуры Step + ConnectionGroup + Connections
3. Метаданные заполнены (id, name, description, category, icon_s3_key, color, config_schema)
4. Примеры использования добавлены

### Примеры пресетов

- См. `backend/app/presets/conditional.py` - пример IF/ELSE пресета
- См. `backend/app/presets/base.py` - базовый класс
- См. `backend/app/presets/registry.py` - реестр пресетов

---


**Обновлено**: 20.11.2025
