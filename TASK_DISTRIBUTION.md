# Распределение задач по интеграциям

Этот документ содержит полный список интеграций для реализации и таблицу для распределения задач между студентами.

## Статистика

- **Всего интеграций**: ~150+
- **Категорий**: 12
- **Оценка времени на интеграцию**: 3-5 дней

---

## Полный список интеграций

### Категория: Messaging (Мессенджеры) - ~30 интеграций

#### Telegram (python-telegram-bot>=20.0) - 15 интеграций

| № | Интеграция | Файл | Сложность | Статус | Студент |
|---|-----------|------|-----------|--------|---------|
| 1 | Telegram Get Updates | `telegram/get_updates.py` | Низкая | ⬜ | |
| 2 | Telegram Send Message | `telegram/send_message.py` | Низкая | ✅ | УЖЕ РЕАЛИЗОВАНО |
| 3 | Telegram Send Photo | `telegram/send_photo.py` | Низкая | ⬜ | |
| 4 | Telegram Send Document | `telegram/send_document.py` | Низкая | ⬜ | |
| 5 | Telegram Send Video | `telegram/send_video.py` | Низкая | ⬜ | |
| 6 | Telegram Send Audio | `telegram/send_audio.py` | Низкая | ⬜ | |
| 7 | Telegram Send Voice | `telegram/send_voice.py` | Низкая | ⬜ | |
| 8 | Telegram Send Location | `telegram/send_location.py` | Низкая | ⬜ | |
| 9 | Telegram Edit Message | `telegram/edit_message.py` | Низкая | ⬜ | |
| 10 | Telegram Delete Message | `telegram/delete_message.py` | Низкая | ⬜ | |
| 11 | Telegram Get Chat | `telegram/get_chat.py` | Низкая | ⬜ | |
| 12 | Telegram Get User | `telegram/get_user.py` | Низкая | ⬜ | |
| 13 | Telegram Forward Message | `telegram/forward_message.py` | Низкая | ⬜ | |
| 14 | Telegram Send Poll | `telegram/send_poll.py` | Средняя | ⬜ | |
| 15 | Telegram Answer Callback Query | `telegram/answer_callback_query.py` | Низкая | ⬜ | |

#### Discord (discord.py>=2.3.0) - 8 интеграций

| № | Интеграция | Файл | Сложность | Статус | Студент |
|---|-----------|------|-----------|--------|---------|
| 16 | Discord Send Message | `discord/send_message.py` | Низкая | ⬜ | |
| 17 | Discord Execute Webhook | `discord/execute_webhook.py` | Низкая | ⬜ | |
| 18 | Discord Edit Message | `discord/edit_message.py` | Низкая | ⬜ | |
| 19 | Discord Delete Message | `discord/delete_message.py` | Низкая | ⬜ | |
| 20 | Discord Send Embed | `discord/send_embed.py` | Средняя | ⬜ | |
| 21 | Discord Add Reaction | `discord/add_reaction.py` | Низкая | ⬜ | |
| 22 | Discord Get Channel | `discord/get_channel.py` | Низкая | ⬜ | |
| 23 | Discord Get Guild | `discord/get_guild.py` | Низкая | ⬜ | |

#### VK (vk-api>=11.9.9 или httpx) - 4 интеграции

| № | Интеграция | Файл | Сложность | Статус | Студент |
|---|-----------|------|-----------|--------|---------|
| 24 | VK Send Message | `vk/send_message.py` | Средняя | ⬜ | |
| 25 | VK Send Photo | `vk/send_photo.py` | Средняя | ⬜ | |
| 26 | VK Get User | `vk/get_user.py` | Низкая | ⬜ | |
| 27 | VK Get Group | `vk/get_group.py` | Низкая | ⬜ | |

#### WhatsApp (httpx) - 3 интеграции

| № | Интеграция | Файл | Сложность | Статус | Студент |
|---|-----------|------|-----------|--------|---------|
| 28 | WhatsApp Send Message | `whatsapp/send_message.py` | Средняя | ⬜ | |
| 29 | WhatsApp Send Media | `whatsapp/send_media.py` | Средняя | ⬜ | |
| 30 | WhatsApp Get Message Status | `whatsapp/get_message_status.py` | Средняя | ⬜ | |

