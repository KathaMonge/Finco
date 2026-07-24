from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import select, func, and_

from core.database import get_session
from core.models import CategorySplit, Transaction, TransactionSplit
from core.schemas import SplitEntry, TransactionCreate, TransactionUpdate


class TransactionService:
    def create(self, data: TransactionCreate) -> Transaction:
        with get_session() as session:
            tx = Transaction(**data.model_dump())
            session.add(tx)
            session.flush()

            default_splits = session.execute(
                select(CategorySplit).where(CategorySplit.category_id == tx.category_id)
            ).scalars().all()
            for split in default_splits:
                session.add(
                    TransactionSplit(
                        transaction_id=tx.id,
                        participant_id=split.participant_id,
                        percentage=split.percentage,
                    )
                )

            session.commit()
            session.refresh(tx)
            return tx

    def get_by_id(self, tx_id: int) -> Optional[Transaction]:
        with get_session() as session:
            return session.get(Transaction, tx_id)

    def list_active(
        self,
        account_id: Optional[int] = None,
        category_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        type_filter: Optional[str] = None,
        ownership_filter: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Transaction]:
        with get_session() as session:
            query = select(Transaction).where(Transaction.deleted_at.is_(None))

            if account_id is not None:
                query = query.where(Transaction.account_id == account_id)
            if category_id is not None:
                query = query.where(Transaction.category_id == category_id)
            if date_from is not None:
                query = query.where(Transaction.date >= date_from)
            if date_to is not None:
                query = query.where(Transaction.date <= date_to)
            if type_filter is not None:
                query = query.where(Transaction.type == type_filter)
            if ownership_filter is not None:
                query = query.where(Transaction.ownership_type == ownership_filter)
            if search:
                query = query.where(Transaction.description.ilike(f"%{search}%"))

            query = query.order_by(Transaction.date.desc(), Transaction.id.desc())
            query = query.limit(limit).offset(offset)
            return list(session.execute(query).scalars().all())

    def count_active(
        self,
        account_id: Optional[int] = None,
        category_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        type_filter: Optional[str] = None,
        ownership_filter: Optional[str] = None,
        search: Optional[str] = None,
    ) -> int:
        with get_session() as session:
            query = select(func.count(Transaction.id)).where(
                Transaction.deleted_at.is_(None)
            )

            if account_id is not None:
                query = query.where(Transaction.account_id == account_id)
            if category_id is not None:
                query = query.where(Transaction.category_id == category_id)
            if date_from is not None:
                query = query.where(Transaction.date >= date_from)
            if date_to is not None:
                query = query.where(Transaction.date <= date_to)
            if type_filter is not None:
                query = query.where(Transaction.type == type_filter)
            if ownership_filter is not None:
                query = query.where(Transaction.ownership_type == ownership_filter)
            if search:
                query = query.where(Transaction.description.ilike(f"%{search}%"))

            result = session.execute(query).scalar()
            return result or 0

    def update(self, tx_id: int, data: TransactionUpdate) -> Optional[Transaction]:
        with get_session() as session:
            tx = session.get(Transaction, tx_id)
            if not tx or tx.deleted_at is not None:
                return None
            for key, value in data.model_dump(exclude_unset=True).items():
                setattr(tx, key, value)
            session.commit()
            session.refresh(tx)
            return tx

    def soft_delete(self, tx_id: int) -> Optional[Transaction]:
        with get_session() as session:
            tx = session.get(Transaction, tx_id)
            if not tx:
                return None
            tx.deleted_at = datetime.now()
            session.commit()
            session.refresh(tx)
            return tx

    def restore(self, tx_id: int) -> Optional[Transaction]:
        with get_session() as session:
            tx = session.get(Transaction, tx_id)
            if not tx or tx.deleted_at is None:
                return None
            tx.deleted_at = None
            session.commit()
            session.refresh(tx)
            return tx

    def get_month_summary(self, year: int, month: int, account_id: Optional[int] = None):
        with get_session() as session:
            base_filter = and_(
                Transaction.deleted_at.is_(None),
                func.strftime("%Y", Transaction.date) == str(year),
                func.strftime("%m", Transaction.date) == f"{month:02d}",
            )
            if account_id is not None:
                base_filter = and_(base_filter, Transaction.account_id == account_id)

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

            return {
                "incomes": Decimal(str(incomes or 0)),
                "expenses": Decimal(str(expenses or 0)),
                "balance": Decimal(str((incomes or 0) - (expenses or 0))),
            }

    def get_splits(self, transaction_id: int) -> list[TransactionSplit]:
        with get_session() as session:
            query = select(TransactionSplit).where(TransactionSplit.transaction_id == transaction_id)
            return list(session.execute(query).scalars().all())

    def set_splits(self, transaction_id: int, splits: list[SplitEntry]) -> None:
        total = sum(s.percentage for s in splits)
        if splits and abs(total - 100) > Decimal("0.5"):
            raise ValueError(f"Los porcentajes deben sumar 100 (suman {total})")

        with get_session() as session:
            session.execute(
                TransactionSplit.__table__.delete().where(
                    TransactionSplit.transaction_id == transaction_id
                )
            )
            for entry in splits:
                session.add(
                    TransactionSplit(
                        transaction_id=transaction_id,
                        participant_id=entry.participant_id,
                        percentage=entry.percentage,
                    )
                )
            session.commit()


transaction_service = TransactionService()
