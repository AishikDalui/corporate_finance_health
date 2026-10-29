"""Read-only database execution engine with safety timeouts and error isolation."""
import os
import time
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text, URL
from backend.app.config import settings
from backend.app.core.sql_validator import SQLValidator


class DatabaseConnection:
    """Manages read-only connections to MySQL database."""

    _engine = None

    @classmethod
    def get_engine(cls):
        """Lazy initialization of SQLAlchemy engine with pool pre-ping."""
        if cls._engine is None:
            db_url = URL.create(
                drivername="mysql+pymysql",
                username=settings.db_user,
                password=settings.db_password,
                host=settings.db_host,
                port=settings.db_port,
                database=settings.db_name,
            )
            cls._engine = create_engine(
                db_url,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
                connect_args={"connect_timeout": 5},
            )
        return cls._engine

    @classmethod
    def execute_query(cls, sql: str, timeout_seconds: int = 10) -> List[Dict[str, Any]]:
        """Validate and execute a read-only SQL query against the database.
        
        Raises:
            ValueError: If SQL validation fails.
            Exception: If execution fails or database is unreachable.
        """
        is_valid, reason = SQLValidator.validate(sql)
        if not is_valid:
            raise ValueError(f"Security validation blocked query: {reason}")

        cleaned_sql = SQLValidator.sanitize(sql)

        engine = cls.get_engine()
        with engine.connect() as conn:
            # Set query execution timeout
            conn.execute(text(f"SET max_execution_time = {timeout_seconds * 1000}"))
            result = conn.execute(text(cleaned_sql))
            rows = result.mappings().all()
            return [dict(row) for row in rows]