---

### Категория: AI (Искусственный интеллект) - ~20 интеграций

#### OpenAI (openai>=1.0.0) - 10 интеграций

| № | Интеграция | Файл | Сложность | Статус | Студент |
|---|-----------|------|-----------|--------|---------|
| 31 | OpenAI Chat Completion | `openai/chat_completion.py` | Средняя | ⬜ | |
| 32 | OpenAI Embedding | `openai/embedding.py` | Низкая | ⬜ | |
| 33 | OpenAI Image Generation | `openai/image_generation.py` | Средняя | ⬜ | |
| 34 | OpenAI Audio Transcription | `openai/audio_transcription.py` | Средняя | ⬜ | |
| 35 | OpenAI Audio Translation | `openai/audio_translation.py` | Средняя | ⬜ | |
| 36 | OpenAI Moderation | `openai/moderation.py` | Низкая | ⬜ | |
| 37 | OpenAI Fine-tune Create | `openai/fine_tune_create.py` | Высокая | ⬜ | |
| 38 | OpenAI File Upload | `openai/file_upload.py` | Средняя | ⬜ | |
| 39 | OpenAI File List | `openai/file_list.py` | Низкая | ⬜ | |
| 40 | OpenAI File Delete | `openai/file_delete.py` | Низкая | ⬜ | |

#### Yandex GPT (yandexcloud>=0.1.0 или httpx) - 4 интеграции

| № | Интеграция | Файл | Сложность | Статус | Студент |
|---|-----------|------|-----------|--------|---------|
| 41 | Yandex GPT Completion | `yandex/gpt_completion.py` | Средняя | ⬜ | |
| 42 | Yandex GPT Embedding | `yandex/gpt_embedding.py` | Средняя | ⬜ | |
| 43 | Yandex SpeechKit Recognition | `yandex/speechkit_recognition.py` | Средняя | ⬜ | |
| 44 | Yandex SpeechKit Synthesis | `yandex/speechkit_synthesis.py` | Средняя | ⬜ | |

#### Anthropic Claude (httpx) - 2 интеграции

| № | Интеграция | Файл | Сложность | Статус | Студент |
|---|-----------|------|-----------|--------|---------|
| 45 | Claude Chat Completion | `claude/chat_completion.py` | Средняя | ⬜ | |
| 46 | Claude Message | `claude/message.py` | Средняя | ⬜ | |

#### Google AI (google-generativeai или httpx) - 2 интеграции

| № | Интеграция | Файл | Сложность | Статус | Студент |
|---|-----------|------|-----------|--------|---------|
| 47 | Google Gemini Chat | `google/gemini_chat.py` | Средняя | ⬜ | |
| 48 | Google Gemini Embedding | `google/gemini_embedding.py` | Средняя | ⬜ | |

---

### Категория: Storage (Хранилища) - ~20 интеграций

#### Google (google-api-python-client>=2.0.0) - 11 интеграций

| № | Интеграция | Файл | Сложность | Статус | Студент |
|---|-----------|------|-----------|--------|---------|
| 49 | Google Sheets Read | `google/sheets_read.py` | Средняя | ⬜ | |
| 50 | Google Sheets Write | `google/sheets_write.py` | Средняя | ⬜ | |
| 51 | Google Sheets Append | `google/sheets_append.py` | Средняя | ⬜ | |
| 52 | Google Sheets Update | `google/sheets_update.py` | Средняя | ⬜ | |
| 53 | Google Sheets Clear | `google/sheets_clear.py` | Низкая | ⬜ | |
| 54 | Google Drive Upload | `google/drive_upload.py` | Средняя | ⬜ | |
| 55 | Google Drive Download | `google/drive_download.py` | Средняя | ⬜ | |
| 56 | Google Drive List | `google/drive_list.py` | Низкая | ⬜ | |
| 57 | Google Drive Delete | `google/drive_delete.py` | Низкая | ⬜ | |
| 58 | Google Drive Create Folder | `google/drive_create_folder.py` | Низкая | ⬜ | |
| 59 | Google Drive Share | `google/drive_share.py` | Средняя | ⬜ | |

#### Dropbox (dropbox>=11.36.0) - 6 интеграций

