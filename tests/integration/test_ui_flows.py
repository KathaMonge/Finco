"""Integration tests for UI flows.

These tests verify that the services work together correctly
in scenarios that mimic user workflows.
"""

from datetime import date, datetime
from decimal import Decimal

from core.schemas import AccountCreate, CategoryCreate, TransactionCreate
from services.transaction_service import transaction_service
from services.category_service import category_service
from services.account_service import account_service
from services.dashboard_service import dashboard_service
from services.backup_service import backup_service


class TestFullWorkflow:
    def test_lifecycle(self):
        cat = category_service.create(
            CategoryCreate(name="Groceries", icon="shopping_cart", color="#FF0000")
        )
        acc = account_service.create(
            AccountCreate(name="Wallet", type="cash", balance=Decimal("500.00"))
        )

        tx1 = transaction_service.create(
            TransactionCreate(
                account_id=acc.id,
                category_id=cat.id,
                amount=Decimal("80.00"),
                date=date(2024, 10, 1),
                description="Supermarket",
                type="expense",
            )
        )
        tx2 = transaction_service.create(
            TransactionCreate(
                account_id=acc.id,
                category_id=cat.id,
                amount=Decimal("1500.00"),
                date=date(2024, 10, 5),
                description="Salary",
                type="income",
            )
        )

        summary = dashboard_service.get_month_summary(2024, 10)
        assert summary["incomes"] == Decimal("1500.00")
        assert summary["expenses"] == Decimal("80.00")
        assert summary["balance"] == Decimal("1420.00")

        recent = dashboard_service.get_recent_transactions(limit=10)
        assert len(recent) == 2

        expenses_by_cat = dashboard_service.get_expenses_by_category(2024, 10)
        assert len(expenses_by_cat) == 1
        assert expenses_by_cat[0]["name"] == "Groceries"
        assert expenses_by_cat[0]["total"] == Decimal("80.00")

        transaction_service.soft_delete(tx1.id)
        summary_after_delete = dashboard_service.get_month_summary(2024, 10)
        assert summary_after_delete["expenses"] == Decimal("0.00")

        transaction_service.restore(tx1.id)
        summary_after_restore = dashboard_service.get_month_summary(2024, 10)
        assert summary_after_restore["expenses"] == Decimal("80.00")

    def test_ui_views_render(self):
        from unittest.mock import MagicMock
        from ui.views.dashboard_view import dashboard_view
        from ui.views.transactions_view import transactions_view
        from ui.views.categories_view import categories_view
        from ui.views.accounts_view import accounts_view

        page = MagicMock()
        d_view = dashboard_view(page)
        assert d_view is not None

        t_view = transactions_view(page)
        assert t_view is not None

        c_view = categories_view(page)
        assert c_view is not None

        a_view = accounts_view(page)
        assert a_view is not None


class TestBackupFlow:
    def test_export_json(self, tmp_path):
        export_path = backup_service.export_json(tmp_path)
        assert export_path.exists()
        assert export_path.suffix == ".json"
        content = export_path.read_text(encoding="utf-8")
        assert "exported_at" in content

    def test_export_csv(self, tmp_path):
        export_path = backup_service.export_csv(tmp_path)
        assert export_path.exists()
        assert export_path.suffix == ".csv"
        content = export_path.read_text(encoding="utf-8-sig")
        assert "ID,Fecha,Tipo" in content
