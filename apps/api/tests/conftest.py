import pytest

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import settings


@pytest.fixture(scope="session")
def test_engine():
    if not settings.TEST_DATABASE_URL:
        pytest.fail("TEST_DATABASE_URL is not configured.")

    test_url = make_url(settings.TEST_DATABASE_URL)
    dev_url = make_url(settings.DATABASE_URL)

    if test_url.database != "hackradar_test":
        pytest.fail(
            "Integration tests must use hackradar_test."
        )

    if test_url == dev_url:
        pytest.fail(
            "Test database must not be the development database."
        )

    engine = create_engine(
        settings.TEST_DATABASE_URL,
        pool_pre_ping=True,
        hide_parameters=True,
        connect_args={"connect_timeout": 5},
    )

    try:
        with engine.connect() as connection:
            database_name = connection.execute(
                text("SELECT current_database()")
            ).scalar_one()

            if database_name != "hackradar_test":
                pytest.fail(
                    "Connected to an unexpected database."
                )

        yield engine

    finally:
        engine.dispose()


@pytest.fixture
def db_session(test_engine):
    connection = test_engine.connect()
    transaction = connection.begin()

    session = Session(
        bind=connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )

    try:
        yield session

    finally:
        session.close()

        if transaction.is_active:
            transaction.rollback()

        connection.close()