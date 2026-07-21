"""Tests for TransactionService."""

from datetime import date
from decimal import Decimal

import pytest

from core.schemas import TransactionCreate, TransactionUpdate


class TestTransactionService:
    def test_create_transaction(self, transaction_service, sample_account, sample_category):
        data = TransactionCreate(
            account_id=sample_account.id,
            category_id=sample_category.id,
            amount=Decimal("250.00"),
            date=date(2024, 7, 1),
            description="Test income",
            type="income",
        )
        tx = transaction_service.create(data)
        assert tx.id is not None
        assert tx.amount == Decimal("250.00")
        assert tx.type == "income"

    def test_soft_delete_and_restore(self, transaction_service, sample_account, sample_category):
        data = TransactionCreate(
            account_id=sample_account.id,
            category_id=sample_category.id,
            amount=Decimal("100.00"),
            date=date(2024, 7, 2),
            description="To delete",
            type="expense",
        )
        tx = transaction_service.create(data)

        deleted = transaction_service.soft_delete(tx.id)
        assert deleted is not None
        assert deleted.deleted_at is not None

        active_list = transaction_service.list_active()
        assert tx.id not in [t.id for t in active_list]

        restored = transaction_service.restore(tx.id)
        assert restored is not None
        assert restored.deleted_at is None

        active_list = transaction_service.list_active()
        assert tx.id in [t.id for t in active_list]

    def test_list_with_filters(self, transaction_service, sample_account, sample_category):
        transaction_service.create(
            TransactionCreate(
                account_id=sample_account.id,
                category_id=sample_category.id,
                amount=Decimal("50.00"),
                date=date(2024, 8, 1),
                description="Supermarket",
                type="expense",
            )
        )
        transaction_service.create(
            TransactionCreate(
                account_id=sample_account.id,
                category_id=sample_category.id,
                amount=Decimal("200.00"),
                date=date(2024, 8, 5),
                description="Salary",
                type="income",
            )
        )

        expenses = transaction_service.list_active(type_filter="expense")
        assert len(expenses) == 1
        assert expenses[0].amount == Decimal("50.00")

        searched = transaction_service.list_active(search="Salary")
        assert len(searched) == 1
        assert searched[0].type == "income"

    def test_create_with_ownership(self, transaction_service, sample_account, sample_category):
        data = TransactionCreate(
            account_id=sample_account.id,
            category_id=sample_category.id,
            amount=Decimal("100.00"),
            date=date(2024, 10, 1),
            description="Shared expense",
            type="expense",
            ownership_type="shared",
            split_ratio=Decimal("0.50"),
        )
        tx = transaction_service.create(data)
        assert tx.ownership_type == "shared"
        assert tx.split_ratio == Decimal("0.50")

    def test_ownership_filter(self, transaction_service, sample_account, sample_category):
        transaction_service.create(TransactionCreate(
            account_id=sample_account.id, category_id=sample_category.id,
            amount=Decimal("100.00"), date=date(2024, 11, 1),
            description="Shared", type="expense", ownership_type="shared",
        ))
        transaction_service.create(TransactionCreate(
            account_id=sample_account.id, category_id=sample_category.id,
            amount=Decimal("50.00"), date=date(2024, 11, 1),
            description="Personal", type="expense", ownership_type="personal",
        ))
        transaction_service.create(TransactionCreate(
            account_id=sample_account.id, category_id=sample_category.id,
            amount=Decimal("30.00"), date=date(2024, 11, 1),
            description="External", type="expense", ownership_type="external",
        ))

        shared = transaction_service.list_active(ownership_filter="shared")
        personal = transaction_service.list_active(ownership_filter="personal")
        external = transaction_service.list_active(ownership_filter="external")
        assert len(shared) == 1
        assert len(personal) == 1
        assert len(external) == 1

    def test_month_summary(self, transaction_service, sample_account, sample_category):
        transaction_service.create(
            TransactionCreate(
                account_id=sample_account.id,
                category_id=sample_category.id,
                amount=Decimal("1000.00"),
                date=date(2024, 9, 10),
                description="Salary",
                type="income",
            )
        )
        transaction_service.create(
            TransactionCreate(
                account_id=sample_account.id,
                category_id=sample_category.id,
                amount=Decimal("300.00"),
                date=date(2024, 9, 15),
                description="Rent",
                type="expense",
            )
        )

        summary = transaction_service.get_month_summary(2024, 9)
        assert summary["incomes"] == Decimal("1000.00")
        assert summary["expenses"] == Decimal("300.00")
        assert summary["balance"] == Decimal("700.00")
