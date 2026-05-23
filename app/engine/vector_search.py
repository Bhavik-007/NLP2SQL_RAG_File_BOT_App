import logging
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
from app.core.config import config

class SchemaRetriever:
    def __init__(self):
        q_set = config.settings.get('qdrant', {})
        self.url = config.qdrant_url
        self.collection = q_set.get('collection_name', "schema_metadata")
        self.available = False
        
        self.client = QdrantClient(url=self.url)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        if self._setup_collection():
            self.available = True
            self.index_tables()

    def _setup_collection(self):
        try:
            cols = self.client.get_collections().collections
            if not any(c.name == self.collection for c in cols):
                self.client.create_collection(
                    collection_name=self.collection,
                    vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
                )
            return True
        except Exception as e:
            logging.error(f"Qdrant Init Error: {e}")
            return False

    def get_relevant_schema(self, query: str, top_k=3) -> str:
        if not self.available:
            return self._yaml_schema_context()

        try:
            vector = self.model.encode(query).tolist()
            results = self.client.search(
                collection_name=self.collection,
                query_vector=vector,
                limit=top_k
            )
            if not results:
                return self._yaml_schema_context()
            
            return "\n\n".join([r.payload.get('schema_text', '') for r in results])
        except Exception as e:
            logging.error(f"Qdrant Search Error: {e}")
            return self._yaml_schema_context()

    def index_tables(self):
        """Load configured table metadata into Qdrant."""
        if not self.available:
            return

        points = []
        for idx, (name, details) in enumerate(config.tables['tables'].items()):
            full_name = details.get("full_name", name)
            schema = details.get("schema", "dbo")
            relationships = self._format_relationships(details.get("relationships", []))
            txt = (
                f"Table: {full_name}. Schema: {schema}. Logical name: {name}. "
                f"Columns: {details['allowed_columns']}. Info: {details['description']}. "
                f"{relationships} "
                f"Use {full_name} in SQL queries."
            )
            points.append(models.PointStruct(
                id=idx, 
                vector=self.model.encode(txt).tolist(),
                payload={"schema_text": txt}
            ))
        if points:
            try:
                self.client.upsert(collection_name=self.collection, points=points)
            except Exception as e:
                self.available = False
                logging.error(f"Qdrant Index Error: {e}")

    @staticmethod
    def _yaml_schema_context() -> str:
        schema_lines = []
        for name, details in (config.tables.get("tables") or {}).items():
            full_name = details.get("full_name", name)
            schema = details.get("schema", "dbo")
            relationships = SchemaRetriever._format_relationships(details.get("relationships", []))
            schema_lines.append(
                f"Table: {full_name}. Schema: {schema}. Logical name: {name}. "
                f"Columns: {details.get('allowed_columns', [])}. "
                f"Info: {details.get('description', '')}. {relationships} "
                f"Use {full_name} in SQL queries."
            )
        return "\n\n".join(schema_lines)

    @staticmethod
    def _format_relationships(relationships: list[dict]) -> str:
        if not relationships:
            return ""

        formatted = []
        for relationship in relationships:
            formatted.append(
                "Relationship: "
                f"{relationship.get('from_column')} joins to "
                f"{relationship.get('to_table')}.{relationship.get('to_column')}."
            )
        return " ".join(formatted)
