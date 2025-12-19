"""Parallel Preset для DBCV - позволяет создать параллельное выполнение задач."""
from typing import Dict, Any, List
from uuid import UUID

from app.integrations.base import IntegrationMetadata
from app.presets.base import BasePreset
from app.models.step import StepModel
from app.models.connection_group import ConnectionGroupModel
from app.models.connection import ConnectionModel
from app.models.message import MessageModel


class ParallelPreset(BasePreset):
    """Пресет для создания параллельного выполнения задач."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="parallel_preset",
            version="1.0.0",
            name="Parallel",
            description="Параллельное выполнение нескольких задач",
            category="logic",
            icon_s3_key="icons/presets/parallel.svg",
            color="#4ECDC4",
            config_schema={
                "type": "object",
                "required": ["tasks"],
                "properties": {
                    "tasks": {
                        "type": "array",
                        "title": "Tasks",
                        "description": "Список задач для параллельного выполнения",
                        "items": {
                            "type": "object",
                            "required": ["name", "type"],
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "title": "Task Name",
                                    "description": "Название задачи"
                                },
                                "type": {
                                    "type": "string",
                                    "title": "Task Type",
                                    "description": "Тип задачи",
                                    "enum": ["http", "code", "integration"]
                                },
                                "config": {
                                    "type": "object",
                                    "title": "Task Configuration",
                                    "description": "Конфигурация задачи"
                                }
                            }
                        }
                    },
                    "timeout": {
                        "type": "integer",
                        "title": "Timeout",
                        "description": "Таймаут выполнения в секундах",
                        "default": 60
                    },
                    "wait_for_all": {
                        "type": "boolean",
                        "title": "Wait For All",
                        "description": "Ожидать завершения всех задач",
                        "default": True
                    }
                }
            },
            credentials_provider="",
            credentials_strategy="",
            library_name=None
        )

    def build(
        self,
        config: Dict[str, Any],
        bot_id: UUID
    ) -> Dict[str, Any]:
        """
        Создает структуры: Step, ConnectionGroup, Connections для параллельного выполнения.
        
        Args:
            config: Параметры пресета
            bot_id: ID бота
        
        Returns:
            Словарь с полями: step, connection_group, connections, next_step_id
        """
        # Извлекаем параметры из конфига
        tasks = config.get("tasks", [])
        timeout = config.get("timeout", 60)
        wait_for_all = config.get("wait_for_all", True)

        # Создаем прокси-шаг для начала параллельного выполнения
        parallel_start_step = StepModel(
            bot_id=bot_id,
            name="Parallel Execution Start",
            description="Начало параллельного выполнения задач",
            is_proxy=True,
            timeout_after=timeout
        )

        # Создаем сообщение с информацией о параллельном выполнении
        parallel_message = MessageModel(
            text=f"Параллельное выполнение {len(tasks)} задач",
            params={
                "tasks_count": len(tasks),
                "timeout": timeout,
                "wait_for_all": wait_for_all
            }
        )

        # Создаем группу связей для прокси-шага
        tasks_configs = []
        for i, task in enumerate(tasks):
            task_name = task.get("name", f"task_{i}")
            task_type = task.get("type", "code")
            task_config = task.get("config", {})
            
            tasks_configs.append({
                "name": task_name,
                "type": task_type,
                "config": task_config
            })

        code_template = """
async def main(message: dict | None, variables: dict):
    import asyncio
    import concurrent.futures
    import time
    
    # Список для хранения результатов задач
    results = {}
    
    # Запускаем все задачи параллельно
    tasks = []
"""

        # Добавляем код для создания задач в зависимости от их типа
        for i, task in enumerate(tasks_configs):
            task_name = task["name"]
            task_type = task["type"]
            
            if task_type == "code":
                code_template += f"""
    async def task_{i}():
        # Выполнить пользовательский код для {task_name}
        try:
            # Добавить код для выполнения задачи {task_name}
            result = "executed"
        except Exception as e:
            result = f"failed: {{str(e)}}"
        return "{task_name}", result

    tasks.append(task_{i}())
"""
            elif task_type == "http":
                code_template += f"""
    async def task_{i}():
        # Выполнить HTTP запрос для {task_name}
        import httpx
        try:
            # Добавить выполнение HTTP запроса
            async with httpx.AsyncClient() as client:
                response = await client.request(**{task["config"]})
                result = response.json() if response.content else "success"
        except Exception as e:
            result = f"failed: {{str(e)}}"
        return "{task_name}", result

    tasks.append(task_{i}())
"""
            else:  # integration
                code_template += f"""
    async def task_{i}():
        # Выполнить интеграцию для {task_name}
        try:
            # Логика выполнения интеграции
            result = "executed"
        except Exception as e:
            result = f"failed: {{str(e)}}"
        return "{task_name}", result

    tasks.append(task_{i}())
"""

        code_template += f"""
    # Запускаем задачи параллельно
    start_time = time.time()
    timeout = {timeout}
    
    try:
        if {wait_for_all}:
            # Ждем завершения всех задач
            completed_tasks = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=timeout
            )
        else:
            # Ждем хотя бы одну задачу
            done, pending = await asyncio.wait(
                tasks, 
                timeout=timeout, 
                return_when=asyncio.FIRST_COMPLETED
            )
            for task in pending:
                task.cancel()
            completed_tasks = [t.result() if not isinstance(t.result(), Exception) else t.result() for t in done]
        
        # Собираем результаты
        for result in completed_tasks:
            if isinstance(result, tuple) and len(result) == 2:
                task_name, task_result = result
                results[task_name] = task_result
            elif isinstance(result, Exception):
                results["error"] = str(result)
        
        return {{"parallel_results": results}}
    except asyncio.TimeoutError:
        return {{"parallel_results": {{"status": "timeout", "message": "Tasks did not complete within timeout"}}}}
"""

        parallel_connection_group = ConnectionGroupModel(
            search_type="code",
            code=code_template,
            variables={
                f"session.parallel_results": "{$response.result.parallel_results$}"
            }
        )

        # Создаем соединения для параллельного выполнения
        connections: List[ConnectionModel] = []

        # Соединение для продолжения после параллельного выполнения
        continue_connection = ConnectionModel(
            rules={},
            next_step_id=None,  # будет заполнен позже
            priority=0
        )
        connections.append(continue_connection)

        return {
            "step": parallel_start_step,
            "message": parallel_message,
            "connection_group": parallel_connection_group,
            "connections": connections,
            "next_step_id": None  # ID следующего шага после параллельного выполнения
        }