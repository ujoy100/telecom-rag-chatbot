"""
Ingests data/telecom_guide.pdf into the 'guides' Chroma collection.
Uses larger overlapping chunks so a topic, its risk, and its prevention advice
stay together as much as possible.
Run after changing the PDF: python ingest_pdf.py
"""
import os
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_store")
COLLECTION = "guides"
PDF_PATH = os.path.join(BASE_DIR, "data", "telecom_guide.pdf")
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# 600/100 split the Wangiri definition from its prevention advice.
# Larger chunks + overlap keep related sentences together.
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 250


def main():
    print("Loading PDF...")
    loader = PyPDFLoader(PDF_PATH)
    pages = loader.load()
    print(f"  {len(pages)} pages loaded.")

    print(f"Chunking (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " "],
    )
    chunks = splitter.split_documents(pages)

    for i, chunk in enumerate(chunks):
        chunk.metadata["source"] = "guide"
        chunk.metadata["chunk_index"] = i
        if "page" in chunk.metadata:
            chunk.metadata["page_number"] = int(chunk.metadata["page"]) + 1

    print(f"  {len(chunks)} chunks produced.")

    print("Initialising embedding model...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)

    # Remove the old guide collection before rebuilding it.
    # This prevents stale 600-character chunks and duplicate vectors.
    old_store = Chroma(
        collection_name=COLLECTION,
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR,
    )
    try:
        old_store.delete_collection()
        print("  Old 'guides' collection removed.")
    except Exception:
        pass

    print(f"Embedding and storing in Chroma collection '{COLLECTION}'...")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=COLLECTION,
        persist_directory=CHROMA_DIR,
    )
    print(f"  Done. {vectorstore._collection.count()} vectors stored.")


if __name__ == "__main__":
    main()
