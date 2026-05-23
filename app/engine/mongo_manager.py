import logging
import os
from datetime import datetime, timezone

from app.core.config import config


class MongoManager:
    def __init__(self):
        mongo_settings = config.rag_settings.get("mongodb", {})
        self.available = False
        self.files_collection = None
        self.history_collection = None

        try:
            from pymongo import MongoClient
        except ImportError:
            logging.warning("pymongo is not installed. MongoDB persistence is disabled.")
            return

        try:
            client = MongoClient(
                os.getenv("MONGODB_URI", mongo_settings.get("uri", "mongodb://localhost:27017")),
                serverSelectionTimeoutMS=1500,
            )
            client.admin.command("ping")
            database = client[mongo_settings.get("database", "nlp_sql_bot")]
            self.files_collection = database[
                mongo_settings.get("files_collection", "document_files")
            ]
            self.history_collection = database[
                mongo_settings.get("history_collection", "document_chat_history")
            ]
            self.available = True
        except Exception as exc:
            logging.error(f"MongoDB Init Error: {exc}")

    def save_file_metadata(self, file_name: str, file_type: str, chunk_count: int) -> None:
        if not self.available:
            return

        self.files_collection.insert_one(
            {
                "file_name": file_name,
                "file_type": file_type,
                "chunk_count": chunk_count,
                "created_at_utc": datetime.now(timezone.utc),
            }
        )

    def save_chat_history(self, question: str, answer: str, sources: list[str]) -> None:
        if not self.available:
            return

        self.history_collection.insert_one(
            {
                "question": question,
                "answer": answer,
                "sources": sources,
                "created_at_utc": datetime.now(timezone.utc),
            }
        )