| № | Интеграция | Файл | Сложность | Статус | Студент |
|---|-----------|------|-----------|--------|---------|
| 60 | Dropbox Upload | `dropbox/upload.py` | Средняя | ⬜ | |
| 61 | Dropbox Download | `dropbox/download.py` | Средняя | ⬜ | |
| 62 | Dropbox List | `dropbox/list.py` | Низкая | ⬜ | |
| 63 | Dropbox Delete | `dropbox/delete.py` | Низкая | ⬜ | |
| 64 | Dropbox Create Folder | `dropbox/create_folder.py` | Низкая | ⬜ | |
| 65 | Dropbox Share Link | `dropbox/share_link.py` | Средняя | ⬜ | |

#### Notion (httpx) - 5 интеграций

| № | Интеграция | Файл | Сложность | Статус | Студент |
|---|-----------|------|-----------|--------|---------|
| 66 | Notion Create Page | `notion/create_page.py` | Средняя | ⬜ | |
| 67 | Notion Update Page | `notion/update_page.py` | Средняя | ⬜ | |
| 68 | Notion Read Page | `notion/read_page.py` | Низкая | ⬜ | |
| 69 | Notion Query Database | `notion/query_database.py` | Средняя | ⬜ | |
| 70 | Notion Create Database | `notion/create_database.py` | Средняя | ⬜ | |

---

### Категория: Payments (Платежи) - ~15 интеграций

#### Stripe (stripe>=7.0.0) - 8 интеграций

| № | Интеграция | Файл | Сложность | Статус | Студент |
|---|-----------|------|-----------|--------|---------|
| 71 | Stripe Create Payment | `stripe/create_payment.py` | Средняя | ⬜ | |
| 72 | Stripe Create Payment Intent | `stripe/create_payment_intent.py` | Средняя | ⬜ | |
| 73 | Stripe Get Payment | `stripe/get_payment.py` | Низкая | ⬜ | |
| 74 | Stripe Refund | `stripe/refund.py` | Средняя | ⬜ | |
| 75 | Stripe Create Customer | `stripe/create_customer.py` | Низкая | ⬜ | |
| 76 | Stripe Get Customer | `stripe/get_customer.py` | Низкая | ⬜ | |
| 77 | Stripe Create Subscription | `stripe/create_subscription.py` | Высокая | ⬜ | |
| 78 | Stripe Cancel Subscription | `stripe/cancel_subscription.py` | Средняя | ⬜ | |

#### YooKassa (yookassa>=2.3.0) - 4 интеграции

| № | Интеграция | Файл | Сложность | Статус | Студент |
|---|-----------|------|-----------|--------|---------|
| 79 | YooKassa Create Payment | `yookassa/create_payment.py` | Средняя | ⬜ | |
| 80 | YooKassa Get Payment | `yookassa/get_payment.py` | Низкая | ⬜ | |
| 81 | YooKassa Cancel Payment | `yookassa/cancel_payment.py` | Средняя | ⬜ | |
| 82 | YooKassa Refund | `yookassa/refund.py` | Средняя | ⬜ | |

#### PayPal (httpx) - 4 интеграции

| № | Интеграция | Файл | Сложность | Статус | Студент |
|---|-----------|------|-----------|--------|---------|
| 83 | PayPal Create Order | `paypal/create_order.py` | Средняя | ⬜ | |
| 84 | PayPal Capture Order | `paypal/capture_order.py` | Средняя | ⬜ | |
| 85 | PayPal Get Order | `paypal/get_order.py` | Низкая | ⬜ | |
| 86 | PayPal Refund | `paypal/refund.py` | Средняя | ⬜ | |

---

### Категория: CRM - ~20 интеграций

#### AmoCRM (httpx) - 7 интеграций

| № | Интеграция | Файл | Сложность | Статус | Студент |
|---|-----------|------|-----------|--------|---------|
| 87 | AmoCRM Create Contact | `amocrm/create_contact.py` | Средняя | ⬜ | |
| 88 | AmoCRM Update Contact | `amocrm/update_contact.py` | Средняя | ⬜ | |
| 89 | AmoCRM Get Contact | `amocrm/get_contact.py` | Низкая | ⬜ | |
| 90 | AmoCRM Create Lead | `amocrm/create_lead.py` | Средняя | ⬜ | |
| 91 | AmoCRM Update Lead | `amocrm/update_lead.py` | Средняя | ⬜ | |
| 92 | AmoCRM Create Task | `amocrm/create_task.py` | Средняя | ⬜ | |
| 93 | AmoCRM Create Note | `amocrm/create_note.py` | Низкая | ⬜ | |

