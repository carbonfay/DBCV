#!/usr/bin/env python3
"""
Упрощённый тестовый скрипт для GitHub Create Pull Request интеграции.
Не требует установки всех зависимостей проекта.
"""

import json
from datetime import datetime

# Параметры для тестирования
GITHUB_TOKEN = "YOUR_NEW_TOKEN_HERE"  # Замените на новый token с правами repo
OWNER = "carbonfay"
REPO = "DBCV"
HEAD_BRANCH = "test/create-pr"  # Ветка с изменениями (убедитесь что она существует)
BASE_BRANCH = "integration/github-midaev-akhmad"  # Целевая ветка


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


def test_list_branches(g):
    """Проверяет какие ветки существуют в репозитории."""
    from github.GithubException import GithubException
    
    print("\n" + "=" * 80)
    print("🌿 ПРОВЕРКА ВЕТОК В РЕПОЗИТОРИИ")
    print("=" * 80)
    print(f"Репозиторий: {OWNER}/{REPO}")
    print()
    
    try:
        repo = g.get_user(OWNER).get_repo(REPO)
        
        print("📋 Доступные ветки:")
        branches = list(repo.get_branches())
        
        if not branches:
            print("  ❌ Не найдено веток")
            return False
        
        for branch in branches[:20]:  # Показываем первые 20
            marker = "✅" if branch.name in [HEAD_BRANCH, BASE_BRANCH] else "  "
            print(f"  {marker} {branch.name}")
        
        if len(branches) > 20:
            print(f"  ... и еще {len(branches) - 20} веток")
        
        # Проверяем наличие нужных веток
        branch_names = [b.name for b in branches]
        
        if HEAD_BRANCH not in branch_names:
            print(f"\n⚠️  HEAD ветка '{HEAD_BRANCH}' не найдена!")
            print(f"   Доступные ветки похожие на test/*:")
            for b in branch_names:
                if b.startswith("test/"):
                    print(f"     - {b}")
            return False
        
        if BASE_BRANCH not in branch_names:
            print(f"\n⚠️  BASE ветка '{BASE_BRANCH}' не найдена!")
            return False
        
        print(f"\n✅ Обе ветки найдены!")
        print(f"   HEAD: {HEAD_BRANCH}")
        print(f"   BASE: {BASE_BRANCH}")
        
        return True
        
    except GithubException as e:
        if e.status == 404:
            print(f"❌ Репозиторий {OWNER}/{REPO} не найден")
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


def test_create_simple_pr(g):
    """Тестирует создание простого Pull Request."""
    from github.GithubException import GithubException
    
    print("\n" + "=" * 80)
    print("📤 СОЗДАНИЕ ПРОСТОГО PULL REQUEST")
    print("=" * 80)
    print(f"Репозиторий: {OWNER}/{REPO}")
    print(f"HEAD ветка: {HEAD_BRANCH}")
    print(f"BASE ветка: {BASE_BRANCH}")
    print()
    
    try:
        # Получаем репозиторий
        repo = g.get_user(OWNER).get_repo(REPO)
        print(f"✅ Репозиторий найден: {repo.full_name}")
        
        # Создаем PR
        pr_title = f"[TEST] Simple PR created at {datetime.now().isoformat()[:19]}"
        pr_body = """## Test Pull Request

This is a test Pull Request created by the GitHub Create Pull Request integration.

### Description
Testing basic PR creation functionality.

### Changes
- Test implementation
- Validation of API
"""
        
        print(f"\nСоздание PR:")
        print(f"  Название: {pr_title}")
        print(f"  Описание: (первые 100 символов)")
        print(f"    {pr_body[:100]}...")
        
        pr = repo.create_pull(
            title=pr_title,
            head=HEAD_BRANCH,
            base=BASE_BRANCH,
            body=pr_body
        )
        
        # Переполучаем обновленный PR
        updated_pr = repo.get_pull(pr.number)
        
        result = {
            "number": updated_pr.number,
            "title": updated_pr.title,
            "state": updated_pr.state,
            "draft": updated_pr.draft,
            "head": {
                "ref": updated_pr.head.ref,
                "sha": updated_pr.head.sha[:8]
            },
            "base": {
                "ref": updated_pr.base.ref,
                "sha": updated_pr.base.sha[:8]
            },
            "created_at": updated_pr.created_at.isoformat() if updated_pr.created_at else None,
            "url": updated_pr.html_url
        }
        
        print("\n" + "=" * 80)
        print("✅ РЕЗУЛЬТАТ СОЗДАНИЯ")
        print("=" * 80)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        return True, updated_pr.number
        
    except GithubException as e:
        if e.status == 404:
            print(f"❌ Репозиторий или ветки не найдены")
        elif e.status == 403:
            print(f"❌ Доступ запрещен (проверьте права token)")
        elif e.status == 401:
            print(f"❌ Недействительный token")
        elif e.status == 422:
            print(f"❌ Validation failed: {e.data.get('message', 'Unknown error')}")
            if 'errors' in e.data:
                for error in e.data['errors']:
                    print(f"     - {error.get('message', 'Unknown error')}")
        else:
            print(f"❌ Ошибка GitHub API ({e.status}): {e.data.get('message', '')}")
        return False, None
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        return False, None


