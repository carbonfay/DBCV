#!/usr/bin/env python3
"""
Скрипт для проверки прав GitHub Personal Access Token
"""

from github import Github
from github.GithubException import GithubException

# Ваш token
TOKEN = "YOUR_TOKEN_HERE"

def check_token_scopes():
    """Проверяет права и возможности token."""
    try:
        g = Github(TOKEN)
        
        # Информация о пользователе
        user = g.get_user()
        print(f"✅ Аутентифицирован как: {user.login}")
        print(f"   Имя: {user.name}")
        print(f"   Email: {user.email}")
        
        # Проверяем репозитории
        repos = list(user.get_repos())
        print(f"\n✅ Доступные репозитории: {len(repos)}")
        
        # Проверяем конкретный репозиторий
        try:
            repo = g.get_user("carbonfay").get_repo("DBCV")
            print(f"\n✅ Найден репозиторий: {repo.full_name}")
            print(f"   Permissions: {repo.permissions}")
            
            # Проверяем права на редактирование Issues
            if repo.permissions.push or repo.permissions.maintain or repo.permissions.admin:
                print(f"   ✅ Права на редактирование Issues: ДА")
            else:
                print(f"   ❌ Права на редактирование Issues: НЕТ")
                print(f"   Push: {repo.permissions.push}")
                print(f"   Maintain: {repo.permissions.maintain}")
                print(f"   Admin: {repo.permissions.admin}")
        
        except GithubException as e:
            print(f"\n❌ Не могу получить доступ к репозиторию:")
            print(f"   Ошибка: {e.status} - {e.data.get('message', '')}")
        
        # Пробуем получить Issue
        try:
            repo = g.get_user("carbonfay").get_repo("DBCV")
            issue = repo.get_issue(18)
            print(f"\n✅ Найдена Issue: #{issue.number}")
            print(f"   Название: {issue.title}")
            print(f"   Статус: {issue.state}")
            
            # Пробуем обновить (если есть права)
            if repo.permissions.push or repo.permissions.maintain or repo.permissions.admin:
                print(f"\n🔍 Пробуем обновить Issue...")
                issue.edit(body="Test update")
                print(f"   ✅ Успешно обновили Issue!")
            else:
                print(f"\n❌ Нет прав на обновление Issues")
        
        except GithubException as e:
            print(f"\n❌ Ошибка при работе с Issue:")
            print(f"   Статус: {e.status}")
            print(f"   Сообщение: {e.data.get('message', '')}")
    
    except Exception as e:
        print(f"❌ Критическая ошибка: {str(e)}")

if __name__ == "__main__":
    print("=" * 80)
    print("🔍 ПРОВЕРКА GITHUB TOKEN ПРАВ")
    print("=" * 80)
    print()
    
    if TOKEN == "YOUR_TOKEN_HERE":
        print("❌ Ошибка: Замените YOUR_TOKEN_HERE на реальный token!")
        exit(1)
    
    check_token_scopes()
    
    print("\n" + "=" * 80)
    print("📋 ТРЕБУЕМЫЕ ПРАВА ДЛЯ ОБНОВЛЕНИЯ ISSUES:")
    print("=" * 80)
    print("""
✅ SCOPES CHECKLIST:
  ✓ repo - Full control of private repositories
    - Позволяет читать и писать в репозитории
    - Необходимо для обновления Issues
  
  ✓ workflow (опционально) - Update GitHub Actions workflows
  
  ✓ admin:org_hook (опционально) - Full control of organization hooks

❌ НЕ ДОСТАТОЧНО:
  ✗ public_repo - Только чтение публичных репозиториев
  ✗ read:user - Только чтение информации пользователя
""")
