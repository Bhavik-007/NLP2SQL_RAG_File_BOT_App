import csv
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone

from app.core.config import config


def get_app_logger(name: str = "nlp_sql_bot") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logs_dir = config.root_dir / "logs"
    logs_dir.mkdir(exist_ok=True)

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    handler = RotatingFileHandler(
        logs_dir / "app.log",
        maxBytes=5_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def write_audit_event(question: str, sql: str, answer: str, status: str) -> None:
    logger = get_app_logger("nlp_sql_audit")
    safe_question = question.replace("\n", " ").strip()
    safe_answer = answer.replace("\n", " ").strip()
    safe_sql = sql.replace("\n", " ").strip()
    logger.info(
        "status=%s | question=%s | generated_sql=%s | answer=%s",
        status,
        safe_question,
        safe_sql,
        safe_answer[:1000],
    )
    write_audit_csv(safe_question, safe_sql, safe_answer, status)


def write_audit_csv(question: str, sql: str, answer: str, status: str) -> None:
    logs_dir = config.root_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    csv_path = logs_dir / "app.csv"
    file_exists = csv_path.exists()

    with open(csv_path, "a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "timestamp_utc",
                "status",
                "question",
                "generated_sql",
                "answer",
            ],
        )
        if not file_exists:
            writer.writeheader()

        writer.writerow(
            {
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "status": status,
                "question": question,
                "generated_sql": sql,
                "answer": answer[:1000],
            }
        )
