from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import select, func, and_

from core.database import get_session
from core.models import Participant, Transaction, TransactionSplit, Category


class DashboardService:
    def get_month_summary(self, year: int, month: int) -> dict:
        with get_session() as session:
            base_filter = and_(
                Transaction.deleted_at.is_(None),
                func.strftime("%Y", Transaction.date) == str(year),
                func.strftime("%m", Transaction.date) == f"{month:02d}",
            )

            incomes = session.execute(
                select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                    and_(base_filter, Transaction.type == "income")
                )
            ).scalar()

            expenses = session.execute(
                select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                    and_(base_filter, Transaction.type == "expense")
                )
            ).scalar()

            expense_base = and_(base_filter, Transaction.type == "expense")

            shared_expenses = session.execute(
                select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                    and_(expense_base, Transaction.ownership_type == "shared")
                )
            ).scalar()

            personal_expenses = session.execute(
                select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                    and_(expense_base, Transaction.ownership_type == "personal")
                )
            ).scalar()

            external_expenses = session.execute(
                select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                    and_(expense_base, Transaction.ownership_type == "external")
                )
            ).scalar()

            shared_rows = session.execute(
                select(Transaction.amount, Transaction.split_ratio).where(
                    and_(expense_base, Transaction.ownership_type == "shared")
                )
            ).all()
            shared_due = sum(
                Decimal(str(row.amount)) * row.split_ratio for row in shared_rows
            )

            tx_count = session.execute(
                select(func.count(Transaction.id)).where(base_filter)
            ).scalar()

            return {
                "incomes": Decimal(str(incomes or 0)),
                "expenses": Decimal(str(expenses or 0)),
                "balance": Decimal(str((incomes or 0) - (expenses or 0))),
                "transaction_count": tx_count or 0,
                "shared_expenses": Decimal(str(shared_expenses or 0)),
                "personal_expenses": Decimal(str(personal_expenses or 0)),
                "external_expenses": Decimal(str(external_expenses or 0)),
                "shared_due": shared_due,
                "split_50_total": (Decimal(str(expenses or 0)) / 2).quantize(Decimal("0.01")),
            }

    def get_expenses_by_category(self, year: int, month: int) -> list[dict]:
        with get_session() as session:
            query = (
                select(
                    Category.name,
                    Category.color,
                    Category.icon,
                    func.coalesce(func.sum(Transaction.amount), 0).label("total"),
                )
                .join(Category, Transaction.category_id == Category.id)
                .where(
                    and_(
                        Transaction.deleted_at.is_(None),
                        Transaction.type == "expense",
                        func.strftime("%Y", Transaction.date) == str(year),
                        func.strftime("%m", Transaction.date) == f"{month:02d}",
                    )
                )
                .group_by(Category.id)
                .order_by(func.sum(Transaction.amount).desc())
            )
            rows = session.execute(query).all()
            return [
                {
                    "name": row.name,
                    "color": row.color,
                    "icon": row.icon,
                    "total": Decimal(str(row.total)),
                }
                for row in rows
            ]

    def get_recent_transactions(self, limit: int = 5) -> list[Transaction]:
        with get_session() as session:
            query = (
                select(Transaction)
                .where(Transaction.deleted_at.is_(None))
                .order_by(Transaction.date.desc(), Transaction.id.desc())
                .limit(limit)
            )
            return list(session.execute(query).scalars().all())

    def get_top_merchants(self, year: int, month: int, limit: int = 5) -> list[dict]:
        with get_session() as session:
            query = (
                select(
                    Transaction.description,
                    func.count(Transaction.id).label("count"),
                    func.sum(Transaction.amount).label("total"),
                )
                .where(
                    and_(
                        Transaction.deleted_at.is_(None),
                        Transaction.type == "expense",
                        func.strftime("%Y", Transaction.date) == str(year),
                        func.strftime("%m", Transaction.date) == f"{month:02d}",
                    )
                )
                .group_by(Transaction.description)
                .order_by(func.sum(Transaction.amount).desc())
                .limit(limit)
            )
            rows = session.execute(query).all()
            return [
                {
                    "merchant": row.description,
                    "count": row.count,
                    "total": Decimal(str(row.total)),
                }
                for row in rows
            ]

    def get_participant_summary(self, year: int, month: int) -> list[dict]:
        with get_session() as session:
            query = (
                select(
                    Participant.id,
                    Participant.name,
                    Participant.color,
                    func.sum(Transaction.amount * TransactionSplit.percentage / 100).label("total_owed"),
                )
                .join(TransactionSplit, TransactionSplit.participant_id == Participant.id)
                .join(Transaction, Transaction.id == TransactionSplit.transaction_id)
                .where(
                    and_(
                        Transaction.deleted_at.is_(None),
                        Transaction.type == "expense",
                        Participant.is_active.is_(True),
                        func.strftime("%Y", Transaction.date) == str(year),
                        func.strftime("%m", Transaction.date) == f"{month:02d}",
                    )
                )
                .group_by(Participant.id, Participant.name, Participant.color)
                .order_by(Participant.id)
            )
            rows = session.execute(query).all()
            return [
                {
                    "participant_id": row.id,
                    "name": row.name,
                    "color": row.color,
                    "total_owed": Decimal(str(row.total_owed or 0)),
                }
                for row in rows
            ]


dashboard_service = DashboardService()
