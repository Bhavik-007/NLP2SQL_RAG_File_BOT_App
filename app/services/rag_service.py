from langchain_ollama import OllamaLLM

from app.core.config import config
from app.engine.document_loader import DocumentLoader
from app.engine.document_vector_store import DocumentVectorStore
from app.engine.mongo_manager import MongoManager


class RAGService:
    GREETING_TERMS = {"hi", "hello", "hey", "thanks", "thank you", "ok", "okay"}

    def __init__(self, model_name=None):
        ollama_settings = config.settings.get("ollama", {})
        rag_settings = config.rag_settings.get("rag", {})
        self.llm = OllamaLLM(
            base_url=ollama_settings.get("base_url", "http://localhost:11434"),
            model=model_name or ollama_settings.get("model", "llama3"),
            temperature=ollama_settings.get("temperature", 0),
        )
        self.loader = DocumentLoader(
            chunk_size=rag_settings.get("chunk_size", 900),
            chunk_overlap=rag_settings.get("chunk_overlap", 150),
        )
        self.vector_store = DocumentVectorStore()
        self.mongo = MongoManager()
        self.top_k = rag_settings.get("top_k", 4)
        self.indexed_chunk_count = 0

    def ingest_files(self, uploaded_files) -> tuple[int, list[str], list[str]]:
        total_chunks = 0
        errors = []
        indexed_files = []

        for uploaded_file in uploaded_files or []:
            try:
                content = uploaded_file.getvalue()
                chunks = self.loader.load_file(uploaded_file.name, content)
                if not chunks:
                    raise ValueError(
                        "No extractable text found. If this is a scanned PDF, OCR is required before upload."
                    )
                chunk_count = self.vector_store.add_chunks(chunks)
                if not chunk_count:
                    raise ValueError("Document was read, but no chunks were indexed.")
                total_chunks += chunk_count
                self.indexed_chunk_count += chunk_count
                indexed_files.append(uploaded_file.name)
                file_type = uploaded_file.name.rsplit(".", 1)[-1].lower()
                self.mongo.save_file_metadata(uploaded_file.name, file_type, chunk_count)
            except Exception as exc:
                errors.append(f"{uploaded_file.name}: {exc}")

        return total_chunks, errors, indexed_files

    def ask(self, question: str) -> tuple[str, list[str]]:
        if not question or not question.strip():
            return "Please ask a question about the uploaded documents.", []

        normalized = " ".join(question.lower().strip().split()).rstrip("?!.")
        if normalized in self.GREETING_TERMS:
            return "Hello. Upload a document and ask a question about its content.", []

        contexts = self.vector_store.search(question, top_k=self.top_k)
        contexts = [item for item in contexts if item.get("text")]
        if not contexts:
            return "No document content is indexed yet. Please upload a document first.", []

        sources = self._format_sources(contexts)
        prompt = self._build_answer_prompt(question, contexts)
        answer = self._clean_answer(self.llm.invoke(prompt))

        self.mongo.save_chat_history(question, answer, sources)
        return answer, sources

    def has_indexed_content(self) -> bool:
        return self.indexed_chunk_count > 0 or self.vector_store.has_content()

    @staticmethod
    def _build_answer_prompt(question: str, contexts: list[dict]) -> str:
        context_text = "\n\n".join(
            (
                f"Source: {item['metadata'].get('file_name')} "
                f"chunk {item['metadata'].get('chunk_index')}\n"
                f"{item['text']}"
            )
            for item in contexts
        )
        return (
            "You are an enterprise document assistant. Answer only from the provided document context. "
            "If the answer is not present in the context, say that the uploaded documents do not contain enough information. "
            "Do not start with phrases like 'According to the provided documents'. "
            "Do not include source lines, chunk IDs, filenames, or citations in the final answer.\n\n"
            f"Document context:\n{context_text}\n\n"
            f"Question: {question}\n\n"
            "Answer concisely in plain business language."
        )

    @staticmethod
    def _clean_answer(raw_answer: str) -> str:
        answer = (raw_answer or "").strip()
        removable_prefixes = (
            "According to the provided documents, ",
            "According to the provided document, ",
            "Based on the provided documents, ",
            "Based on the provided document, ",
        )
        for prefix in removable_prefixes:
            if answer.startswith(prefix):
                answer = answer[len(prefix):].lstrip()

        clean_lines = []
        for line in answer.splitlines():
            stripped = line.strip()
            if stripped.lower().startswith(("source:", "sources:")):
                continue
            clean_lines.append(line)
        return "\n".join(clean_lines).strip()

    @staticmethod
    def _format_sources(contexts: list[dict]) -> list[str]:
        sources = []
        seen = set()
        for item in contexts:
            metadata = item.get("metadata", {})
            source = f"{metadata.get('file_name')}#chunk-{metadata.get('chunk_index')}"
            if source not in seen:
                seen.add(source)
                sources.append(source)
        return sources