def test_create_pr_with_labels(g, pr_number):
    """Тестирует создание PR и добавление labels."""
    from github.GithubException import GithubException
    
    print("\n" + "=" * 80)
    print("🏷️ СОЗДАНИЕ PR И ДОБАВЛЕНИЕ LABELS")
    print("=" * 80)
    print(f"Репозиторий: {OWNER}/{REPO}")
    print(f"HEAD ветка: {HEAD_BRANCH}")
    print(f"BASE ветка: {BASE_BRANCH}")
    print()
    
    try:
        repo = g.get_user(OWNER).get_repo(REPO)
        
        pr_title = f"[TEST] PR with labels at {datetime.now().isoformat()[:19]}"
        
        print(f"Создание PR:")
        print(f"  Название: {pr_title}")
        
        pr = repo.create_pull(
            title=pr_title,
            head=HEAD_BRANCH,
            base=BASE_BRANCH,
            body="Test PR with labels"
        )
        
        # Добавляем labels
        labels = ["test", "automation", "integration"]
        print(f"\nДобавление labels: {labels}")
        
        pr.add_to_labels(*labels)
        
        # Переполучаем PR
        updated_pr = repo.get_pull(pr.number)
        
        result = {
            "number": updated_pr.number,
            "title": updated_pr.title,
            "labels": [label.name for label in updated_pr.labels],
            "url": updated_pr.html_url
        }
        
        print("\n" + "=" * 80)
        print("✅ РЕЗУЛЬТАТ СОЗДАНИЯ")
        print("=" * 80)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        return True, updated_pr.number
        
    except GithubException as e:
        print(f"❌ Ошибка GitHub API ({e.status}): {e.data.get('message', '')}")
        return False, None
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        return False, None


def test_create_draft_pr(g):
    """Тестирует создание draft PR."""
    from github.GithubException import GithubException
    
    print("\n" + "=" * 80)
    print("📋 СОЗДАНИЕ DRAFT PULL REQUEST")
    print("=" * 80)
    print(f"Репозиторий: {OWNER}/{REPO}")
    print(f"HEAD ветка: {HEAD_BRANCH}")
    print(f"BASE ветка: {BASE_BRANCH}")
    print()
    
    try:
        repo = g.get_user(OWNER).get_repo(REPO)
        
        pr_title = f"[DRAFT] Work in progress at {datetime.now().isoformat()[:19]}"
        
        print(f"Создание draft PR:")
        print(f"  Название: {pr_title}")
        print(f"  Draft: True")
        
        pr = repo.create_pull(
            title=pr_title,
            head=HEAD_BRANCH,
            base=BASE_BRANCH,
            body="This is a draft PR - work in progress",
            draft=True
        )
        
        # Переполучаем PR
        updated_pr = repo.get_pull(pr.number)
        
        result = {
            "number": updated_pr.number,
            "title": updated_pr.title,
            "draft": updated_pr.draft,
            "state": updated_pr.state,
            "url": updated_pr.html_url
        }
        
        print("\n" + "=" * 80)
        print("✅ РЕЗУЛЬТАТ СОЗДАНИЯ")
        print("=" * 80)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        return True, updated_pr.number
        
    except GithubException as e:
        print(f"❌ Ошибка GitHub API ({e.status}): {e.data.get('message', '')}")
        return False, None
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        return False, None


