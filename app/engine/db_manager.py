import pandas as pd
from pandas.errors import DatabaseError
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from app.core.config import config
from app.core.security import SQLSecurity

class DatabaseManager:
    def __init__(self):
        db_settings = config.settings.get("database", {})
        pool_settings = db_settings.get("pooling", {})
        self.engine = create_engine(
            config.connection_string,
            pool_pre_ping=True,
            pool_size=pool_settings.get("pool_size", 5),
            max_overflow=pool_settings.get("max_overflow", 10),
            pool_timeout=pool_settings.get("pool_timeout", 30),
        )

    def execute_query(self, sql: str):
        is_safe, reason = SQLSecurity.validate(sql, config.tables)
        if not is_safe:
            return None, "Security Violation: Unauthorized SQL operation."
        
        try:
            with self.engine.connect() as conn:
                result = pd.read_sql(text(sql), conn)
                if result.empty:
                    return None, "No data found"
                return result, None
        except (DatabaseError, SQLAlchemyError) as e:
            return None, f"Execution Error: {str(e)}"
