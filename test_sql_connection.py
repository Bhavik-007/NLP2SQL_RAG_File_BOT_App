import os
from pathlib import Path

import pyodbc
import yaml
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).parent
CONFIG_PATH = ROOT_DIR / "config" / "settings.yaml"


def load_database_settings() -> dict:
    load_dotenv(ROOT_DIR / ".env")
    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        settings = yaml.safe_load(file)
    return settings["database"]


def installed_sql_drivers() -> list[str]:
    return [driver for driver in pyodbc.drivers() if "SQL Server" in driver]


def build_connection_string(server: str, database: str, driver: str) -> str:
    return (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        "Trusted_Connection=yes;"
        "Encrypt=no;"
        "TrustServerCertificate=yes;"
        "Connection Timeout=5;"
    )


def test_connection(server: str, database: str, driver: str) -> bool:
    connection_string = build_connection_string(server, database, driver)
    print(f"\nTesting server: {server}")
    print(f"Driver: {driver}")

    try:
        with pyodbc.connect(connection_string) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT @@SERVERNAME, DB_NAME(), SYSTEM_USER")
            server_name, db_name, system_user = cursor.fetchone()
            print("SUCCESS")
            print(f"Connected server: {server_name}")
            print(f"Connected database: {db_name}")
            print(f"Windows user: {system_user}")
            return True
    except Exception as exc:
        print("FAILED")
        print(str(exc))
        return False


def main() -> None:
    db = load_database_settings()
    drivers = installed_sql_drivers()

    if not drivers:
        print("No Microsoft SQL Server ODBC drivers found.")
        print("Install Microsoft ODBC Driver 17 or 18 for SQL Server, then retry.")
        return

    configured_driver = os.getenv("SQL_DRIVER", db.get("driver", drivers[-1]))
    driver = configured_driver if configured_driver in drivers else drivers[-1]
    database = os.getenv("SQL_DATABASE", db["database"])
    configured_server = os.getenv("SQL_SERVER", db["server"])

    print("Installed SQL Server ODBC drivers:")
    for item in drivers:
        print(f"- {item}")

    candidate_servers = [
        configured_server,
        "localhost",
        ".",
        "localhost\\SQLEXPRESS",
        ".\\SQLEXPRESS",
        "tcp:localhost,1433",
        "tcp:127.0.0.1,1433",
    ]

    seen = set()
    unique_servers = []
    for server in candidate_servers:
        if server and server not in seen:
            seen.add(server)
            unique_servers.append(server)

    print(f"\nDatabase: {database}")
    for server in unique_servers:
        if test_connection(server, database, driver):
            print(f"\nUse this value in config/settings.yaml: server: \"{server}\"")
            return

    print("\nNo tested server value worked.")
    print("Check SQL Server service name, TCP/IP status, SQL Server Browser, and database name.")


if __name__ == "__main__":
    main()
