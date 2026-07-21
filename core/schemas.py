from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class AccountCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., pattern=r"^(cash|debit|credit)$")
    balance: Decimal = Field(default=Decimal("0.00"), ge=0)
    icon: str = Field(default="credit_card", max_length=50)


class AccountUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[str] = Field(None, pattern=r"^(cash|debit|credit)$")
    balance: Optional[Decimal] = Field(None, ge=0)
    icon: Optional[str] = Field(None, max_length=50)


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    icon: str = Field(..., max_length=50)
    color: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$")
    monthly_budget: Optional[Decimal] = Field(None, ge=0)


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    icon: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    monthly_budget: Optional[Decimal] = Field(None, ge=0)


class TransactionCreate(BaseModel):
    account_id: int = Field(..., ge=1)
    category_id: int = Field(..., ge=1)
    amount: Decimal = Field(..., ge=0)
    currency: str = Field(default="ARS", pattern=r"^[A-Z]{3}$")
    date: date
    description: str = Field(..., min_length=1, max_length=255)
    type: str = Field(..., pattern=r"^(income|expense)$")
    ownership_type: str = Field(default="shared", pattern=r"^(shared|personal|external)$")
    split_ratio: Decimal = Field(default=Decimal("0.50"), ge=0, le=1)
    receipt_image: Optional[str] = None
    ocr_data: Optional[str] = None
    ocr_confidence: Optional[float] = Field(None, ge=0, le=1)

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        return v.quantize(Decimal("0.01"))


class TransactionUpdate(BaseModel):
    account_id: Optional[int] = Field(None, ge=1)
    category_id: Optional[int] = Field(None, ge=1)
    amount: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, pattern=r"^[A-Z]{3}$")
    date: Optional[date] = None
    description: Optional[str] = Field(None, min_length=1, max_length=255)
    type: Optional[str] = Field(None, pattern=r"^(income|expense)$")
    ownership_type: Optional[str] = Field(None, pattern=r"^(shared|personal|external)$")
    split_ratio: Optional[Decimal] = Field(None, ge=0, le=1)
