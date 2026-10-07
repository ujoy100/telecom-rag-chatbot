from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

load_dotenv()

EMBED_MODEL = "text-embedding-3-small"


def get_embeddings():
    """Return the embedding model shared by ingestion and retrieval."""
    return OpenAIEmbeddings(model=EMBED_MODEL)