"""
Builds one merged retriever across all three Chroma collections:
- faq     : FAQ entries
- tickets : resolved support tickets
- guides  : PDF guide chunks

Retrieves candidates from each collection and keeps the best matches overall.
"""

import os

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.runnables import RunnableLambda, Runnable
from langchain_core.documents import Document


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_store")
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def _get_stores():
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBED_MODEL
    )

    return [
        Chroma(
            collection_name="faq",
            embedding_function=embeddings,
            persist_directory=CHROMA_DIR,
        ),
        Chroma(
            collection_name="tickets",
            embedding_function=embeddings,
            persist_directory=CHROMA_DIR,
        ),
        Chroma(
            collection_name="guides",
            embedding_function=embeddings,
            persist_directory=CHROMA_DIR,
        ),
    ]


# Returns documents + distance scores
def build_scored_retriever(
    k_per_source: int = 4,
    final_k: int = 5,
) -> RunnableLambda:

    stores = _get_stores()

    def retrieve(query: str):
        candidates = []

        for store in stores:
            for doc, distance in store.similarity_search_with_score(
                query,
                k=k_per_source,
            ):
                candidates.append((doc, float(distance)))

        # Smaller distance = better match
        candidates.sort(key=lambda item: item[1])

        return candidates[:final_k]

    return RunnableLambda(retrieve)


# Existing retriever - returns only documents
def build_retriever(
    k_per_source: int = 4,
    final_k: int = 5,
) -> Runnable[str, list[Document]]:

    scored_retriever = build_scored_retriever(
        k_per_source=k_per_source,
        final_k=final_k,
    )

    def remove_scores(results) -> list[Document]:
        return [
            doc for doc, distance in results
        ]

    return scored_retriever | RunnableLambda(remove_scores)