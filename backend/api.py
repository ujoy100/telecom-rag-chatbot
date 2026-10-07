"""
FastAPI backend for the Telecom RAG Chatbot.

Endpoints:
- GET  /health
- POST /chat
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.rag_chain import build_chain


# ---------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------

app = FastAPI(
    title="Telecom RAG Chatbot API",
    description=(
        "REST API for a telecom customer-care RAG assistant "
        "using LangChain, Chroma, Hugging Face embeddings, "
        "and selectable Groq or OpenAI LLM providers."
    ),
    version="1.0.0",
)

# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

# React/Vite will run on port 5173 during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# Build RAG chains once when the backend starts
# ---------------------------------------------------------

rag_chains = {
    "groq": build_chain(provider="groq"),
    "openai": build_chain(provider="openai"),
}


# ---------------------------------------------------------
# Request / response models
# ---------------------------------------------------------


class ChatRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        description="Customer telecom question",
    )

    provider: str = Field(
        default="groq",
        description="LLM provider: groq or openai",
    )


class ChatResponse(BaseModel):
    answer: str


class HealthResponse(BaseModel):
    status: str


# ---------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------


@app.get(
    "/health",
    response_model=HealthResponse,
)
def health_check():
    """
    Check whether the API is running.
    """

    return {
        "status": "ok",
    }


# ---------------------------------------------------------
# Chat endpoint
# ---------------------------------------------------------


@app.post(
    "/chat",
    response_model=ChatResponse,
)
def chat(request: ChatRequest):
    """
    Send a customer question through the Telecom RAG chain.
    """

    try:
        provider = request.provider.strip().lower()

        rag_chain = rag_chains.get(provider)

        if rag_chain is None:
            raise HTTPException(
                status_code=400,
                detail="Unsupported LLM provider. Use 'groq' or 'openai'.",
            )

        answer = rag_chain.invoke(request.question)

        return {"answer": answer}

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Unable to process the question.",
        ) from exc


# ---------------------------------------------------------
# Streaming chat endpoint
# ---------------------------------------------------------


@app.post("/chat/stream")
def chat_stream(request: ChatRequest):
    """
    Stream a customer answer through the Telecom RAG chain.
    """

    provider = request.provider.strip().lower()

    rag_chain = rag_chains.get(provider)

    if rag_chain is None:
        raise HTTPException(
            status_code=400,
            detail="Unsupported LLM provider. Use 'groq' or 'openai'.",
        )

    def generate():
        try:
            for chunk in rag_chain.stream(request.question):
                if chunk:
                    yield chunk
        except Exception:
            yield "\nUnable to process the question."

    return StreamingResponse(
        generate(),
        media_type="text/plain",
    )
