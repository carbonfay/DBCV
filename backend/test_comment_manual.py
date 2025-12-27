#!/usr/bin/env python3
"""
Тестовый скрипт для ручного тестирования создания комментария в VK.
Введите API ключ бота и данные поста для создания комментария.
Использует vk-api напрямую.
"""

import asyncio

try:
    import vk_api
    from vk_api.exceptions import VkApiError
    VK_API_AVAILABLE = True
except ImportError:
    print("❌ vk-api не установлен. Установите: pip install vk-api")
    exit(1)

async def test_create_comment():
    """Тестирование создания комментария с ручным вводом данных."""

    print("=== Тест создания комментария VK ===")
    print("Введите данные для тестирования:")
    print()

    # Ввод данных
    access_token = input("Введите API ключ бота ВКонтакте: ").strip()
    if not access_token:
        print("❌ API ключ обязателен!")
        return

    try:
        owner_id = int(input("Введите ID владельца стены (отрицательное для сообщества): ").strip())
    except ValueError:
        print("❌ Неверный формат owner_id!")
        return

    try:
        post_id = int(input("Введите ID поста: ").strip())
    except ValueError:
        print("❌ Неверный формат post_id!")
        return

    message = input("Введите текст комментария: ").strip()
    if not message:
        print("❌ Текст комментария обязателен!")
        return

    from_group = input("Комментировать от имени сообщества? (y/n, по умолчанию y): ").strip().lower()
    from_group = from_group != 'n'  # True по умолчанию

    print("\n=== Запуск теста ===")

    # Параметры для API
    params = {
        "owner_id": owner_id,
        "post_id": post_id,
        "message": message
    }

    if from_group:
        params["from_group"] = 1

    try:
        # Создаем VK API клиент
        vk = vk_api.VkApi(token=access_token)

        # Выполняем запрос в отдельном потоке
        result = await asyncio.to_thread(
            vk.method,
            "wall.createComment",
            params
        )

        # Проверяем результат
        comment_id = result.get("comment_id")
        if comment_id:
            print("✅ УСПЕХ!")
            print(f"Комментарий создан с ID: {comment_id}")
            print(f"Ссылка на комментарий: https://vk.com/wall{owner_id}_{post_id}?reply={comment_id}")
        else:
            print("❌ ОШИБКА: Не удалось получить ID комментария")
            print(f"Ответ API: {result}")

    except VkApiError as e:
        print("❌ ОШИБКА VK API!")
        print(f"Код ошибки: {getattr(e, 'error_code', 'неизвестен')}")
        print(f"Описание: {str(e)}")

        # Специальная обработка для распространенных ошибок
        if getattr(e, "error_code", None) == 15:
            print("💡 Совет: Проверьте права доступа токена (нужно право 'wall')")

    except Exception as e:
        print(f"❌ НЕПРЕДВИДЕННАЯ ОШИБКА: {e}")

if __name__ == "__main__":
    asyncio.run(test_create_comment())