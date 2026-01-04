from __future__ import annotations
from typing import Optional, Dict, Any, Union
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from app.schemas.base import Timestamp


class StepExecutionDataBase(BaseModel):
    step_id: Union[UUID, str]
    variables: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None


class StepExecutionDataCreate(StepExecutionDataBase):
    pass


class StepExecutionDataUpdate(BaseModel):
    variables: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None


class StepExecutionDataPublic(StepExecutionDataBase, Timestamp):
    model_config = ConfigDict(from_attributes=True)
    id: Union[UUID, str]
    user_id: Optional[Union[UUID, str]] = None