#### Битрикс24 (httpx) - 6 интеграций

| № | Интеграция | Файл | Сложность | Статус | Студент |
|---|-----------|------|-----------|--------|---------|
| 94 | Битрикс24 Create Task | `bitrix24/create_task.py` | Средняя | ⬜ | |
| 95 | Битрикс24 Update Task | `bitrix24/update_task.py` | Средняя | ⬜ | |
| 96 | Битрикс24 Create Deal | `bitrix24/create_deal.py` | Средняя | ⬜ | |
| 97 | Битрикс24 Create Contact | `bitrix24/create_contact.py` | Средняя | ⬜ | |
| 98 | Битрикс24 Create Company | `bitrix24/create_company.py` | Средняя | ⬜ | |
| 99 | Битрикс24 Add Comment | `bitrix24/add_comment.py` | Низкая | ⬜ | |

#### HubSpot (hubspot-api-client>=7.0.0) - 5 интеграций

| № | Интеграция | Файл | Сложность | Статус | Студент |
|---|-----------|------|-----------|--------|---------|
| 100 | HubSpot Create Contact | `hubspot/create_contact.py` | Средняя | ⬜ | |
| 101 | HubSpot Update Contact | `hubspot/update_contact.py` | Средняя | ⬜ | |
| 102 | HubSpot Get Contact | `hubspot/get_contact.py` | Низкая | ⬜ | |
| 103 | HubSpot Create Deal | `hubspot/create_deal.py` | Средняя | ⬜ | |
| 104 | HubSpot Create Company | `hubspot/create_company.py` | Средняя | ⬜ | |

---

### Категория: E-commerce - ~10 интеграций

#### Wildberries (httpx) - 4 интеграции

| № | Интеграция | Файл | Сложность | Статус | Студент |
|---|-----------|------|-----------|--------|---------|
| 105 | Wildberries Get Product Info | `wildberries/get_product_info.py` | Средняя | ⬜ | |
| 106 | Wildberries Get Orders | `wildberries/get_orders.py` | Средняя | ⬜ | |
| 107 | Wildberries Update Stock | `wildberries/update_stock.py` | Высокая | ⬜ | |
| 108 | Wildberries Get Analytics | `wildberries/get_analytics.py` | Средняя | ⬜ | |

#### Ozon (httpx) - 4 интеграции

| № | Интеграция | Файл | Сложность | Статус | Студент |
|---|-----------|------|-----------|--------|---------|
| 109 | Ozon Get Product Info | `ozon/get_product_info.py` | Средняя | ⬜ | |
| 110 | Ozon Get Orders | `ozon/get_orders.py` | Средняя | ⬜ | |
| 111 | Ozon Update Stock | `ozon/update_stock.py` | Высокая | ⬜ | |
| 112 | Ozon Create FBO Order | `ozon/create_fbo_order.py` | Высокая | ⬜ | |

---

### Категория: Weather (Погода) - ~5 интеграций

#### OpenWeatherMap (httpx) - 3 интеграции

| № | Интеграция | Файл | Сложность | Статус | Студент |
|---|-----------|------|-----------|--------|---------|
| 113 | OpenWeatherMap Get Current | `openweathermap/get_current.py` | Низкая | ⬜ | |
| 114 | OpenWeatherMap Get Forecast | `openweathermap/get_forecast.py` | Низкая | ⬜ | |
| 115 | OpenWeatherMap Get History | `openweathermap/get_history.py` | Средняя | ⬜ | |

#### Яндекс.Погода (httpx) - 2 интеграции

| № | Интеграция | Файл | Сложность | Статус | Студент |
|---|-----------|------|-----------|--------|---------|
| 116 | Yandex Weather Get Current | `yandex/weather_current.py` | Низкая | ⬜ | |
| 117 | Yandex Weather Get Forecast | `yandex/weather_forecast.py` | Низкая | ⬜ | |

---

