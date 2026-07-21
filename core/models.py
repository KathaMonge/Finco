from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    type: Mapped[str] = mapped_column(String(20))
    balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    icon: Mapped[str] = mapped_column(String(50), default="credit_card")
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="account")

    def __repr__(self) -> str:
        return f"<Account {self.name} ({self.type})>"


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    icon: Mapped[str] = mapped_column(String(50))
    color: Mapped[str] = mapped_column(String(7))
    monthly_budget: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    is_system: Mapped[bool] = mapped_column(default=False)

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="category")

    def __repr__(self) -> str:
        return f"<Category {self.name}>"


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), default="ARS")
    date: Mapped[date]
    description: Mapped[str] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(10))
    receipt_image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    ocr_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ocr_confidence: Mapped[Optional[float]] = mapped_column(nullable=True)
    ownership_type: Mapped[str] = mapped_column(String(20), default="shared")
    split_ratio: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.50"))
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    account: Mapped["Account"] = relationship(back_populates="transactions")
    category: Mapped["Category"] = relationship(back_populates="transactions")

    def __repr__(self) -> str:
        return f"<Transaction {self.type} ${self.amount} on {self.date}>"
