from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def ensure_schema_compatibility():
    if "sqlite" not in settings.DATABASE_URL:
        return

    inspector = inspect(engine)

    if inspector.has_table("stores"):
        store_columns = {column["name"] for column in inspector.get_columns("stores")}
        store_alters = {
            "default_urgent_fee": "ALTER TABLE stores ADD COLUMN default_urgent_fee FLOAT DEFAULT 0.0",
            "default_urgent_description": "ALTER TABLE stores ADD COLUMN default_urgent_description VARCHAR(255)",
        }
        with engine.begin() as connection:
            for column_name, sql in store_alters.items():
                if column_name not in store_columns:
                    connection.execute(text(sql))

    if inspector.has_table("service_items"):
        service_columns = {column["name"] for column in inspector.get_columns("service_items")}
        service_alters = {
            "urgent_fee": "ALTER TABLE service_items ADD COLUMN urgent_fee FLOAT DEFAULT 0.0",
            "urgent_description": "ALTER TABLE service_items ADD COLUMN urgent_description VARCHAR(255)",
        }
        with engine.begin() as connection:
            for column_name, sql in service_alters.items():
                if column_name not in service_columns:
                    connection.execute(text(sql))

    if inspector.has_table("orders"):
        order_columns = {column["name"] for column in inspector.get_columns("orders")}
        order_alters = {
            "is_suspended": "ALTER TABLE orders ADD COLUMN is_suspended BOOLEAN DEFAULT 0",
            "previous_status": "ALTER TABLE orders ADD COLUMN previous_status VARCHAR(30)",
            "suspend_reason": "ALTER TABLE orders ADD COLUMN suspend_reason VARCHAR(50)",
            "suspend_remark": "ALTER TABLE orders ADD COLUMN suspend_remark TEXT",
            "suspended_by": "ALTER TABLE orders ADD COLUMN suspended_by INTEGER",
            "suspended_at": "ALTER TABLE orders ADD COLUMN suspended_at DATETIME",
            "is_urgent": "ALTER TABLE orders ADD COLUMN is_urgent BOOLEAN DEFAULT 0",
            "urgent_remark": "ALTER TABLE orders ADD COLUMN urgent_remark TEXT",
            "urgent_fee": "ALTER TABLE orders ADD COLUMN urgent_fee FLOAT DEFAULT 0.0",
        }
        with engine.begin() as connection:
            for column_name, sql in order_alters.items():
                if column_name not in order_columns:
                    connection.execute(text(sql))

    if inspector.has_table("order_status_logs"):
        log_columns = {column["name"] for column in inspector.get_columns("order_status_logs")}
        log_alters = {
            "log_type": "ALTER TABLE order_status_logs ADD COLUMN log_type VARCHAR(20) DEFAULT 'status_change'",
            "suspend_reason": "ALTER TABLE order_status_logs ADD COLUMN suspend_reason VARCHAR(50)",
            "resume_result": "ALTER TABLE order_status_logs ADD COLUMN resume_result TEXT",
            "urgent_changed": "ALTER TABLE order_status_logs ADD COLUMN urgent_changed BOOLEAN DEFAULT 0",
            "from_urgent": "ALTER TABLE order_status_logs ADD COLUMN from_urgent BOOLEAN DEFAULT 0",
            "to_urgent": "ALTER TABLE order_status_logs ADD COLUMN to_urgent BOOLEAN DEFAULT 0",
            "urgent_remark_changed": "ALTER TABLE order_status_logs ADD COLUMN urgent_remark_changed BOOLEAN DEFAULT 0",
            "from_urgent_remark": "ALTER TABLE order_status_logs ADD COLUMN from_urgent_remark TEXT",
            "to_urgent_remark": "ALTER TABLE order_status_logs ADD COLUMN to_urgent_remark TEXT",
        }
        with engine.begin() as connection:
            for column_name, sql in log_alters.items():
                if column_name not in log_columns:
                    connection.execute(text(sql))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
