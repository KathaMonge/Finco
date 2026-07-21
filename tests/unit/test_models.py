"""Tests for SQLAlchemy models."""

from datetime import date, datetime
from decimal import Decimal

import pytest

from core.models import Account, Category, Transaction


class TestAccount:
    def test_create_account(self, db_session):
        acc = Account(name="Test", type="cash", balance=Decimal("500.00"))
        db_session.add(acc)
        db_session.commit()
        assert acc.id is not None
        assert acc.name == "Test"
        assert acc.type == "cash"
        assert acc.balance == Decimal("500.00")

    def test_account_defaults(self, db_session):
        acc = Account(name="Default Test", type="debit")
        db_session.add(acc)
        db_session.commit()
        assert acc.balance == Decimal("0")
        assert acc.icon == "credit_card"
        assert acc.created_at is not None


class TestCategory:
    def test_create_category(self, db_session):
        cat = Category(name="Food", icon="restaurant", color="#FF0000")
        db_session.add(cat)
        db_session.commit()
        assert cat.id is not None
        assert cat.name == "Food"
        assert cat.is_system is False

    def test_category_unique_name(self, db_session):
        cat1 = Category(name="Unique", icon="a", color="#FFF")
        db_session.add(cat1)
        db_session.commit()
        cat2 = Category(name="Unique", icon="b", color="#000")
        db_session.add(cat2)
        with pytest.raises(Exception):
            db_session.commit()


class TestTransaction:
    def test_create_transaction(self, db_session, sample_account, sample_category):
        tx = Transaction(
            account_id=sample_account.id,
            category_id=sample_category.id,
            amount=Decimal("99.99"),
            currency="ARS",
            date=date(2024, 6, 15),
            description="Compra test",
            type="expense",
        )
        db_session.add(tx)
        db_session.commit()
        assert tx.id is not None
        assert tx.deleted_at is None
        assert tx.amount == Decimal("99.99")

    def test_soft_delete(self, db_session, sample_transaction):
        from datetime import datetime
        tx = db_session.get(Transaction, sample_transaction.id)
        assert tx.deleted_at is None
        tx.deleted_at = datetime.now()
        db_session.commit()
        db_session.refresh(tx)
        assert tx.deleted_at is not None
