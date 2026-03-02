import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

from app.core.config import settings
from app.core.database import Base
from app.models.user     import User
from app.models.product  import Product
from app.models.product import Category
from app.models.order    import Order, OrderItem, Address, CartItem, Wishlist

config = context.config
fileConfig(config.config_file_name)

target_metadata = Base.metadata

# ── Force set URL directly from settings ─────────────────────────────────────
migration_url = settings.DATABASE_MIGRATION_URL or settings.DATABASE_URL
config.set_main_option("sqlalchemy.url", migration_url)


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    from sqlalchemy import create_engine
    connectable = create_engine(
        migration_url,
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()