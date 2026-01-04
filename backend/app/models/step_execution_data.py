import uuid
from typing import Optional, Dict, Any
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSON
from .base import BaseModel, UUID


class StepExecutionDataModel(BaseModel):
    __tablename__ = "step_execution_data"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4, type_=UUID)
    step_id: Mapped[UUID] = mapped_column(ForeignKey("step.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=True)
    
    # JSON поля для хранения variables и context
    variables: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    context: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Связи
    step: Mapped["StepModel"] = relationship("StepModel", back_populates="execution_data", lazy="select")
    user: Mapped[Optional["UserModel"]] = relationship("UserModel", lazy="select")

