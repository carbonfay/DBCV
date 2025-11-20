from __future__ import annotations

from typing import Optional, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from pydantic.types import JsonSchemaValue


class VariablesBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    data: Optional[JsonSchemaValue] = None


class VariablesPublic(VariablesBase):
    model_config = ConfigDict(from_attributes=True)
    id: Union[UUID, str]


class VariablesUpdate(VariablesBase):
    pass
