import re

class SQLSecurity:
    BLOCKED_KEYWORDS = {
        "ALTER", "CREATE", "DELETE", "DROP", "EXEC", "EXECUTE", "INSERT",
        "MERGE", "TRUNCATE", "UPDATE", "UPSERT", "GRANT", "REVOKE",
        "DENY", "BACKUP", "RESTORE", "OPENROWSET", "OPENDATASOURCE",
        "XP_CMDSHELL", "INTO", "DECLARE", "SET"
    }
    COMMENT_PATTERNS = ("--", "/*", "*/")
    
    @staticmethod
    def is_safe(sql: str) -> bool:
        is_valid, _ = SQLSecurity.validate(sql)
        return is_valid

    @staticmethod
    def validate(sql: str, tables_config: dict | None = None) -> tuple[bool, str]:
        if not sql or not isinstance(sql, str):
            return False, "SQL is empty."

        normalized = sql.strip()
        sql_upper = normalized.upper()

        if any(pattern in normalized for pattern in SQLSecurity.COMMENT_PATTERNS):
            return False, "SQL comments are not allowed."

        if ";" in normalized:
            return False, "Multiple statements are not allowed."

        if not re.match(r"^\s*SELECT\b", sql_upper):
            return False, "Only SELECT statements are allowed."

        for word in SQLSecurity.BLOCKED_KEYWORDS:
            if re.search(rf"\b{word}\b", sql_upper):
                return False, f"Keyword {word} is not allowed."

        if tables_config:
            allowed_tables = SQLSecurity._allowed_table_names(tables_config)
            referenced_tables = SQLSecurity._extract_referenced_tables(normalized)
            unknown_tables = referenced_tables - allowed_tables
            if unknown_tables:
                return False, f"Unauthorized table reference: {', '.join(sorted(unknown_tables))}."

        return True, "SQL is safe."

    @staticmethod
    def _extract_referenced_tables(sql: str) -> set[str]:
        matches = re.findall(r"\b(?:FROM|JOIN)\s+([\[\]\w\.]+)", sql, flags=re.IGNORECASE)
        tables = set()
        for match in matches:
            table = match.replace("[", "").replace("]", "").split(".")[-1]
            if table:
                tables.add(table.lower())
        return tables

    @staticmethod
    def _allowed_table_names(tables_config: dict) -> set[str]:
        allowed = set()
        for name, details in (tables_config.get("tables") or {}).items():
            allowed.add(name.lower())
            full_name = details.get("full_name")
            if full_name:
                table = full_name.replace("[", "").replace("]", "").split(".")[-1]
                allowed.add(table.lower())
        return allowed

    @staticmethod
    def sanitize_output(df):
        if df.empty:
            return "No data found"
        return df
