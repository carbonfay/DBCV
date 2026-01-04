from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Union, Dict, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator, Field, computed_field

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
    credential_id: Optional[Union[UUID, str]] = None


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


class ExecuteStepIn(BaseModel):
    """Входные данные для выполнения шага."""
    # Context variables в формате {"bot": {...}, "channel": {...}, "session": {...}, "user": {...}}
    variables: Dict[str, Any] = Field(default_factory=dict)
    bot_id: Optional[Union[UUID, str]] = None  # Если не указан, берётся из step.bot_id
    credential_id: Optional[Union[UUID, str]] = None  # Разовый выбор credential для запуска (без сохранения)
    # Dry-run: только подстановка переменных, без реального выполнения
    dry_run: bool = False


class ConnectionGroupResult(BaseModel):
    """Результат выполнения одного connection_group."""
    connection_group_id: Union[UUID, str]
    search_type: str
    result: Optional[Any] = None
    error: Optional[str] = None
    variables_updated: Dict[str, Any] = Field(default_factory=dict)
    priority: Optional[int] = None  # Для совместимости с фронтендом
    
    @computed_field
    @property
    def group_id(self) -> str:
        """Алиас для connection_group_id для совместимости с фронтендом."""
        return str(self.connection_group_id)


class ExecuteStepOut(BaseModel):
    """Результат выполнения шага."""
    step_id: Union[UUID, str]
    step_name: str
    connection_groups_results: List[ConnectionGroupResult]
    final_variables: Dict[str, Any]
    executed_count: int
    success_count: int
    error_count: int
    
    @computed_field
    @property
    def results(self) -> List[Dict[str, Any]]:
        """Алиас для connection_groups_results для совместимости с фронтендом."""
        return [item.model_dump(mode='json') for item in self.connection_groups_results]


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
        ExecuteStepIn,
        ConnectionGroupResult,
        ExecuteStepOut,
    ):
        model.model_rebuild()


register_model_rebuilder(_rebuild_models)
