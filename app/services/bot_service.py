from langchain_ollama import OllamaLLM
from app.engine.db_manager import DatabaseManager
from app.engine.vector_search import SchemaRetriever
from app.core.config import config
from app.core.security import SQLSecurity

class SQLBotService:
    GREETING_TERMS = {
        "hi", "hello", "hey", "good morning", "good afternoon", "good evening",
        "thanks", "thank you", "ok", "okay"
    }
    ANALYTIC_TERMS = {
        "show", "list", "count", "total", "sum", "average", "avg", "minimum",
        "maximum", "min", "max", "compare", "trend", "group", "by", "sales",
        "purchase", "customer", "customers", "product", "products", "order",
        "orders", "city", "region", "channel", "category", "amount", "age",
        "actual", "predicted", "prediction", "ad", "click"
    }

    def __init__(self, model_name=None):
        ollama_settings = config.settings.get("ollama", {})
        self.llm = OllamaLLM(
            base_url=ollama_settings.get("base_url", "http://localhost:11434"),
            model=model_name or ollama_settings.get("model", "llama3"),
            temperature=ollama_settings.get("temperature", 0)
        )
        self.db = DatabaseManager()
        self.retriever = SchemaRetriever()

    def ask(self, question: str):
        if not question or not question.strip():
            return "Please enter a business question.", ""

        is_data_question, message = self._validate_data_question(question)
        if not is_data_question:
            return message, ""

        # 1. Retrieve relevant metadata
        schema_context = self.retriever.get_relevant_schema(question)
        
        # 2. SQL Generation
        gen_prompt = self._build_sql_prompt(question, schema_context)
        generated_sql = self._clean_sql(self.llm.invoke(gen_prompt))

        if generated_sql.upper() == "NOT_A_DATA_QUESTION":
            return (
                "Please ask a specific business data question about the configured SQL Server tables.",
                "",
            )

        is_safe, reason = SQLSecurity.validate(generated_sql, config.tables)
        if not is_safe:
            return f"I could not generate a safe query for that question. {reason}", generated_sql
        
        # 3. Execution
        df, error = self.db.execute_query(generated_sql)
        if error:
            return error, generated_sql
        if df is None or df.empty:
            return "No data found", generated_sql
            
        # 4. Summarization
        ans_prompt = (
            "You are a business data analyst. Answer the user's question using only "
            "the provided query result. Do not mention or expose SQL.\n\n"
            f"Question: {question}\n"
            f"Data JSON: {df.head(50).to_json(orient='records')}\n\n"
            "Return a concise business answer."
        )
        return self.llm.invoke(ans_prompt), generated_sql

    @staticmethod
    def _build_sql_prompt(question: str, schema_context: str) -> str:
        return (
            "You generate safe Microsoft SQL Server T-SQL for a read-only analytics assistant.\n"
            "Rules:\n"
            "- Return only one SELECT statement.\n"
            "- If the user question is not asking for database analysis, return exactly: NOT_A_DATA_QUESTION\n"
            "- Do not include markdown fences, comments, explanations, or semicolons.\n"
            "- Use only the provided tables and columns.\n"
            "- Use the exact SQL table name from the schema, including square brackets and schema name when provided.\n"
            "- Never use INSERT, UPDATE, DELETE, DROP, ALTER, EXEC, TRUNCATE, SELECT INTO, temp tables, or stored procedures.\n"
            "- Add TOP 100 unless the user clearly asks for an aggregate result.\n\n"
            f"Allowed schema:\n{schema_context}\n\n"
            f"User question: {question}\n"
            "T-SQL:"
        )

    @staticmethod
    def _clean_sql(raw_sql: str) -> str:
        sql = (raw_sql or "").strip()
        if sql.startswith("```"):
            sql = sql.strip("`").replace("sql", "", 1).replace("SQL", "", 1).strip()
        return sql.rstrip(";").strip()

    @classmethod
    def _validate_data_question(cls, question: str) -> tuple[bool, str]:
        normalized = " ".join(question.lower().strip().split())
        normalized = normalized.rstrip("?!.,")

        if normalized in cls.GREETING_TERMS:
            return (
                False,
                "Hello. Please ask a business question about customers, purchases, sales, products, predictions, or related metrics.",
            )

        tokens = set(normalized.replace("_", " ").split())
        has_analytic_intent = bool(tokens & cls.ANALYTIC_TERMS)
        has_question_shape = any(
            phrase in normalized
            for phrase in (
                "how many",
                "how much",
                "what is",
                "which",
                "top",
                "highest",
                "lowest",
                "breakdown",
                "summary",
            )
        )

        if len(normalized) < 8 or not (has_analytic_intent or has_question_shape):
            return (
                False,
                "Please ask a specific business data question, for example: total sales by region or average purchase amount by city.",
            )

        return True, ""
