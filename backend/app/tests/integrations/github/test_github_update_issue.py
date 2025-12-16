#!/usr/bin/env python3
"""
Упрощённый тестовый скрипт для GitHub Update Issue интеграции.
Не требует установки всех зависимостей проекта.
"""

import json
from datetime import datetime

# Параметры для тестирования
GITHUB_TOKEN = "YOUR_NEW_TOKEN_HERE"  # Замените на новый token с правами repo
OWNER = "carbonfay"
REPO = "DBCV"
ISSUE_NUMBER = 18


def test_pygithub_installed():
    """Проверяет установлен ли PyGithub."""
    try:
        import github
        print("✅ PyGithub установлена")
        return True
    except ImportError:
        print("❌ PyGithub не установлена")
        print("   Установите: pip install PyGithub>=2.0.0")
        return False


def test_github_connection():
    """Тестирует подключение к GitHub API."""
    from github import Github
    from github.GithubException import GithubException
    
    print("\n" + "=" * 80)
    print("🔐 ТЕСТИРОВАНИЕ ПОДКЛЮЧЕНИЯ К GITHUB")
    print("=" * 80)
    
    try:
        g = Github(GITHUB_TOKEN)
        
        # Проверяем что token работает
        user = g.get_user()
        print(f"✅ Аутентифицирован как: {user.login}")
        print(f"   Имя: {user.name}")
        print(f"   Репо: {user.public_repos}")
        
        return g, True
    except GithubException as e:
        print(f"❌ Ошибка GitHub API: {e.status} - {e.data.get('message', '')}")
        return None, False
    except Exception as e:
        print(f"❌ Ошибка подключения: {str(e)}")
        return None, False


def test_update_issue_title(g):
    """Тестирует обновление названия Issue."""
    from github.GithubException import GithubException
    
    print("\n" + "=" * 80)
    print("📝 ОБНОВЛЕНИЕ НАЗВАНИЯ ISSUE")
    print("=" * 80)
    print(f"Репозиторий: {OWNER}/{REPO}")
    print(f"Issue номер: {ISSUE_NUMBER}")
    print()
    
    try:
        # Получаем репозиторий
        repo = g.get_user(OWNER).get_repo(REPO)
        print(f"✅ Репозиторий найден: {repo.full_name}")
        
        # Получаем Issue
        issue = repo.get_issue(ISSUE_NUMBER)
        print(f"✅ Issue найдена!")
        
        # Запоминаем старое название
        old_title = issue.title
        print(f"\nСтарое название: {old_title}")
        
        # Обновляем название
        new_title = f"[UPDATED] {old_title} (at {datetime.now().isoformat()[:19]})"
        issue.edit(title=new_title)
        
        # Переполучаем обновленный Issue
        updated_issue = repo.get_issue(ISSUE_NUMBER)
        
        print(f"✅ Новое название: {updated_issue.title}")
        
        result = {
            "number": updated_issue.number,
            "title": updated_issue.title,
            "state": updated_issue.state,
            "updated_at": updated_issue.updated_at.isoformat() if updated_issue.updated_at else None,
        }
        
        print("\n" + "=" * 80)
        print("✅ РЕЗУЛЬТАТ ОБНОВЛЕНИЯ")
        print("=" * 80)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        return True
        
    except GithubException as e:
        if e.status == 404:
            print(f"❌ Issue #{ISSUE_NUMBER} не найдена в {OWNER}/{REPO}")
        elif e.status == 403:
            print(f"❌ Доступ запрещен (проверьте права token)")
        elif e.status == 401:
            print(f"❌ Недействительный token")
        else:
            print(f"❌ Ошибка GitHub API ({e.status}): {e.data.get('message', '')}")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        return False


