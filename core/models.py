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
    splits: Mapped[list["TransactionSplit"]] = relationship(
        back_populates="transaction", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Transaction {self.type} ${self.amount} on {self.date}>"


class Participant(Base):
    __tablename__ = "participants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    color: Mapped[str] = mapped_column(String(7), default="#4ECDC4")
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    category_splits: Mapped[list["CategorySplit"]] = relationship(back_populates="participant")
    transaction_splits: Mapped[list["TransactionSplit"]] = relationship(back_populates="participant")

    def __repr__(self) -> str:
        return f"<Participant {self.name}>"


class CategorySplit(Base):
    __tablename__ = "category_splits"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    participant_id: Mapped[int] = mapped_column(ForeignKey("participants.id"))
    percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2))

    category: Mapped["Category"] = relationship()
    participant: Mapped["Participant"] = relationship(back_populates="category_splits")

    def __repr__(self) -> str:
        return f"<CategorySplit category={self.category_id} participant={self.participant_id} {self.percentage}%>"


class TransactionSplit(Base):
    __tablename__ = "transaction_splits"

    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id"))
    participant_id: Mapped[int] = mapped_column(ForeignKey("participants.id"))
    percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2))

    transaction: Mapped["Transaction"] = relationship(back_populates="splits")
    participant: Mapped["Participant"] = relationship(back_populates="transaction_splits")

    def __repr__(self) -> str:
        return f"<TransactionSplit tx={self.transaction_id} participant={self.participant_id} {self.percentage}%>"
