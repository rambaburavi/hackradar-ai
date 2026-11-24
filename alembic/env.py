import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import create_engine, pool
from sqlalchemy.engine import make_url


PROJECT_ROOT = Path(__file__).resolve().parents[1]
API_ROOT = PROJECT_ROOT / "apps" / "api"

sys.path.insert(0, str(API_ROOT))


from app.core.config import settings
from app.db.base import Base
import app.models


config = context.config


if config.config_file_name is not None:
    fileConfig(config.config_file_name)


target_metadata = Base.metadata


def get_database_url() -> str:
    arguments = context.get_x_argument(as_dictionary=True)

    target = arguments.get("target", "dev")

    if target == "dev":
        database_url = settings.DATABASE_URL

    elif target == "test":
        database_url = settings.TEST_DATABASE_URL

        if not database_url:
            raise RuntimeError(
                "TEST_DATABASE_URL is not configured."
            )

        test_url = make_url(database_url)
        dev_url = make_url(settings.DATABASE_URL)

        if test_url.database != "hackradar_test":
            raise RuntimeError(
                "Test migrations must target hackradar_test."
            )

        if test_url == dev_url:
            raise RuntimeError(
                "Test and development databases must be different."
            )

    else:
        raise RuntimeError(
            f"Unsupported migration target: {target}"
        )

    return database_url


def run_migrations_offline() -> None:
    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(
        get_database_url(),
        poolclass=pool.NullPool,
        hide_parameters=True,
        connect_args={"connect_timeout": 5},
    )

    try:
        with engine.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                compare_type=True,
                compare_server_default=True,
            )

            with context.begin_transaction():
                context.run_migrations()

    finally:
        engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()