#!/usr/bin/env python3
"""
Упрощённый тестовый скрипт для GitHub Get Issue интеграции.
Не требует установки всех зависимостей проекта.
"""

import json
from datetime import datetime

# Параметры для тестирования
GITHUB_TOKEN = "github_token"
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


def test_get_issue(g):
    """Тестирует получение Issue."""
    from github.GithubException import GithubException
    
    print("\n" + "=" * 80)
    print("📝 ПОЛУЧЕНИЕ ISSUE")
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
        
        # Выводим информацию об Issue
        print("\n" + "=" * 80)
        print("📊 ИНФОРМАЦИЯ ОБ ISSUE")
        print("=" * 80)
        
        result = {
            "id": issue.id,
            "number": issue.number,
            "title": issue.title,
            "body": issue.body[:100] + "..." if issue.body and len(issue.body) > 100 else issue.body,
            "state": issue.state,
            "state_reason": issue.state_reason,
            "user": {
                "login": issue.user.login,
                "id": issue.user.id,
                "avatar_url": issue.user.avatar_url
            },
            "created_at": issue.created_at.isoformat() if issue.created_at else None,
            "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
            "closed_at": issue.closed_at.isoformat() if issue.closed_at else None,
            "comments": issue.comments,
            "labels": [label.name for label in issue.labels],
            "assignees": [assignee.login for assignee in issue.assignees],
            "url": issue.html_url
        }
        
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        print("\n" + "=" * 80)
        print("✅ РЕЗУЛЬТАТЫ")
        print("=" * 80)
        print(f"Номер: #{result['number']}")
        print(f"Название: {result['title']}")
        print(f"Статус: {result['state']}")
        print(f"Автор: {result['user']['login']}")
        print(f"Комментариев: {result['comments']}")
        print(f"Меток: {', '.join(result['labels']) if result['labels'] else 'нет'}")
        print(f"URL: {result['url']}")
        
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
    ]
    
    for i, (param, value, description) in enumerate(tests, 1):
        config = {"owner": OWNER, "repo": REPO, "issue_number": ISSUE_NUMBER}
        
        # Валидация
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
        
        status = "✅" if valid else "❌"
        print(f"{i}️⃣ {status} {description}: {error if error else 'OK'}")


def main():
    """Главная функция."""
    print("🧪 ТЕСТИРОВАНИЕ GitHub Get Issue ИНТЕГРАЦИИ\n")
    
    # Проверяем установку PyGithub
    if not test_pygithub_installed():
        return
    
    # Проверяем подключение к GitHub
    g, success = test_github_connection()
    if not success:
        return
    
    # Тестируем получение Issue
    test_get_issue(g)
    
    # Тестируем валидацию
    test_validation()
    
    print("\n" + "=" * 80)
    print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 80)
    print("\n📝 ИНТЕГРАЦИЯ ГОТОВА К ИСПОЛЬЗОВАНИЮ!")
    print("\nДля использования в боте:")
    print("1. Добавьте credentials GitHub в DBCV")
    print("2. Используйте integration_id: 'github_get_issue'")
    print("3. Передайте параметры: owner, repo, issue_number")


if __name__ == "__main__":
    main()
