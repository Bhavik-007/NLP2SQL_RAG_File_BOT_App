import yaml
import os
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import quote_plus

class AppConfig:
    def __init__(self):
        # Locate the root folder (NLP-to-SQL) relative to this file
        self.root_dir = Path(__file__).parent.parent.parent
        load_dotenv(self.root_dir / ".env", override=True)
        
        settings_path = self.root_dir / "config" / "settings.yaml"
        tables_path = self.root_dir / "config" / "tables_config.yaml"
        rag_settings_path = self.root_dir / "config" / "rag_settings.yaml"
        
        if not settings_path.exists():
            raise FileNotFoundError(f"Missing settings.yaml at {settings_path}")

        with open(settings_path, "r", encoding="utf-8") as f:
            self.settings = yaml.safe_load(f)
            
        if not tables_path.exists():
            raise FileNotFoundError(f"Missing tables_config.yaml at {tables_path}")

        with open(tables_path, "r", encoding="utf-8") as f:
            self.tables = yaml.safe_load(f)

        self.rag_settings = {}
        if rag_settings_path.exists():
            with open(rag_settings_path, "r", encoding="utf-8") as f:
                self.rag_settings = yaml.safe_load(f) or {}

    @property
    def connection_string(self) -> str:
        db = self.effective_database_settings
        conn = (
            f"DRIVER={{{db['driver']}}};"
            f"SERVER={db['server']};"
            f"DATABASE={db['database']};"
            f"Trusted_Connection={db['trusted_connection']};"
            f"Encrypt={db['encrypt']};"
            f"TrustServerCertificate={db['trust_server_certificate']};"
            f"Connection Timeout={db['connection_timeout']};"
        )
        return f"mssql+pyodbc:///?odbc_connect={quote_plus(conn)}"

    @property
    def effective_database_settings(self) -> dict:
        db = self.settings["database"]
        server = os.getenv("SQL_SERVER", db["server"])
        database = os.getenv("SQL_DATABASE", db["database"])
        driver = os.getenv("SQL_DRIVER", db.get("driver", "ODBC Driver 17 for SQL Server"))
        trusted_connection = os.getenv("SQL_TRUSTED_CONNECTION", db.get("trusted_connection", "yes"))
        encrypt = os.getenv("SQL_ENCRYPT", str(db.get("encrypt", "no")))
        trust_server_certificate = os.getenv(
            "SQL_TRUST_SERVER_CERTIFICATE",
            str(db.get("trust_server_certificate", "yes")),
        )
        connection_timeout = os.getenv(
            "SQL_CONNECTION_TIMEOUT",
            str(db.get("connection_timeout", 30)),
        )
        return {
            "server": server,
            "database": database,
            "driver": driver,
            "trusted_connection": trusted_connection,
            "encrypt": encrypt,
            "trust_server_certificate": trust_server_certificate,
            "connection_timeout": connection_timeout,
        }

    @property
    def qdrant_url(self) -> str:
        qdrant = self.settings.get("qdrant", {})
        if qdrant.get("url"):
            return qdrant["url"]
        host = qdrant.get("host", "localhost")
        port = qdrant.get("port", 6333)
        return f"http://{host}:{port}"

config = AppConfig()