### Категория: Maps (Карты) - ~10 интеграций

#### Яндекс.Карты (httpx) - 4 интеграции

| № | Интеграция | Файл | Сложность | Статус | Студент |
|---|-----------|------|-----------|--------|---------|
| 118 | Yandex Maps Geocode | `yandex/maps_geocode.py` | Низкая | ⬜ | |
| 119 | Yandex Maps Reverse Geocode | `yandex/maps_reverse_geocode.py` | Низкая | ⬜ | |
| 120 | Yandex Maps Route | `yandex/maps_route.py` | Средняя | ⬜ | |
| 121 | Yandex Maps Search | `yandex/maps_search.py` | Средняя | ⬜ | |

#### Google Maps (googlemaps>=4.10.0) - 5 интеграций

| № | Интеграция | Файл | Сложность | Статус | Студент |
|---|-----------|------|-----------|--------|---------|
| 122 | Google Maps Geocode | `google/maps_geocode.py` | Низкая | ⬜ | |
| 123 | Google Maps Reverse Geocode | `google/maps_reverse_geocode.py` | Низкая | ⬜ | |
| 124 | Google Maps Route | `google/maps_route.py` | Средняя | ⬜ | |
| 125 | Google Maps Place Search | `google/maps_place_search.py` | Средняя | ⬜ | |
| 126 | Google Maps Distance Matrix | `google/maps_distance_matrix.py` | Средняя | ⬜ | |

---

### Категория: Translation (Переводы) - ~5 интеграций

#### Яндекс.Переводчик (httpx) - 2 интеграции

| № | Интеграция | Файл | Сложность | Статус | Студент |
|---|-----------|------|-----------|--------|---------|
| 127 | Yandex Translate Text | `yandex/translate_text.py` | Низкая | ⬜ | |
| 128 | Yandex Translate Detect Language | `yandex/translate_detect.py` | Низкая | ⬜ | |

#### Google Translate (googletrans>=4.0.0 или httpx) - 2 интеграции

| № | Интеграция | Файл | Сложность | Статус | Студент |
|---|-----------|------|-----------|--------|---------|
| 129 | Google Translate Text | `google/translate_text.py` | Низкая | ⬜ | |
| 130 | Google Translate Detect Language | `google/translate_detect.py` | Низкая | ⬜ | |

---

### Категория: News (Новости) - ~5 интеграций

#### NewsAPI (httpx) - 3 интеграции

| № | Интеграция | Файл | Сложность | Статус | Студент |
|---|-----------|------|-----------|--------|---------|
| 131 | NewsAPI Get Top Headlines | `newsapi/get_top_headlines.py` | Низкая | ⬜ | |
| 132 | NewsAPI Search | `newsapi/search.py` | Низкая | ⬜ | |
| 133 | NewsAPI Get Sources | `newsapi/get_sources.py` | Низкая | ⬜ | |

#### Яндекс.Новости (httpx) - 2 интеграции

| № | Интеграция | Файл | Сложность | Статус | Студент |
|---|-----------|------|-----------|--------|---------|
| 134 | Yandex News Get Top | `yandex/news_top.py` | Низкая | ⬜ | |
| 135 | Yandex News Search | `yandex/news_search.py` | Низкая | ⬜ | |

---

### Категория: Social Media - ~10 интеграций

#### Twitter/X (httpx) - 3 интеграции

| № | Интеграция | Файл | Сложность | Статус | Студент |
|---|-----------|------|-----------|--------|---------|
| 136 | Twitter Post Tweet | `twitter/post_tweet.py` | Средняя | ⬜ | |
| 137 | Twitter Get Tweet | `twitter/get_tweet.py` | Низкая | ⬜ | |
| 138 | Twitter Search Tweets | `twitter/search_tweets.py` | Средняя | ⬜ | |

#### Instagram (httpx) - 2 интеграции

| № | Интеграция | Файл | Сложность | Статус | Студент |
|---|-----------|------|-----------|--------|---------|
| 139 | Instagram Get Media | `instagram/get_media.py` | Средняя | ⬜ | |
| 140 | Instagram Get User | `instagram/get_user.py` | Низкая | ⬜ | |

---

### Категория: Communication - ~10 интеграций

#### Email (smtplib или httpx) - 3 интеграции

