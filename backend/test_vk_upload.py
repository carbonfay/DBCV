#!/usr/bin/env python3
"""
Тестовый скрипт для проверки интеграции VK Upload Photo.
Позволяет ввести access_token, путь к фото, group_id и caption,
затем загружает фото и публикует пост на стене группы.
"""

import os
import sys

try:
    import vk_api
    from vk_api.exceptions import VkApiError
    VK_API_AVAILABLE = True
except ImportError:
    print("❌ Ошибка: vk-api не установлена. Установите командой: pip install vk-api>=11.9.9")
    VK_API_AVAILABLE = False
    sys.exit(1)

def test_vk_upload():
    print("🧪 Тест интеграции VK Upload Photo")
    print("=" * 50)

    # Ввод данных
    access_token = input("Введите access_token бота VK: ").strip()
    if not access_token:
        print("❌ Ошибка: access_token обязателен")
        return

    photo_path = input("Введите путь к фото файлу: ").strip()
    if not photo_path or not os.path.isfile(photo_path):
        print(f"❌ Ошибка: Файл не найден: {photo_path}")
        return

    group_id_input = input("Введите ID группы (без минуса, например 123456789): ").strip()
    try:
        group_id = int(group_id_input) if group_id_input else None
    except ValueError:
        print("❌ Ошибка: group_id должен быть числом")
        return

    caption = input("Введите текст поста (caption): ").strip()

    print("\n🔄 Выполняем тест...")

    try:
        # Инициализация VK API
        print("🔗 Подключаемся к VK API...")
        vk_session = vk_api.VkApi(token=access_token)
        vk = vk_session.get_api()
        upload = vk_api.VkUpload(vk_session)
        print("✅ Подключение к VK API успешно")

        # Простая проверка типа токена: попробуем вызвать метод пользователя.
        is_group_token = False
        try:
            vk.users.get()
            print("🔒 Тип токена: пользовательский (user token) — методы пользователя доступны")
        except VkApiError as e_check:
            err_text = str(e_check).lower()
            err_code = getattr(e_check, "error_code", None)
            if err_code == 27 or "method is unavailable with group auth" in err_text or "group authorization failed" in err_text:
                is_group_token = True
                print("🔒 Тип токена: токен сообщества (group token) — некоторые методы пользователя недоступны")
            else:
                print(f"⚠️ Невозможно однозначно определить тип токена: {e_check}")

        # Пропускаем проверку пользователя для group tokens

        # Загрузка фото на стену группы
        print(f"📤 Загружаем фото: {photo_path}")
        print(f"📍 Группа ID: {group_id}")
        
        photo_list = upload.photo_wall(
            photos=photo_path,
            group_id=group_id
        )

        if not photo_list:
            print("❌ Ошибка: VK вернул пустой список фото")
            return

        photo_info = photo_list[0]
        owner_id = photo_info["owner_id"]
        photo_id = photo_info["id"]
        attachment = f"photo{owner_id}_{photo_id}"

        print(f"✅ Фото загружено: {attachment}")
        print(f"📊 Owner ID: {owner_id}, Photo ID: {photo_id}")

        # Публикация поста
        if caption.strip():
            print(f"📝 Публикуем пост с текстом: '{caption}'")
        else:
            print("📝 Публикуем пост без текста")

        target_owner_id = -group_id if group_id else owner_id
        print(f"🎯 Цель публикации: {target_owner_id}")

        post_kwargs = {
            "owner_id": target_owner_id,
            "message": caption,
            "attachments": attachment,
        }

        if group_id or is_group_token:
            post_kwargs["from_group"] = 1

        try:
            post_result = vk.wall.post(**post_kwargs)
            post_id = post_result.get("post_id")
            print(f"✅ Пост опубликован! ID поста: {post_id}")

            if group_id:
                link = f"https://vk.com/wall-{group_id}_{post_id}"
            else:
                link = f"https://vk.com/wall{owner_id}_{post_id}"

            print(f"🔗 Ссылка на пост: {link}")
            print("\n🎉 Тест пройден успешно! Интеграция работает корректно.")

        except VkApiError as e:
            error_code = getattr(e, "error_code", None)
            print(f"❌ Ошибка VK API (код {error_code}): {e}")

            if error_code == 27 or "method is unavailable with group auth" in str(e).lower():
                print("💡 Ошибка 27: Метод недоступен при групповом токене. Возможные причины:")
                print("- Токен сообщества не имеет нужных прав или доступ через API не включен для сообщества.")
                print("- Этот метод нельзя вызывать с текущим типом авторизации.")
                print("Решения:")
                print("- Используйте пользовательский токен (user access_token) с правами photos и wall.")
                print("- Либо убедитесь, что токен сообщества выдан для нужного сообщества и у сообщества включён доступ через API и права публикации.")
            elif error_code == 5:
                print("💡 Ошибка авторизации: Проверьте access_token")
            elif error_code == 15:
                print("💡 Доступ запрещен: Бот не имеет прав на публикацию")
            elif error_code == 100:
                print("💡 Ошибка параметров: Проверьте group_id и формат данных")
            elif error_code == 200:
                print("💡 Доступ к альбому запрещен: Проверьте права бота")
            else:
                print("💡 Подробности ошибки смотрите в документации VK API")

            return

    except VkApiError as e:
        error_code = getattr(e, "error_code", "неизвестен")
        print(f"❌ Ошибка VK API (код {error_code}): {e}")
        
        # Расшифровка распространенных ошибок
        if error_code == 5:
            print("💡 Ошибка авторизации: Проверьте access_token")
        elif error_code == 15:
            print("💡 Доступ запрещен: Бот не имеет прав на публикацию")
        elif error_code == 100:
            print("💡 Ошибка параметров: Проверьте group_id и формат данных")
        elif error_code == 200:
            print("💡 Доступ к альбому запрещен: Проверьте права бота")
        else:
            print("💡 Подробности ошибки смотрите в документации VK API")
            
    except FileNotFoundError:
        print(f"❌ Ошибка: Файл не найден: {photo_path}")
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_vk_upload()