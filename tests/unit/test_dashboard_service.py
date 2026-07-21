"""Tests for DashboardService split calculations."""

from datetime import date
from decimal import Decimal

from core.schemas import TransactionCreate
from core.database import get_session
from core.models import Transaction


class TestDashboardSplit:
    def test_month_summary_with_splits(self, transaction_service, sample_account, sample_category, db_session):
        transaction_service.create(TransactionCreate(
            account_id=sample_account.id, category_id=sample_category.id,
            amount=Decimal("1000.00"), date=date(2024, 9, 10),
            description="Salary", type="income",
        ))
        transaction_service.create(TransactionCreate(
            account_id=sample_account.id, category_id=sample_category.id,
            amount=Decimal("200.00"), date=date(2024, 9, 15),
            description="Shared rent", type="expense",
            ownership_type="shared", split_ratio=Decimal("0.50"),
        ))
        transaction_service.create(TransactionCreate(
            account_id=sample_account.id, category_id=sample_category.id,
            amount=Decimal("50.00"), date=date(2024, 9, 16),
            description="Personal food", type="expense",
            ownership_type="personal", split_ratio=Decimal("1.00"),
        ))
        transaction_service.create(TransactionCreate(
            account_id=sample_account.id, category_id=sample_category.id,
            amount=Decimal("30.00"), date=date(2024, 9, 17),
            description="External insurance", type="expense",
            ownership_type="external",
        ))

        from services.dashboard_service import dashboard_service
        summary = dashboard_service.get_month_summary(2024, 9)

        assert summary["incomes"] == Decimal("1000.00")
        assert summary["expenses"] == Decimal("280.00")
        assert summary["shared_expenses"] == Decimal("200.00")
        assert summary["personal_expenses"] == Decimal("50.00")
        assert summary["external_expenses"] == Decimal("30.00")
        assert summary["shared_due"] == Decimal("100.00")
        assert summary["split_50_total"] == Decimal("140.00")

    def test_all_personal_no_split(self, transaction_service, sample_account, sample_category):
        transaction_service.create(TransactionCreate(
            account_id=sample_account.id, category_id=sample_category.id,
            amount=Decimal("100.00"), date=date(2024, 10, 1),
            description="Personal", type="expense",
            ownership_type="personal",
        ))

        from services.dashboard_service import dashboard_service
        summary = dashboard_service.get_month_summary(2024, 10)

        assert summary["shared_expenses"] == Decimal("0")
        assert summary["personal_expenses"] == Decimal("100.00")
        assert summary["external_expenses"] == Decimal("0")
        assert summary["shared_due"] == Decimal("0")
        assert summary["split_50_total"] == Decimal("50.00")

    def test_all_external_no_due(self, transaction_service, sample_account, sample_category):
        transaction_service.create(TransactionCreate(
            account_id=sample_account.id, category_id=sample_category.id,
            amount=Decimal("200.00"), date=date(2024, 11, 1),
            description="External", type="expense",
            ownership_type="external",
        ))

        from services.dashboard_service import dashboard_service
        summary = dashboard_service.get_month_summary(2024, 11)

        assert summary["shared_expenses"] == Decimal("0")
        assert summary["external_expenses"] == Decimal("200.00")
        assert summary["shared_due"] == Decimal("0")

    def test_custom_split_ratio(self, transaction_service, sample_account, sample_category):
        transaction_service.create(TransactionCreate(
            account_id=sample_account.id, category_id=sample_category.id,
            amount=Decimal("100.00"), date=date(2024, 12, 1),
            description="Custom split", type="expense",
            ownership_type="shared", split_ratio=Decimal("0.30"),
        ))

        from services.dashboard_service import dashboard_service
        summary = dashboard_service.get_month_summary(2024, 12)

        assert summary["shared_expenses"] == Decimal("100.00")
        assert summary["shared_due"] == Decimal("30.00")
