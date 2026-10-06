"""Print the documents retrieved for a question before they are sent to the LLM."""
from retriever import build_retriever


def main():
    retriever = build_retriever()
    question = input("Question: ").strip()
    docs = retriever.invoke(question)

    for i, doc in enumerate(docs, 1):
        print(f"\n--- Retrieved document {i} ---")
        print("Metadata:", doc.metadata)
        print(doc.page_content)


if __name__ == "__main__":
    main()
