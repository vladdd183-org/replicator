"""
License Data Schemas

Схемы данных для работы с информацией о лицензии.
"""

from pydantic import BaseModel, Field
from typing import Optional


class LicenseInfoResponse(BaseModel):
    """
    Ответ с информацией о лицензии
    
    Attributes:
        status: Статус лицензии (valid, no_license, expired, error)
        machine_id: Уникальный идентификатор машины
        expires_at: Дата истечения лицензии (если статус valid)
        message: Человекочитаемое сообщение о статусе
        cached: Является ли результат кешированным
    """
    
    status: str = Field(
        ...,
        description="Статус лицензии: valid, no_license, expired, error"
    )
    machine_id: Optional[str] = Field(
        None,
        description="Уникальный идентификатор машины"
    )
    expires_at: Optional[str] = Field(
        None,
        description="Дата истечения лицензии в формате ISO 8601"
    )
    message: Optional[str] = Field(
        None,
        description="Человекочитаемое сообщение о статусе лицензии"
    )
    cached: bool = Field(
        False,
        description="Является ли результат кешированным"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "valid",
                "machine_id": "abc123def456...",
                "expires_at": "2025-12-31T23:59:59Z",
                "message": "License is valid",
                "cached": False
            }
        }


__all__ = ["LicenseInfoResponse"]

