"""
Builds the RAG chain:
retriever -> confidence check -> grounded prompt
-> selected LLM provider (OpenAI or Groq) -> string output
"""

from pathlib import Path
from functools import lru_cache
from dotenv import load_dotenv

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnableBranch
from langchain_core.documents import Document
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

from backend.retriever import build_scored_retriever
import os


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")
# ---------------------------------------------------------
# Confidence / fallback settings
# Chroma distance: smaller = better match
# ---------------------------------------------------------

DISTANCE_THRESHOLD = 1.2

FALLBACK_MESSAGE = (
    "I don't know based on the available knowledge base. "
    "Please call 611 for assistance."
)


# ---------------------------------------------------------
# System prompt
# ---------------------------------------------------------

SYSTEM_PROMPT = """
You are a helpful and professional telecom customer care assistant.

Answer the customer's question using ONLY the provided context.

The context may contain:
- FAQ entries
- Previously resolved support tickets
- Technical guide documentation

Rules:

1. Prefer the highest-ranked document that directly answers the question.

2. If the best source is an FAQ:
   - Answer primarily from that FAQ.
   - Include all important facts and recommended actions from that FAQ.
   - Keep the answer short and direct.
   - Do not add ticket or guide information unless the FAQ is insufficient.

3. If the best source is a resolved support ticket:
   - Start with "In a similar previously resolved case..."
   - Give the specific problem, identified cause, and resolution from that ticket.
   - Make clear that the resolution applied to that particular case.
   - Do not present the ticket-specific fix as a guaranteed solution.
   - Use FAQ or guide information only if essential.
   - Do not repeat troubleshooting advice already stated.

4. If the best source is the technical guide:
   - Explain the concept clearly.
   - Include important risks, prevention advice, or troubleshooting steps
     contained in the relevant guide section.
   - Do not add unrelated FAQ or ticket information.

5. Use secondary documents only when the highest-ranked document
   does not contain enough information to answer the question.

6. Do not combine loosely related information from different documents.

7. Do not repeat the same fact, recommendation, or troubleshooting step.

8. Use the source citation exactly as provided in the context.

9. Include the source citation at the end of the answer.

10. Never invent or modify a citation.

11. Do not invent facts, phone numbers, URLs, timings, policies,
    technical fixes, or recommendations.

12. Keep the answer concise, natural, and customer-friendly.

13. Do not start answers with phrases such as
    "Based on the provided context."

14. If the context does not contain enough information, say so clearly.

Context:
{context}
"""


# ---------------------------------------------------------
# Source citation
# ---------------------------------------------------------

def _source_label(doc: Document) -> str:
    source = doc.metadata.get("source", "unknown")

    if source == "faq":
        faq_id = doc.metadata.get("faq_id", "?")
        return f"[FAQ {faq_id}]"

    if source == "ticket":
        ticket_id = doc.metadata.get("ticket_id", "?")
        return f"[Ticket {ticket_id}]"

    if source == "guide":
        page = doc.metadata.get("page_number", "?")
        return f"[Guide p. {page}]"

    return "[Unknown Source]"


# ---------------------------------------------------------
# Format retrieved document
# ---------------------------------------------------------

def _format_docs(docs: list[Document]) -> str:
    if not docs:
        return "No relevant context found."

    # Use only the highest-ranked document
    doc = docs[0]
    citation = _source_label(doc)

    return (
        f"Source citation: {citation}\n\n"
        f"{doc.page_content}"
    )


# ---------------------------------------------------------
# Build RAG chain
# ---------------------------------------------------------
@lru_cache(maxsize=1)
def get_scored_retriever():
    return build_scored_retriever()

def build_chain(provider: str | None = None):
    scored_retriever = get_scored_retriever()

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{question}"),
    ])

   
    provider = (provider or os.getenv("LLM_PROVIDER", "groq")).strip().lower()

    if provider == "openai":
        llm = ChatOpenAI(
            model="gpt-4.1-mini",
            temperature=0,
            max_tokens=400,
            max_retries=2,
        )

    elif provider == "groq":
        llm = ChatGroq(
            model="qwen/qwen3.8-27b",
            temperature=0,
            max_tokens=400,
            reasoning_format="parsed",
            timeout=None,
            max_retries=2,
        )

    else:
        raise ValueError(
            f"Unsupported LLM_PROVIDER: {provider}. "
            "Use 'openai' or 'groq'."
        )
    # -----------------------------------------------------
    # Retrieve best document and check confidence
    # -----------------------------------------------------

    def prepare_input(question: str):
        results = scored_retriever.invoke(question)

        if not results:
            return {
                "question": question,
                "context": "",
                "confident": False,
            }

        best_doc, best_distance = results[0]

        # print(f"Best distance: {best_distance:.4f}")

        return {
            "question": question,
            "context": _format_docs([best_doc]),
            "confident": best_distance <= DISTANCE_THRESHOLD,
        }

    # -----------------------------------------------------
    # Normal RAG answer
    # -----------------------------------------------------

    answer_chain = (
        prompt
        | llm
        | StrOutputParser()
    )

    # -----------------------------------------------------
    # Fallback answer
    # LLM is NOT called
    # -----------------------------------------------------

    fallback_chain = RunnableLambda(
        lambda x: FALLBACK_MESSAGE
    )

    # -----------------------------------------------------
    # Branch based on confidence
    # -----------------------------------------------------

    chain = (
        RunnableLambda(prepare_input)
        | RunnableBranch(
            (
                lambda x: not x["confident"],
                fallback_chain,
            ),
            answer_chain,
        )
    )

    return chain