| № | Интеграция | Файл | Сложность | Статус | Студент |
|---|-----------|------|-----------|--------|---------|
| 141 | Email Send (SMTP) | `email/send_smtp.py` | Средняя | ⬜ | |
| 142 | SendGrid Send Email | `sendgrid/send_email.py` | Средняя | ⬜ | |
| 143 | Mailgun Send Email | `mailgun/send_email.py` | Средняя | ⬜ | |

#### SMS (httpx) - 2 интеграции

| № | Интеграция | Файл | Сложность | Статус | Студент |
|---|-----------|------|-----------|--------|---------|
| 144 | Twilio Send SMS | `twilio/send_sms.py` | Средняя | ⬜ | |
| 145 | SMS.ru Send SMS | `smsru/send_sms.py` | Средняя | ⬜ | |

---

### Категория: Analytics - ~5 интеграций

#### Google Analytics (google-api-python-client) - 2 интеграции

| № | Интеграция | Файл | Сложность | Статус | Студент |
|---|-----------|------|-----------|--------|---------|
| 146 | Google Analytics Get Report | `google/analytics_report.py` | Высокая | ⬜ | |
| 147 | Google Analytics Get Realtime | `google/analytics_realtime.py` | Средняя | ⬜ | |

#### Yandex Metrica (httpx) - 1 интеграция

| № | Интеграция | Файл | Сложность | Статус | Студент |
|---|-----------|------|-----------|--------|---------|
| 148 | Yandex Metrica Get Report | `yandex/metrica_report.py` | Средняя | ⬜ | |

---

### Категория: Other - ~15 интеграций

#### GitHub (httpx) - 3 интеграции

| № | Интеграция | Файл | Сложность | Статус | Студент |
|---|-----------|------|-----------|--------|---------|
| 149 | GitHub Create Issue | `github/create_issue.py` | Средняя | ⬜ | |
| 150 | GitHub Create Pull Request | `github/create_pull_request.py` | Высокая | ⬜ | |
| 151 | GitHub Get Repository | `github/get_repository.py` | Низкая | ⬜ | |

#### Slack (httpx) - 3 интеграции

| № | Интеграция | Файл | Сложность | Статус | Студент |
|---|-----------|------|-----------|--------|---------|
| 152 | Slack Send Message | `slack/send_message.py` | Средняя | ⬜ | |
| 153 | Slack Create Channel | `slack/create_channel.py` | Средняя | ⬜ | |
| 154 | Slack Upload File | `slack/upload_file.py` | Средняя | ⬜ | |

#### Jira (httpx) - 3 интеграции

| № | Интеграция | Файл | Сложность | Статус | Студент |
|---|-----------|------|-----------|--------|---------|
| 155 | Jira Create Issue | `jira/create_issue.py` | Средняя | ⬜ | |
| 156 | Jira Update Issue | `jira/update_issue.py` | Средняя | ⬜ | |
| 157 | Jira Get Issue | `jira/get_issue.py` | Низкая | ⬜ | |

#### Trello (httpx) - 3 интеграции

| № | Интеграция | Файл | Сложность | Статус | Студент |
|---|-----------|------|-----------|--------|---------|
| 158 | Trello Create Card | `trello/create_card.py` | Средняя | ⬜ | |
| 159 | Trello Update Card | `trello/update_card.py` | Средняя | ⬜ | |
| 160 | Trello Create List | `trello/create_list.py` | Средняя | ⬜ | |

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

1. **Начать с простых**: Telegram, Discord (низкая сложность)
2. **Затем средние**: OpenAI, Google Sheets (средняя сложность)
3. **Сложные в конце**: OAuth интеграции, сложные платежи (высокая сложность)

### Группировка задач

Студенты могут взять несколько интеграций одной категории для более эффективной работы.

---

## Полезные ссылки

- [STUDENT_GUIDE.md](./STUDENT_GUIDE.md) - главное руководство
- [STUDENT_AI_PROMPT.md](./STUDENT_AI_PROMPT.md) - примеры промптов
- [STUDENT_WORKFLOW.md](./STUDENT_WORKFLOW.md) - процесс работы
- [INSTALLATION.md](./INSTALLATION.md) - установка окружения

---

**Обновлено**: 20.11.2025