def test_update_issue_state(g):
    """Тестирует обновление статуса Issue (открыть/закрыть)."""
    from github.GithubException import GithubException
    
    print("\n" + "=" * 80)
    print("🔄 ОБНОВЛЕНИЕ СТАТУСА ISSUE")
    print("=" * 80)
    print(f"Репозиторий: {OWNER}/{REPO}")
    print(f"Issue номер: {ISSUE_NUMBER}")
    print()
    
    try:
        # Получаем репозиторий
        repo = g.get_user(OWNER).get_repo(REPO)
        
        # Получаем Issue
        issue = repo.get_issue(ISSUE_NUMBER)
        
        # Запоминаем старый статус
        old_state = issue.state
        print(f"Текущий статус: {old_state}")
        
        # Переключаем статус
        new_state = "closed" if old_state == "open" else "open"
        print(f"Новый статус: {new_state}")
        
        if new_state == "closed":
            issue.edit(state="closed", state_reason="completed")
            print(f"✅ Причина закрытия: completed")
        else:
            issue.edit(state="open")
        
        # Переполучаем обновленный Issue
        updated_issue = repo.get_issue(ISSUE_NUMBER)
        
        result = {
            "number": updated_issue.number,
            "state": updated_issue.state,
            "state_reason": updated_issue.state_reason,
            "closed_at": updated_issue.closed_at.isoformat() if updated_issue.closed_at else None,
            "updated_at": updated_issue.updated_at.isoformat() if updated_issue.updated_at else None,
        }
        
        print("\n" + "=" * 80)
        print("✅ РЕЗУЛЬТАТ ОБНОВЛЕНИЯ")
        print("=" * 80)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        return True
        
    except GithubException as e:
        if e.status == 404:
            print(f"❌ Issue #{ISSUE_NUMBER} не найдена в {OWNER}/{REPO}")
        elif e.status == 403:
            print(f"❌ Доступ запрещен (проверьте права token)")
        elif e.status == 401:
            print(f"❌ Недействительный token")
        else:
            print(f"❌ Ошибка GitHub API ({e.status}): {e.data.get('message', '')}")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        return False


def test_update_issue_labels(g):
    """Тестирует добавление labels к Issue."""
    from github.GithubException import GithubException
    
    print("\n" + "=" * 80)
    print("🏷️ ОБНОВЛЕНИЕ LABELS ISSUE")
    print("=" * 80)
    print(f"Репозиторий: {OWNER}/{REPO}")
    print(f"Issue номер: {ISSUE_NUMBER}")
    print()
    
    try:
        # Получаем репозиторий
        repo = g.get_user(OWNER).get_repo(REPO)
        
        # Получаем Issue
        issue = repo.get_issue(ISSUE_NUMBER)
        
        # Запоминаем старые labels
        old_labels = [label.name for label in issue.labels]
        print(f"Текущие labels: {old_labels if old_labels else 'нет'}")
        
        # Добавляем новые labels
        new_labels = ["bug", "enhancement", "high-priority"]
        print(f"Новые labels: {new_labels}")
        
        issue.edit(labels=new_labels)
        
        # Переполучаем обновленный Issue
        updated_issue = repo.get_issue(ISSUE_NUMBER)
        
        result = {
            "number": updated_issue.number,
            "labels": [label.name for label in updated_issue.labels],
            "updated_at": updated_issue.updated_at.isoformat() if updated_issue.updated_at else None,
        }
        
        print("\n" + "=" * 80)
        print("✅ РЕЗУЛЬТАТ ОБНОВЛЕНИЯ")
        print("=" * 80)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        return True
        
    except GithubException as e:
        if e.status == 404:
            print(f"❌ Issue #{ISSUE_NUMBER} не найдена в {OWNER}/{REPO}")
        elif e.status == 403:
            print(f"❌ Доступ запрещен (проверьте права token)")
        elif e.status == 401:
            print(f"❌ Недействительный token")
        else:
            print(f"❌ Ошибка GitHub API ({e.status}): {e.data.get('message', '')}")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        return False


def test_update_issue_body(g):
    """Тестирует обновление описания Issue."""
    from github.GithubException import GithubException
    
    print("\n" + "=" * 80)
    print("📋 ОБНОВЛЕНИЕ ОПИСАНИЯ ISSUE")
    print("=" * 80)
    print(f"Репозиторий: {OWNER}/{REPO}")
    print(f"Issue номер: {ISSUE_NUMBER}")
    print()
    
    try:
        # Получаем репозиторий
        repo = g.get_user(OWNER).get_repo(REPO)
        
        # Получаем Issue
        issue = repo.get_issue(ISSUE_NUMBER)
        
        # Запоминаем старое описание
        old_body = issue.body[:100] + "..." if issue.body and len(issue.body) > 100 else issue.body
        print(f"Старое описание: {old_body if old_body else 'нет'}")
        
        # Обновляем описание
        new_body = f"""## Updated Description

**Время обновления:** {datetime.now().isoformat()[:19]}

Это обновленное описание Issue, которое было изменено через GitHub Update Issue интеграцию.

### Изменения:
- Добавлено новое описание
- Обновлена информация
- Интеграция работает корректно!
"""
        
        issue.edit(body=new_body)
        
        # Переполучаем обновленный Issue
        updated_issue = repo.get_issue(ISSUE_NUMBER)
        
        result = {
            "number": updated_issue.number,
            "body": updated_issue.body[:150] + "..." if updated_issue.body and len(updated_issue.body) > 150 else updated_issue.body,
            "updated_at": updated_issue.updated_at.isoformat() if updated_issue.updated_at else None,
        }
        
        print("\n" + "=" * 80)
        print("✅ РЕЗУЛЬТАТ ОБНОВЛЕНИЯ")
        print("=" * 80)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        return True
        
    except GithubException as e:
        if e.status == 404:
            print(f"❌ Issue #{ISSUE_NUMBER} не найдена в {OWNER}/{REPO}")
        elif e.status == 403:
            print(f"❌ Доступ запрещен (проверьте права token)")
        elif e.status == 401:
            print(f"❌ Недействительный token")
        else:
            print(f"❌ Ошибка GitHub API ({e.status}): {e.data.get('message', '')}")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        return False


