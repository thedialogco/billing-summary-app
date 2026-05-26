from datetime import datetime
from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from pydantic import BaseModel
from typing import Optional
from database import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    agreement_number: Mapped[str] = mapped_column(String, nullable=False)
    work_order_number: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ProjectCreate(BaseModel):
    name: str
    agreement_number: str
    work_order_number: str


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    agreement_number: Optional[str] = None
    work_order_number: Optional[str] = None


class ProjectRead(BaseModel):
    id: int
    name: str
    agreement_number: str
    work_order_number: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ValidationItem(BaseModel):
    passed: bool
    message: str


class ValidationResult(BaseModel):
    passed: bool
    items: list[ValidationItem]


class GenerateResponse(BaseModel):
    pdf_b64: str
    master_xlsx_b64: str
    validation: ValidationResult
