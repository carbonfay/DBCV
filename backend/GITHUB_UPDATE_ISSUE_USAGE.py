#!/usr/bin/env python3
"""
ИНСТРУКЦИЯ ПО ИСПОЛЬЗОВАНИЮ GitHub Update Issue ИНТЕГРАЦИИ

Этот файл содержит примеры кода для использования интеграции GitHub Update Issue
в вашей DBCV платформе.
"""

# ============================================================================
# ПРИМЕР 1: Базовое использование интеграции
# ============================================================================

async def example_basic_usage():
    """
    Базовый пример использования интеграции GitHub Update Issue.
    """
    from uuid import uuid4
    from app.integrations.registry import registry
    from app.auth.credentials_resolver import CredentialsResolver
    from app.loggers.bot import BotLogger
    
    # Получаем интеграцию из реестра
    integration = registry.get("github_update_issue")
    
    if not integration:
        print("❌ Интеграция 'github_update_issue' не найдена")
        return
    
    # Подготавливаем конфигурацию
    config = {
        "owner": "carbonfay",
        "repo": "DBCV",
        "issue_number": 1,
        "title": "Новое название Issue"
    }
    
    # Инициализируем зависимости (в реальном коде они будут внедрены)
    bot_id = uuid4()
    credentials_resolver = CredentialsResolver()
    logger = BotLogger()
    
    # Выполняем интеграцию
    result = await integration.execute(
        config=config,
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    # Проверяем результат
    if result["response"]["ok"]:
        print("✅ Issue обновлена успешно!")
        issue_info = result["response"]["result"]
        print(f"   Номер: #{issue_info['number']}")
        print(f"   Название: {issue_info['title']}")
        print(f"   Статус: {issue_info['state']}")
    else:
        print(f"❌ Ошибка: {result['response']['description']}")


# ============================================================================
# ПРИМЕР 2: Обновление названия и описания
# ============================================================================

async def example_update_title_and_body():
    """
    Обновление названия и описания Issue одновременно.
    """
    from uuid import uuid4
    from app.integrations.registry import registry
    
    integration = registry.get("github_update_issue")
    
    config = {
        "owner": "carbonfay",
        "repo": "DBCV",
        "issue_number": 1,
        "title": "Обновленное название",
        "body": """## Обновленное описание

### Проблема
Описание проблемы...

### Шаги воспроизведения
1. Шаг 1
2. Шаг 2

### Ожидаемый результат
Ожидаемый результат...
"""
    }
    
    result = await integration.execute(
        config=config,
        credentials_resolver=...,
        bot_id=uuid4(),
        logger=...
    )
    
    return result


# ============================================================================
# ПРИМЕР 3: Закрытие Issue
# ============================================================================

async def example_close_issue():
    """
    Закрыть Issue с указанием причины.
    """
    from uuid import uuid4
    from app.integrations.registry import registry
    
    integration = registry.get("github_update_issue")
    
    config = {
        "owner": "carbonfay",
        "repo": "DBCV",
        "issue_number": 1,
        "state": "closed",
        "state_reason": "completed"
    }
    
    result = await integration.execute(
        config=config,
        credentials_resolver=...,
        bot_id=uuid4(),
        logger=...
    )
    
    return result


# ============================================================================
# ПРИМЕР 4: Добавление labels и assignees
# ============================================================================

async def example_add_labels_and_assignees():
    """
    Добавить labels и assignees к Issue.
    """
    from uuid import uuid4
    from app.integrations.registry import registry
    
    integration = registry.get("github_update_issue")
    
    config = {
        "owner": "carbonfay",
        "repo": "DBCV",
        "issue_number": 1,
        "labels": ["bug", "enhancement", "high-priority"],
        "assignees": ["carbonfay", "other_developer"]
    }
    
    result = await integration.execute(
        config=config,
        credentials_resolver=...,
        bot_id=uuid4(),
        logger=...
    )
    
    return result


# ============================================================================
# ПРИМЕР 5: Переоткрытие закрытой Issue
# ============================================================================

async def example_reopen_issue():
    """
    Переоткрыть закрытую Issue (изменить статус с 'closed' на 'open').
    """
    from uuid import uuid4
    from app.integrations.registry import registry
    
    integration = registry.get("github_update_issue")
    
    config = {
        "owner": "carbonfay",
        "repo": "DBCV",
        "issue_number": 1,
        "state": "open"
    }
    
    result = await integration.execute(
        config=config,
        credentials_resolver=...,
        bot_id=uuid4(),
        logger=...
    )
    
    return result


# ============================================================================
# ПРИМЕР 6: Использование в обработчике сообщений бота
# ============================================================================

async def example_bot_message_handler(message, bot_id, credentials_resolver, logger):
    """
    Пример использования интеграции при обработке сообщения бота.
    
    Например, когда пользователь пишет в боте "/close-issue 123",
    бот должен закрыть Issue #123 на GitHub.
    """
    from app.integrations.registry import registry
    
    # Парсим команду
    if message.text.startswith("/close-issue"):
        issue_number = int(message.text.split()[1])
        
        # Получаем интеграцию
        integration = registry.get("github_update_issue")
        
        # Подготавливаем конфигурацию
        config = {
            "owner": "carbonfay",
            "repo": "DBCV",
            "issue_number": issue_number,
            "state": "closed",
            "state_reason": "completed"
        }
        
        # Выполняем интеграцию
        result = await integration.execute(
            config=config,
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Возвращаем результат пользователю
        if result["response"]["ok"]:
            return f"✅ Issue #{issue_number} закрыта успешно!"
        else:
            return f"❌ Ошибка: {result['response']['description']}"


# ============================================================================
# ПРИМЕР 7: Обработка всех типов ошибок
# ============================================================================

async def example_error_handling():
    """
    Полная обработка всех типов ошибок при использовании интеграции.
    """
    from uuid import uuid4
    from app.integrations.registry import registry
    
    integration = registry.get("github_update_issue")
    
    config = {
        "owner": "carbonfay",
        "repo": "DBCV",
        "issue_number": 1,
        "title": "Новое название"
    }
    
    result = await integration.execute(
        config=config,
        credentials_resolver=...,
        bot_id=uuid4(),
        logger=...
    )
    
    # Проверяем результат
    if not result["response"]["ok"]:
        error_code = result["response"].get("error_code", 500)
        error_desc = result["response"].get("description", "Unknown error")
        
        if error_code == 400:
            print(f"❌ Ошибка валидации: {error_desc}")
            print("   Проверьте параметры конфигурации")
        
        elif error_code == 401:
            print(f"❌ Ошибка аутентификации: {error_desc}")
            print("   Проверьте GitHub token в credentials")
        
        elif error_code == 403:
            print(f"❌ Ошибка доступа: {error_desc}")
            print("   Проверьте права token на репозиторий")
        
        elif error_code == 404:
            print(f"❌ Issue не найдена: {error_desc}")
            print("   Проверьте owner, repo и issue_number")
        
        elif error_code == 500:
            print(f"❌ Ошибка сервера: {error_desc}")
            print("   Проверьте установку PyGithub")
        
        else:
            print(f"❌ Неизвестная ошибка ({error_code}): {error_desc}")
    
    else:
        issue = result["response"]["result"]
        print(f"✅ Issue #{issue['number']} успешно обновлена")
        print(f"   Название: {issue['title']}")
        print(f"   Статус: {issue['state']}")
        print(f"   Последнее обновление: {issue['updated_at']}")


# ============================================================================
# ПРИМЕР 8: Динамическое обновление на основе webhook от GitHub
# ============================================================================

async def example_github_webhook_handler(webhook_payload, bot_id, credentials_resolver, logger):
    """
    Пример обработки webhook от GitHub и обновления Issue через интеграцию.
    
    Например, при создании комментария на Issue, можно автоматически
    добавить метку "commented".
    """
    from app.integrations.registry import registry
    
    # Парсим webhook
    if webhook_payload.action == "created" and webhook_payload.issue:
        issue_number = webhook_payload.issue.number
        
        # Получаем интеграцию
        integration = registry.get("github_update_issue")
        
        # Подготавливаем конфигурацию
        config = {
            "owner": webhook_payload.repository.owner.login,
            "repo": webhook_payload.repository.name,
            "issue_number": issue_number,
            "labels": ["commented"]
        }
        
        # Выполняем интеграцию
        result = await integration.execute(
            config=config,
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        return result


# ============================================================================
# ПРИМЕР 9: Пакетное обновление нескольких Issues
# ============================================================================

async def example_batch_update():
    """
    Обновление нескольких Issues одновременно.
    """
    from uuid import uuid4
    from app.integrations.registry import registry
    
    integration = registry.get("github_update_issue")
    
    # Список Issues для обновления
    issues_to_update = [
        {"number": 1, "title": "Updated 1"},
        {"number": 2, "title": "Updated 2"},
        {"number": 3, "title": "Updated 3"},
    ]
    
    results = []
    
    for issue in issues_to_update:
        config = {
            "owner": "carbonfay",
            "repo": "DBCV",
            "issue_number": issue["number"],
            "title": issue["title"]
        }
        
        result = await integration.execute(
            config=config,
            credentials_resolver=...,
            bot_id=uuid4(),
            logger=...
        )
        
        results.append(result)
    
    # Проверяем результаты
    successful = sum(1 for r in results if r["response"]["ok"])
    failed = len(results) - successful
    
    print(f"✅ Успешно обновлено: {successful}")
    print(f"❌ Ошибок: {failed}")
    
    return results


# ============================================================================
# ПРИМЕР 10: Условное обновление на основе текущего состояния Issue
# ============================================================================

async def example_conditional_update(bot_id, credentials_resolver, logger):
    """
    Получить текущую информацию об Issue и обновить ее на основе условия.
    """
    from app.integrations.registry import registry
    
    # Сначала получаем текущую информацию об Issue через get_issue интеграцию
    get_issue_integration = registry.get("github_get_issue")
    
    issue_config = {
        "owner": "carbonfay",
        "repo": "DBCV",
        "issue_number": 1
    }
    
    get_result = await get_issue_integration.execute(
        config=issue_config,
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    if not get_result["response"]["ok"]:
        return get_result
    
    current_issue = get_result["response"]["result"]
    
    # На основе текущего состояния решаем, что обновлять
    update_config = {
        "owner": "carbonfay",
        "repo": "DBCV",
        "issue_number": 1
    }
    
    # Если есть более 10 комментариев, добавляем метку "many-comments"
    if current_issue["comments"] > 10:
        existing_labels = current_issue["labels"]
        if "many-comments" not in existing_labels:
            update_config["labels"] = existing_labels + ["many-comments"]
    
    # Если Issue открыта более недели, добавляем метку "stale"
    import datetime
    created_at = datetime.datetime.fromisoformat(
        current_issue["created_at"].replace("Z", "+00:00")
    )
    if datetime.datetime.now(datetime.timezone.utc) - created_at > datetime.timedelta(days=7):
        if current_issue["state"] == "open":
            existing_labels = current_issue["labels"]
            if "stale" not in existing_labels:
                update_config["labels"] = existing_labels + ["stale"]
    
    # Выполняем интеграцию обновления
    update_integration = registry.get("github_update_issue")
    update_result = await update_integration.execute(
        config=update_config,
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    return update_result


# ============================================================================
# КОНСТАНТЫ И КОНФИГУРАЦИЯ
# ============================================================================

# Константы для интеграции
GITHUB_INTEGRATION_ID = "github_update_issue"
GITHUB_PROVIDER = "github"

# Доступные состояния Issue
ISSUE_STATES = {
    "open": "Открыта",
    "closed": "Закрыта"
}

# Доступные причины закрытия Issue
ISSUE_STATE_REASONS = {
    "completed": "Выполнено",
    "not_planned": "Не планируется"
}

# Стандартные метки
DEFAULT_LABELS = {
    "bug": "Ошибка",
    "enhancement": "Улучшение",
    "documentation": "Документация",
    "feature": "Новая функция",
    "help-wanted": "Нужна помощь",
    "high-priority": "Высокий приоритет",
    "wontfix": "Не будет исправлено"
}


# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

def validate_issue_config(config: dict) -> tuple[bool, str]:
    """
    Валидирует конфигурацию для обновления Issue.
    
    Returns:
        (is_valid, error_message)
    """
    required_fields = ["owner", "repo", "issue_number"]
    
    for field in required_fields:
        if field not in config or not config[field]:
            return False, f"Missing required field: {field}"
    
    if not isinstance(config["issue_number"], int) or config["issue_number"] <= 0:
        return False, "issue_number must be a positive integer"
    
    if "state" in config and config["state"] not in ["open", "closed"]:
        return False, "state must be 'open' or 'closed'"
    
    if "state_reason" in config and config["state_reason"] not in ["completed", "not_planned"]:
        return False, "state_reason must be 'completed' or 'not_planned'"
    
    if "labels" in config and not isinstance(config["labels"], list):
        return False, "labels must be a list"
    
    if "assignees" in config and not isinstance(config["assignees"], list):
        return False, "assignees must be a list"
    
    return True, ""


def format_issue_result(result: dict) -> str:
    """
    Форматирует результат обновления Issue для вывода.
    """
    if not result["response"]["ok"]:
        return f"❌ {result['response']['description']}"
    
    issue = result["response"]["result"]
    return f"""✅ Issue #{issue['number']} обновлена
Название: {issue['title']}
Статус: {issue['state']}
Метки: {', '.join(issue['labels']) if issue['labels'] else 'нет'}
Assignees: {', '.join(issue['assignees']) if issue['assignees'] else 'не назначена'}
Последнее обновление: {issue['updated_at']}
"""


# ============================================================================
# DOCUMENTATION / СПРАВКА
# ============================================================================

DOCUMENTATION = """
GitHub Update Issue Интеграция
==============================

ИСПОЛЬЗОВАНИЕ:
1. Получите интеграцию: registry.get("github_update_issue")
2. Подготовьте конфигурацию с требуемыми параметрами
3. Выполните: integration.execute(config, credentials_resolver, bot_id, logger)

ТРЕБУЕМЫЕ ПАРАМЕТРЫ:
- owner: Владелец репозитория (string)
- repo: Название репозитория (string)  
- issue_number: Номер Issue (integer, > 0)

ОПЦИОНАЛЬНЫЕ ПАРАМЕТРЫ (минимум один):
- title: Новое название (string)
- body: Новое описание (string)
- state: Новый статус - "open" или "closed" (string)
- state_reason: Причина закрытия - "completed" или "not_planned" (string)
- labels: Список меток (array[string])
- assignees: Список пользователей (array[string])

РЕЗУЛЬТАТ:
{
  "response": {
    "ok": true/false,
    "result": { /* информация об обновленной Issue */ },
    "error_code": /* в случае ошибки */,
    "description": /* описание ошибки */
  }
}

ПРИМЕРЫ ОШИБОК:
- 400: Bad Request - неверные параметры
- 401: Unauthorized - нет GitHub token
- 403: Forbidden - нет прав на репозиторий
- 404: Not Found - Issue не найдена
- 500: Internal Server Error - PyGithub не установлена
"""

if __name__ == "__main__":
    print(DOCUMENTATION)