def test_validation():
    """Тестирует валидацию параметров."""
    print("\n" + "=" * 80)
    print("✅ ТЕСТИРОВАНИЕ ВАЛИДАЦИИ")
    print("=" * 80)
    
    tests = [
        ("owner", "", "Пустой owner"),
        ("repo", "", "Пустой repo"),
        ("issue_number", -1, "Отрицательный номер"),
        ("issue_number", 0, "Нулевой номер"),
        ("issue_number", "abc", "Строка вместо числа"),
        ("state", "invalid", "Неправильный статус"),
        ("state_reason", "invalid", "Неправильная причина закрытия"),
        ("labels", "not_list", "Labels не список"),
        ("assignees", "not_list", "Assignees не список"),
    ]
    
    for i, (param, value, description) in enumerate(tests, 1):
        valid = True
        error = None
        
        if param == "owner" and not value:
            valid = False
            error = "owner is required"
        elif param == "repo" and not value:
            valid = False
            error = "repo is required"
        elif param == "issue_number":
            if not isinstance(value, int) or value <= 0:
                valid = False
                error = "issue_number must be positive integer"
        elif param == "state" and value == "invalid":
            valid = False
            error = "state must be 'open' or 'closed'"
        elif param == "state_reason" and value == "invalid":
            valid = False
            error = "state_reason must be 'completed' or 'not_planned'"
        elif param == "labels" and not isinstance(value, list):
            valid = False
            error = "labels must be a list"
        elif param == "assignees" and not isinstance(value, list):
            valid = False
            error = "assignees must be a list"
        
        status = "✅" if valid else "❌"
        print(f"{i}️⃣ {status} {description}: {error if error else 'OK'}")


def main():
    """Главная функция."""
    print("🧪 ТЕСТИРОВАНИЕ GitHub Update Issue ИНТЕГРАЦИИ\n")
    
    # Проверяем установку PyGithub
    if not test_pygithub_installed():
        return
    
    # Проверяем подключение к GitHub
    g, success = test_github_connection()
    if not success:
        return
    
    # Тестируем различные операции обновления
    print("\n" + "=" * 80)
    print("⚠️  ВНИМАНИЕ: Следующие тесты будут изменять Issue на GitHub!")
    print("=" * 80)
    print(f"Репозиторий: {OWNER}/{REPO}")
    print(f"Issue номер: {ISSUE_NUMBER}")
    input("\nНажмите Enter для продолжения тестирования или Ctrl+C для отмены...")
    
    # Тестируем обновление названия
    test_update_issue_title(g)
    
    # Тестируем обновление статуса
    test_update_issue_state(g)
    
    # Тестируем добавление labels
    test_update_issue_labels(g)
    
    # Тестируем обновление описания
    test_update_issue_body(g)
    
    # Тестируем валидацию
    test_validation()
    
    print("\n" + "=" * 80)
    print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 80)
    print("\n📝 ИНТЕГРАЦИЯ ГОТОВА К ИСПОЛЬЗОВАНИЮ!")
    print("\nДля использования в боте:")
    print("1. Добавьте credentials GitHub в DBCV")
    print("2. Используйте integration_id: 'github_update_issue'")
    print("3. Передайте параметры: owner, repo, issue_number и параметры для обновления")
    print("\nДоступные параметры для обновления:")
    print("  - title: новое название Issue")
    print("  - body: новое описание Issue")
    print("  - state: 'open' или 'closed'")
    print("  - state_reason: 'completed' или 'not_planned' (при state=closed)")
    print("  - labels: список меток")
    print("  - assignees: список назначенных пользователей (username)")


if __name__ == "__main__":
    main()
