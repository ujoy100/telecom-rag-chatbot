import os

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_store")

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

TOP_K = 3


TEST_CASES = [
    {
        "question": "I switched from 3G to 4G and now I have no mobile internet.",
        "expected_ticket_id": "TK-001",
    },
    {
        "question": "My signal drops to zero several times every day.",
        "expected_ticket_id": "TK-002",
    },
    {
        "question": "I bought a 5 GB add-on but my data balance has not updated.",
        "expected_ticket_id": "TK-003",
    },
    {
        "question": "I returned from Spain and have unexpected roaming charges.",
        "expected_ticket_id": "TK-004",
    },
    {
        "question": "After updating my Android phone it says SIM not provisioned.",
        "expected_ticket_id": "TK-005",
    },
    {
        "question": "I was charged twice for my monthly plan.",
        "expected_ticket_id": "TK-006",
    },
    {
        "question": "All incoming calls go directly to voicemail even though I have full signal.",
        "expected_ticket_id": "TK-007",
    },
    {
        "question": "My 4G speed is below 1 Mbps in the city centre.",
        "expected_ticket_id": "TK-008",
    },
    {
        "question": "My iPhone eSIM QR code keeps failing during activation.",
        "expected_ticket_id": "TK-009",
    },
    {
        "question": "I have international roaming enabled but no service in Tokyo.",
        "expected_ticket_id": "TK-012",
    },
]


def main():
    # Load the same embedding model used during ingestion
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBED_MODEL
    )

    # Open only the tickets collection
    ticket_store = Chroma(
        collection_name="tickets",
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR,
    )

    # Count successful retrievals
    hits = 0

    # Test each question
    for i, test in enumerate(TEST_CASES, 1):
        question = test["question"]
        expected = test["expected_ticket_id"]

        # Retrieve top 3 tickets with distance scores
        results = ticket_store.similarity_search_with_score(
            question,
            k=TOP_K,
        )

        # Extract retrieved ticket IDs
        retrieved_ids = [
            doc.metadata.get("ticket_id")
            for doc, score in results
        ]

        # Check whether expected ticket is in top 3
        hit = expected in retrieved_ids

        if hit:
            hits += 1

        print(f"\nTest {i}")
        print(f"Question: {question}")
        print(f"Expected: {expected}")
        print(f"Retrieved: {retrieved_ids}")
        print(f"Result: {'PASS' if hit else 'FAIL'}")

        # Show ranking and Chroma distance
        for rank, (doc, score) in enumerate(results, 1):
            print(
                f"  Rank {rank}: "
                f"{doc.metadata.get('ticket_id')} "
                f"distance={score:.4f}"
            )

    # Calculate Recall@3
    recall_at_3 = hits / len(TEST_CASES)

    print("\n==============================")
    print("Retrieval Evaluation")
    print("==============================")
    print(f"Hits: {hits}/{len(TEST_CASES)}")
    print(f"Recall@3: {recall_at_3:.2%}")


if __name__ == "__main__":
    main()