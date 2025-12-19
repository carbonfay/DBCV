"""Loop Preset для DBCV - позволяет создать цикл по элементам."""
from typing import Dict, Any, List
from uuid import UUID

from app.integrations.base import IntegrationMetadata
from app.presets.base import BasePreset
from app.models.step import StepModel
from app.models.connection_group import ConnectionGroupModel
from app.models.connection import ConnectionModel
from app.models.message import MessageModel


class LoopPreset(BasePreset):
    """Пресет для создания цикла по элементам."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="loop_preset",
            version="1.0.0",
            name="Loop",
            description="Цикл по элементам массива/списка",
            category="logic",
            icon_s3_key="icons/presets/loop.svg",
            color="#FF6B6B",
            config_schema={
                "type": "object",
                "required": ["items_variable", "item_variable_name"],
                "properties": {
                    "items_variable": {
                        "type": "string",
                        "title": "Items Variable",
                        "description": "Переменная содержащая массив/список для итерации"
                    },
                    "item_variable_name": {
                        "type": "string",
                        "title": "Item Variable Name",
                        "description": "Название переменной для текущего элемента в цикле",
                        "default": "current_item"
                    },
                    "index_variable_name": {
                        "type": "string",
                        "title": "Index Variable Name",
                        "description": "Название переменной для индекса в цикле",
                        "default": "current_index"
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
        Создает структуры: Step, ConnectionGroup, Connections для цикла.
        
        Args:
            config: Параметры пресета
            bot_id: ID бота
        
        Returns:
            Словарь с полями: step, connection_group, connections, next_step_id
        """
        # Извлекаем параметры из конфига
        items_variable = config.get("items_variable")
        item_variable_name = config.get("item_variable_name", "current_item")
        index_variable_name = config.get("index_variable_name", "current_index")

        # Создаем прокси-шаг для начала цикла
        loop_start_step = StepModel(
            bot_id=bot_id,
            name=f"Loop Start: {items_variable}",
            description="Начало цикла по элементам",
            is_proxy=True,
            timeout_after=300
        )

        # Создаем сообщение с информацией о цикле
        loop_message = MessageModel(
            text=f"Начало цикла по {items_variable}",
            params={}
        )

        # Создаем группу связей для прокси-шага
        loop_connection_group = ConnectionGroupModel(
            search_type="code",
            code=f"""
async def main(message: dict | None, variables: dict):
    # Получаем массив для итерации
    items = variables.get('{items_variable}', [])
    
    # Подготовим переменные для цикла
    loop_vars = {{
        '{item_variable_name}s': items,
        '{item_variable_name}s_total': len(items),
        '{item_variable_name}s_index': 0,
        '{item_variable_name}s_current': items[0] if items else None,
        '{index_variable_name}': 0
    }}
    
    return {{'loop_vars': loop_vars}}
            """,
            variables={
                f"session.loop_items": f"{{response.result.loop_vars.{item_variable_name}s}}",
                f"session.loop_total": f"{{response.result.loop_vars.{item_variable_name}s_total}}",
                f"session.loop_index": f"{{response.result.loop_vars.{index_variable_name}}}",
                f"session.{item_variable_name}": f"{{response.result.loop_vars.{item_variable_name}s_current}}"
            }
        )

        # Создаем соединения для цикла
        connections: List[ConnectionModel] = []

        # Соединение для продолжения цикла если есть еще элементы
        continue_loop_connection = ConnectionModel(
            rules={
                "condition": "AND",
                "rules": [
                    {
                        "field": f"session.loop_index",
                        "operator": "less_than",
                        "value": "{$session.loop_total$}"
                    }
                ]
            },
            next_step_id=None,  # будет заполнен позже
            priority=0
        )
        connections.append(continue_loop_connection)

        # Соединение для выхода из цикла
        exit_loop_connection = ConnectionModel(
            rules={},  # ELSE - когда закончились элементы
            next_step_id=None,  # будет заполнен позже
            priority=1
        )
        connections.append(exit_loop_connection)

        return {
            "step": loop_start_step,
            "message": loop_message,
            "connection_group": loop_connection_group,
            "connections": connections,
            "next_step_id": None  # ID следующего шага после цикла
        }