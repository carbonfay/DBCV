#!/usr/bin/env python3
"""
Скрипт для проверки статуса тестов интеграции VK Create Comment.
Выводит: работает или нет.
"""

import subprocess
import sys

def check_tests():
    """Запускает тесты и проверяет статус."""
    try:
        # Запуск pytest для нашего тестового файла
        result = subprocess.run([
            sys.executable, '-m', 'pytest',
            'app/tests/integrations/test_vk_comment_standalone.py',
            '-v', '--tb=short'
        ], capture_output=True, text=True, cwd='.')

        # Проверяем код выхода
        if result.returncode == 0:
            print("✅ СТАТУС: РАБОТАЕТ")
            print("Все тесты прошли успешно!")
            print(f"Количество пройденных тестов: {result.stdout.count('PASSED')}")
        else:
            print("❌ СТАТУС: НЕ РАБОТАЕТ")
            print("Некоторые тесты провалились.")
            print("\nВывод ошибок:")
            print(result.stdout)
            print(result.stderr)

        return result.returncode == 0

    except Exception as e:
        print(f"❌ СТАТУС: ОШИБКА ЗАПУСКА")
        print(f"Не удалось запустить тесты: {e}")
        return False

if __name__ == "__main__":
    success = check_tests()
    sys.exit(0 if success else 1)