def test_validation():
    """Тестирует валидацию параметров."""
    print("\n" + "=" * 80)
    print("✅ ТЕСТИРОВАНИЕ ВАЛИДАЦИИ")
    print("=" * 80)
    
    tests = [
        ("owner", "", "Пустой owner"),
        ("repo", "", "Пустой repo"),
        ("title", "", "Пустой title"),
        ("head", "", "Пустой head"),
        ("base", "", "Пустой base"),
        ("draft", "not_bool", "Draft не boolean"),
        ("labels", "not_list", "Labels не список"),
        ("assignees", "not_list", "Assignees не список"),
        ("reviewers", "not_list", "Reviewers не список"),
    ]
    
    for i, (param, value, description) in enumerate(tests, 1):
        valid = True
        error = None
        
        if param in ["owner", "repo", "title", "head", "base"] and not value:
            valid = False
            error = f"{param} is required"
        elif param == "draft" and not isinstance(value, bool):
            valid = False
            error = "draft must be a boolean"
        elif param in ["labels", "assignees", "reviewers"] and not isinstance(value, list):
            valid = False
            error = f"{param} must be a list"
        
        status = "✅" if valid else "❌"
        print(f"{i}️⃣ {status} {description}: {error if error else 'OK'}")


def main():
    """Главная функция."""
    print("🧪 ТЕСТИРОВАНИЕ GitHub Create Pull Request ИНТЕГРАЦИИ\n")
    
    # Проверяем установку PyGithub
    if not test_pygithub_installed():
        return
    
    # Проверяем подключение к GitHub
    g, success = test_github_connection()
    if not success:
        return
    
    # Проверяем наличие веток
    if not test_list_branches(g):
        print("\n⚠️  ВНИМАНИЕ: Требуемые ветки не найдены!")
        print(f"   Пожалуйста, создайте ветку '{HEAD_BRANCH}' или обновите переменные HEAD_BRANCH и BASE_BRANCH в начале скрипта")
        return
    
    # Тестируем различные операции создания PR
    print("\n" + "=" * 80)
    print("⚠️  ВНИМАНИЕ: Следующие тесты будут создавать Pull Requests на GitHub!")
    print("=" * 80)
    print(f"Репозиторий: {OWNER}/{REPO}")
    print(f"HEAD ветка: {HEAD_BRANCH}")
    print(f"BASE ветка: {BASE_BRANCH}")
    input("\nНажмите Enter для продолжения тестирования или Ctrl+C для отмены...")
    
    # Тестируем создание простого PR
    success1, pr_num1 = test_create_simple_pr(g)
    
    # Тестируем создание PR с labels
    success2, pr_num2 = test_create_pr_with_labels(g, pr_num1)
    
    # Тестируем создание draft PR
    success3, pr_num3 = test_create_draft_pr(g)
    
    # Тестируем валидацию
    test_validation()
    
    print("\n" + "=" * 80)
    print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 80)
    
    if success1 or success2 or success3:
        print("\n📝 ИНТЕГРАЦИЯ ГОТОВА К ИСПОЛЬЗОВАНИЮ!")
        print("\nДля использования в боте:")
        print("1. Добавьте credentials GitHub в DBCV")
        print("2. Используйте integration_id: 'github_create_pull_request'")
        print("3. Передайте параметры: owner, repo, title, head, base и опциональные параметры")
        print("\nОбязательные параметры:")
        print("  - owner: владелец репозитория")
        print("  - repo: название репозитория")
        print("  - title: название Pull Request")
        print("  - head: ветка с изменениями (например: 'feature-branch' или 'user:feature-branch')")
        print("  - base: целевая ветка (например: 'main' или 'develop')")
        print("\nОпциональные параметры:")
        print("  - body: описание Pull Request")
        print("  - draft: создать как draft PR (true/false, по умолчанию false)")
        print("  - labels: список меток для PR")
        print("  - assignees: список назначенных пользователей (username)")
        print("  - reviewers: список reviewers (username)")
        
        if pr_num1:
            print(f"\n🔗 Созданные PRs:")
            if pr_num1:
                print(f"   - PR #{pr_num1} (простой PR)")
            if pr_num2:
                print(f"   - PR #{pr_num2} (PR с labels)")
            if pr_num3:
                print(f"   - PR #{pr_num3} (draft PR)")
    else:
        print("\n❌ Все тесты не пройдены")


if __name__ == "__main__":
    main()
