from decimal import Decimal
from typing import Optional

from sqlalchemy import select, func, and_

from core.database import get_session
from core.models import Category, Transaction
from core.schemas import CategoryCreate, CategoryUpdate
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


category_service = CategoryService()
