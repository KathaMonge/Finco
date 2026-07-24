from decimal import Decimal
from typing import Optional

from sqlalchemy import select, func, and_

from core.database import get_session
from core.models import Category, CategorySplit, Transaction
from core.schemas import CategoryCreate, CategoryUpdate, SplitEntry
from core.config import DEFAULT_CATEGORIES


class CategoryService:
    def create(self, data: CategoryCreate) -> Category:
        with get_session() as session:
            cat = Category(**data.model_dump())
            session.add(cat)
            session.commit()
            session.refresh(cat)
            return cat

    def get_by_id(self, cat_id: int) -> Optional[Category]:
        with get_session() as session:
            return session.get(Category, cat_id)

    def list_all(self) -> list[Category]:
        with get_session() as session:
            query = select(Category).order_by(Category.name)
            return list(session.execute(query).scalars().all())

    def update(self, cat_id: int, data: CategoryUpdate) -> Optional[Category]:
        with get_session() as session:
            cat = session.get(Category, cat_id)
            if not cat:
                return None
            for key, value in data.model_dump(exclude_unset=True).items():
                setattr(cat, key, value)
            session.commit()
            session.refresh(cat)
            return cat

    def delete(self, cat_id: int) -> bool:
        with get_session() as session:
            cat = session.get(Category, cat_id)
            if not cat or cat.is_system:
                return False
            session.delete(cat)
            session.commit()
            return True

    def seed_defaults(self):
        with get_session() as session:
            existing = session.execute(select(func.count(Category.id))).scalar()
            if existing and existing > 0:
                return
            for cat_data in DEFAULT_CATEGORIES:
                cat = Category(**cat_data, is_system=True)
                session.add(cat)
            session.commit()

    def get_budget_report(self, year: int, month: int) -> list[dict]:
        with get_session() as session:
            categories = self.list_all()
            report = []
            for cat in categories:
                spent = session.execute(
                    select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                        and_(
                            Transaction.category_id == cat.id,
                            Transaction.deleted_at.is_(None),
                            Transaction.type == "expense",
                            func.strftime("%Y", Transaction.date) == str(year),
                            func.strftime("%m", Transaction.date) == f"{month:02d}",
                        )
                    )
                ).scalar() or 0

                report.append({
                    "category": cat,
                    "spent": Decimal(str(spent)),
                    "budget": cat.monthly_budget or Decimal("0"),
                    "percentage": (
                        (Decimal(str(spent)) / cat.monthly_budget * 100)
                        if cat.monthly_budget and cat.monthly_budget > 0
                        else None
                    ),
                })
            return report

    def get_default_split(self, category_id: int) -> list[CategorySplit]:
        with get_session() as session:
            query = select(CategorySplit).where(CategorySplit.category_id == category_id)
            return list(session.execute(query).scalars().all())

    def set_default_split(self, category_id: int, splits: list[SplitEntry]) -> None:
        total = sum(s.percentage for s in splits)
        if splits and abs(total - 100) > Decimal("0.5"):
            raise ValueError(f"Los porcentajes deben sumar 100 (suman {total})")

        with get_session() as session:
            session.execute(
                CategorySplit.__table__.delete().where(CategorySplit.category_id == category_id)
            )
            for entry in splits:
                session.add(
                    CategorySplit(
                        category_id=category_id,
                        participant_id=entry.participant_id,
                        percentage=entry.percentage,
                    )
                )
            session.commit()


category_service = CategoryService()
