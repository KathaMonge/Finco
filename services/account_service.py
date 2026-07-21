from typing import Optional

from sqlalchemy import select

from core.database import get_session
from core.models import Account
from core.schemas import AccountCreate, AccountUpdate


class AccountService:
    def create(self, data: AccountCreate) -> Account:
        with get_session() as session:
            account = Account(**data.model_dump())
            session.add(account)
            session.commit()
            session.refresh(account)
            return account

    def get_by_id(self, account_id: int) -> Optional[Account]:
        with get_session() as session:
            return session.get(Account, account_id)

    def list_all(self) -> list[Account]:
        with get_session() as session:
            query = select(Account).order_by(Account.name)
            return list(session.execute(query).scalars().all())

    def update(self, account_id: int, data: AccountUpdate) -> Optional[Account]:
        with get_session() as session:
            account = session.get(Account, account_id)
            if not account:
                return None
            for key, value in data.model_dump(exclude_unset=True).items():
                setattr(account, key, value)
            session.commit()
            session.refresh(account)
            return account

    def delete(self, account_id: int) -> bool:
        with get_session() as session:
            account = session.get(Account, account_id)
            if not account:
                return False
            session.delete(account)
            session.commit()
            return True


account_service = AccountService()
