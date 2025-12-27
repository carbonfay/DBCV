from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Union, Dict, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.utils.decorators import partial_model
from app.schemas.block import Block
from app.schemas import register_model_rebuilder

if TYPE_CHECKING:
    from app.schemas.message import MessagePublic, MessageTemplate
    from app.schemas.connection import ConnectionPublic, ConnectionGroupPublic, ConnectionGroupExport, ConnectionGroupTemplate
    from app.schemas.templates import TemplateInstancePublic


class StepBase(Block):
    name: str
    is_proxy: bool
    description: Optional[str] = None
    timeout_after: Optional[int] = None


class StepRelation(StepBase):
    bot_id: Union[UUID, str]
    template_instance_id: Optional[Union[UUID, str]] = None


class StepSimple(StepRelation):
    model_config = ConfigDict(from_attributes=True)
    id: Union[UUID, str]


class StepPublic(StepSimple):
    model_config = ConfigDict(from_attributes=True)
    message: Optional['MessagePublic'] = None
    connection_groups: List['ConnectionGroupPublic'] = []
    template_instance: Optional['TemplateInstancePublic'] = None


class StepExport(StepSimple):
    message: Optional['MessagePublic'] = None
    connection_groups: List['ConnectionGroupExport'] = []
    template_instance: Optional['TemplateInstancePublic'] = None


class StepCreate(StepRelation):
    ...


@partial_model
class StepUpdate(StepRelation):
    pass


class StepTemplate(StepBase):
    id: Union[UUID, str]
    message: Optional['MessageTemplate'] = None
    connection_groups: List['ConnectionGroupTemplate'] = []

    @field_validator('id')
    def parse_json_fields(cls, value):
        if isinstance(value, UUID):
            try:
                return str(value)
            except Exception:
                return value
        return value


class StepExecuteIn(BaseModel):
    """Входные параметры для выполнения шага."""
    # Context variables in format {"bot": {...}, "channel": {...}, "session": {...}, "user": {...}}
    variables: Dict[str, Any] = Field(default_factory=dict)
    bot_id: Optional[Union[UUID, str]] = None
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Дополнительный контекст выполнения")


class GroupExecutionResult(BaseModel):
    """Результат выполнения одной группы связей."""
    group_id: str
    search_type: str
    priority: int
    result: Any = Field(default=None, description="Результат выполнения handler")
    variables_updated: Optional[Dict[str, Any]] = Field(default=None, description="Обновленные переменные после группы")


class StepExecuteOut(BaseModel):
    """Результат выполнения шага."""
    results: List[GroupExecutionResult] = Field(default_factory=list, description="Результаты выполнения всех групп")
    final_variables: Dict[str, Any] = Field(default_factory=dict, description="Финальное состояние переменных после всех групп")


def _rebuild_models() -> None:
    for model in (
        StepBase,
        StepRelation,
        StepSimple,
        StepPublic,
        StepExport,
        StepCreate,
        StepUpdate,
        StepTemplate,
        StepExecuteIn,
        GroupExecutionResult,
        StepExecuteOut,
    ):
        model.model_rebuild()


register_model_rebuilder(_rebuild_models)
