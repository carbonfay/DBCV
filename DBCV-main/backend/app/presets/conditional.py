"""Preset для условных переходов IF/ELSE."""
from typing import Dict, Any, Union, Optional
from uuid import UUID

from app.presets.base import BasePreset, PresetMetadata
from app.schemas.step import StepCreate
from app.schemas.connection import ConnectionGroupCreate, ConnectionCreate
from app.models.connection import SearchType


class IfPreset(BasePreset):
    """Preset для создания условного перехода IF/ELSE."""
    
    @property
    def metadata(self) -> PresetMetadata:
        return PresetMetadata(
            id="if",
            name="IF/ELSE",
            description="Условный переход: если условие выполнено - переход на один шаг, иначе - на другой",
            category="logic",
            icon_s3_key="icons/presets/if.svg",
            color="#4CAF50",
            config_schema={
                "type": "object",
                "properties": {
                    "condition": {
                        "type": "object",
                        "description": "Правило для IF (формат jqqb)",
                        "properties": {
                            "condition": {
                                "type": "string",
                                "enum": ["AND", "OR"],
                                "description": "Логический оператор для объединения правил"
                            },
                            "rules": {
                                "type": "array",
                                "description": "Список правил",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "field": {
                                            "type": "string",
                                            "description": "Поле для проверки (например, message.text)"
                                        },
                                        "operator": {
                                            "type": "string",
                                            "enum": [
                                                "equals", "not_equals",
                                                "contains", "not_contains",
                                                "greater_than", "less_than",
                                                "greater_than_or_equal", "less_than_or_equal",
                                                "in", "not_in",
                                                "is_empty", "is_not_empty"
                                            ],
                                            "description": "Оператор сравнения"
                                        },
                                        "value": {
                                            "description": "Значение для сравнения"
                                        }
                                    },
                                    "required": ["field", "operator"]
                                }
                            }
                        },
                        "required": ["condition", "rules"]
                    },
                    "if_step_id": {
                        "type": "string",
                        "format": "uuid",
                        "description": "ID шага для IF ветки"
                    },
                    "else_step_id": {
                        "type": "string",
                        "format": "uuid",
                        "description": "ID шага для ELSE ветки (опционально)"
                    },
                    "name": {
                        "type": "string",
                        "description": "Имя шага (опционально)"
                    }
                },
                "required": ["condition", "if_step_id"]
            },
            examples=[
                {
                    "description": "Проверка текста сообщения",
                    "config": {
                        "condition": {
                            "condition": "AND",
                            "rules": [
                                {
                                    "field": "message.text",
                                    "operator": "equals",
                                    "value": "start"
                                }
                            ]
                        },
                        "if_step_id": "uuid-if-step",
                        "else_step_id": "uuid-else-step",
                        "name": "Проверка команды"
                    }
                },
                {
                    "description": "Проверка числового значения",
                    "config": {
                        "condition": {
                            "condition": "AND",
                            "rules": [
                                {
                                    "field": "session.score",
                                    "operator": "greater_than",
                                    "value": 100
                                }
                            ]
                        },
                        "if_step_id": "uuid-if-step",
                        "name": "Проверка счета"
                    }
                }
            ]
        )
    
    async def build(
        self,
        bot_id: Union[UUID, str],
        config: Dict[str, Any],
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Создает структуру Step + ConnectionGroup + Connections для IF/ELSE.
        
        Args:
            bot_id: ID бота
            config: Параметры preset
                - condition: правило для IF (обязательно)
                - if_step_id: ID шага для IF ветки (обязательно)
                - else_step_id: ID шага для ELSE ветки (опционально)
                - name: имя шага (опционально)
            name: Имя шага (если не указано в config)
        
        Returns:
            dict с ключами "step" и "connection_group"
        """
        # Получаем имя шага
        step_name = name or config.get("name") or "IF/ELSE"
        
        # Создаем Step
        step = StepCreate(
            bot_id=bot_id,
            name=step_name,
            is_proxy=True
        )
        
        # Создаем connections
        connections = []
        
        # IF connection (priority=0)
        if_connection = ConnectionCreate(
            next_step_id=config["if_step_id"],
            rules=config["condition"],
            priority=0
        )
        connections.append(if_connection)
        
        # ELSE connection (priority=1, если указан else_step_id)
        if "else_step_id" in config and config["else_step_id"]:
            else_connection = ConnectionCreate(
                next_step_id=config["else_step_id"],
                rules={},  # Пустое правило = всегда True (ELSE case)
                priority=1
            )
            connections.append(else_connection)
        
        # Создаем ConnectionGroup
        connection_group = ConnectionGroupCreate(
            search_type=SearchType.message,
            connections=connections,
            priority=0
        )
        
        return {
            "step": step,
            "connection_group": connection_group
        }

