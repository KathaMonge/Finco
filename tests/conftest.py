"""Test fixtures: in-memory SQLite database and sample data.

IMPORTANT: Sets FINCO_TEST_DB to use in-memory SQLite.
"""

import os

os.environ["FINCO_TEST_DB"] = "sqlite:///:memory:"

from datetime import date
from decimal import Decimal

import pytest

from core.database import Base, get_engine, get_session_factory
from core.models import Account, Category, Transaction


@pytest.fixture(scope="function", autouse=True)
def reset_database():
    """Reset the database before each test by creating all tables."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Provide a SQLAlchemy session for direct ORM operations."""
    session = get_session_factory()()
    yield session
    session.close()


@pytest.fixture(scope="function")
def sample_category(db_session):
    cat = Category(name="Test Category", icon="test", color="#FF0000", is_system=False)
    db_session.add(cat)
    db_session.commit()
    db_session.refresh(cat)
    return cat


@pytest.fixture(scope="function")
def sample_account(db_session):
    acc = Account(name="Test Account", type="cash", balance=Decimal("1000.00"))
    db_session.add(acc)
    db_session.commit()
    db_session.refresh(acc)
    return acc


@pytest.fixture(scope="function")
def category_service():
    from services.category_service import category_service
    return category_service


@pytest.fixture(scope="function")
def transaction_service():
    from services.transaction_service import transaction_service
    return transaction_service


@pytest.fixture(scope="function")
def account_service():
    from services.account_service import account_service
    return account_service


@pytest.fixture(scope="function")
def sample_transaction(db_session, sample_category, sample_account):
    tx = Transaction(
        account_id=sample_account.id,
        category_id=sample_category.id,
        amount=Decimal("150.50"),
        currency="ARS",
        date=date(2024, 1, 15),
        description="Test transaction",
        type="expense",
    )
    db_session.add(tx)
    db_session.commit()
    db_session.refresh(tx)
    return tx
