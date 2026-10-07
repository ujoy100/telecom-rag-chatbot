# Telecom RAG Chatbot

A full-stack **Retrieval-Augmented Generation (RAG)** customer-support
application for telecom use cases.

The project combines a **React/Vite frontend**, **FastAPI backend**,
**LangChain**, **Chroma**, **Hugging Face embeddings**, and selectable
**Groq Qwen / OpenAI GPT** LLM providers. It retrieves information from
multiple telecom knowledge sources, applies a confidence check, streams
grounded answers to the UI, and displays source citations.

------------------------------------------------------------------------

## Demo

### FAQ Retrieval

![FAQ response](docs/screenshots/01-faq-response.png)

The assistant retrieves a relevant FAQ and displays the source
separately in the UI.

``` text
Source: FAQ 2
```

### Resolved Ticket Retrieval

![Resolved ticket response](docs/screenshots/02-ticket-response.png)

The system can retrieve similar previously resolved customer-support
cases.

``` text
Source: Ticket TK-008
```

### Low-Confidence Fallback

![Fallback response](docs/screenshots/03-fallback-response.png)

When the retrieved context is not sufficiently relevant, the application
skips the LLM and returns a controlled fallback response:

``` text
I don't know based on the available knowledge base. Please call 611 for assistance.
```

No source badge is displayed for fallback responses.

------------------------------------------------------------------------
### Runtime Model Selection

The React interface allows the user to switch between **Groq Qwen** and **OpenAI GPT** at runtime without restarting the backend.

#### Groq Qwen

![Groq Qwen model selection](docs/screenshots/04-groq-model-selection.png)

The request is processed using the Groq-hosted Qwen model while using the same RAG retrieval pipeline and source-citation logic.

#### OpenAI GPT

![OpenAI GPT model selection](docs/screenshots/05-openai-model-selection.png)

The same interface can switch to OpenAI GPT while continuing to use the shared telecom knowledge base, confidence check, and citation pipeline.

---
## Key Features

-   Multi-source Retrieval-Augmented Generation
-   FAQ knowledge-base retrieval
-   Resolved support-ticket retrieval
-   Telecom PDF guide retrieval
-   Hugging Face sentence embeddings
-   Chroma vector database
-   LangChain RAG orchestration
-   Runtime LLM selection between **Groq Qwen** and **OpenAI GPT**
-   Streaming LLM responses
-   Progressive React chat rendering
-   Source-aware answers
-   FAQ, ticket, and guide citations
-   Confidence-based fallback that avoids unnecessary LLM calls
-   Shared cached retriever across LLM providers
-   React source badges
-   Disabled controls during active requests
-   Duplicate-submit protection
-   Friendly API/network error handling
-   FastAPI REST and streaming endpoints
-   React/Vite frontend
-   Retrieval evaluation using Recall@3

------------------------------------------------------------------------

## Architecture

``` mermaid
flowchart TD
    A[Customer] --> B[React/Vite Chat Interface]
    B --> C{Select LLM Provider}
    C -->|Groq Qwen| D[FastAPI Backend]
    C -->|OpenAI GPT| D

    D -->|POST /chat| E[Standard Response Path]
    D -->|POST /chat/stream| F[Streaming Response Path]

    E --> G[LangChain RAG Chain]
    F --> G

    G --> H[Shared Cached Retriever]
    H --> I[Hugging Face Embedding Model]
    I --> J[Chroma Vector Database]

    J --> K[FAQ Collection]
    J --> L[Resolved Tickets Collection]
    J --> M[Telecom Guide Collection]

    K --> N[Rank Retrieved Documents]
    L --> N
    M --> N

    N --> O{Confidence Check}

    O -->|High Confidence| P{Selected LLM}
    P --> Q[Groq Qwen]
    P --> R[OpenAI GPT]

    O -->|Low Confidence| S[Fallback Response]

    Q --> T[Grounded Answer + Citation]
    R --> T

    T --> U[Standard or Streaming Response]
    S --> U
    U --> B
```

For more detail, see:

``` text
docs/ARCHITECTURE.md
```

------------------------------------------------------------------------

## RAG Flow

``` text
Customer Question
        |
        v
React Frontend
        |
        | question + selected provider
        v
FastAPI
        |
        v
Shared Cached Retriever
        |
        v
Query Embedding
        |
        v
Chroma Retrieval
        |
        +-- FAQ
        +-- Resolved Tickets
        +-- Telecom Guide
        |
        v
Merge + Rank by Distance
        |
        v
Best Retrieved Document
        |
        v
Confidence Check
       / \
      /   \
     v     v
Confident  Low Confidence
   |            |
   v            v
Selected LLM   Fallback
Groq/OpenAI    (no LLM call)
   |
   v
Grounded Answer
   |
   v
Source Citation
   |
   v
Streaming / Standard API Response
   |
   v
React UI
```

------------------------------------------------------------------------

## Knowledge Sources

The chatbot uses three knowledge sources.

### 1. FAQ Knowledge Base

``` text
backend/data/faq.csv
```

Contains frequently asked telecom customer-support questions.

Current collection:

``` text
faq
25 vectors
```

Example citation:

``` text
[FAQ 2]
```

### 2. Resolved Support Tickets

``` text
backend/data/tickets.db
```

Contains previously resolved customer-support cases stored in SQLite.

Current collection:

``` text
tickets
19 vectors
```

Example citation:

``` text
[Ticket TK-008]
```

Resolved-ticket responses are presented as similar previous cases rather
than guaranteed fixes.

### 3. Telecom Technical Guide

``` text
backend/data/telecom_guide.pdf
```

The telecom guide is chunked before embedding.

Current configuration:

``` text
Pages: 9
Chunk size: 1200
Chunk overlap: 250
Chunks: 23
```

Current collection:

``` text
guides
23 vectors
```

Example citation:

``` text
[Guide p. 6]
```

------------------------------------------------------------------------

## Embedding Model

The project uses:

``` text
sentence-transformers/all-MiniLM-L6-v2
```

The same embedding model is used for knowledge-base ingestion and
customer-query embedding, enabling semantic similarity search across the
Chroma collections.

The retriever is cached and shared by the Groq and OpenAI chains so the
embedding/retrieval stack does not need to be initialized separately for
each provider.

------------------------------------------------------------------------

## Retrieval Strategy

The application searches the FAQ, ticket, and guide collections and
combines the retrieved candidates.

``` text
Customer Query
       |
       +-- FAQ search
       +-- Ticket search
       +-- Guide search
              |
              v
       Merge candidates
              |
              v
       Sort by distance
              |
              v
       Best document
```

Chroma distance is interpreted as:

``` text
Smaller distance = better semantic match
```

The current RAG chain uses the highest-ranked document as the context
supplied to the selected LLM.

------------------------------------------------------------------------

## Confidence-Based Fallback

The project uses a Chroma distance threshold:

``` text
1.2
```

If:

``` text
best distance <= 1.2
```

the application uses the retrieved document and calls the selected LLM.

If:

``` text
best distance > 1.2
```

the LLM branch is skipped and the application returns:

``` text
I don't know based on the available knowledge base. Please call 611 for assistance.
```

This reduces unsupported answers and avoids an unnecessary LLM call for
low-confidence retrievals.

------------------------------------------------------------------------

## LLM Providers

The user can select the LLM provider directly from the React interface.

### Groq

``` text
Provider: Groq
Model: qwen/qwen3.8-27b
```

### OpenAI

``` text
Provider: OpenAI
Model: gpt-4.1-mini
```

Both providers use the same retrieval pipeline, confidence logic,
grounded prompt, and citation format.

The provider is selected at runtime, so the FastAPI server does not need
to be restarted when switching between Groq and OpenAI.

------------------------------------------------------------------------

## Streaming Responses

The project supports progressive response streaming through:

``` text
POST /chat/stream
```

FastAPI uses `StreamingResponse`, while the React frontend reads the
response with:

``` javascript
const reader = response.body.getReader()
const decoder = new TextDecoder()
```

As chunks arrive, React updates the same assistant message so the answer
appears progressively instead of waiting for the complete response.

When streaming finishes, the frontend separates the trailing citation
from the answer and displays it as a source badge.

The low-confidence fallback remains non-generative and may therefore
appear immediately rather than token-by-token.

------------------------------------------------------------------------

## Source Citations

Supported citation formats include:

``` text
[FAQ 2]
[Ticket TK-008]
[Guide p. 6]
```

The backend includes the citation in the grounded answer. The React
frontend separates it from the answer text and renders it as a badge:

``` text
Source: FAQ 2
```

Fallback and connection-error responses do not display a source badge.

------------------------------------------------------------------------

## Backend API

The backend is implemented with **FastAPI**.

Main application:

``` text
backend/api.py
```

Available endpoints:

``` text
GET  /health
POST /chat
POST /chat/stream
```

### Health Check

``` bash
curl http://127.0.0.1:8000/health
```

Example response:

``` json
{
  "status": "ok"
}
```

### Standard Chat Endpoint

Groq example:

``` bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"How can I activate international roaming?","provider":"groq"}'
```

OpenAI example:

``` bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"How can I activate international roaming?","provider":"openai"}'
```

Example JSON response:

``` json
{
  "answer": "To activate international roaming ... [FAQ 9]"
}
```

### Streaming Chat Endpoint

Groq:

``` bash
curl -N -X POST http://127.0.0.1:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"question":"How can I activate international roaming?","provider":"groq"}'
```

OpenAI:

``` bash
curl -N -X POST http://127.0.0.1:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"question":"How can I activate international roaming?","provider":"openai"}'
```

`curl -N` disables curl output buffering so streamed chunks can be
displayed as they arrive.

------------------------------------------------------------------------

## Frontend

The user interface is built with:

``` text
React
Vite
CSS
```

Main component:

``` text
frontend/src/App.jsx
```

The frontend provides:

-   customer question input
-   conversation history
-   user and assistant message bubbles
-   Groq/OpenAI runtime model selector
-   progressive streamed answers
-   citation badges
-   disabled controls while processing
-   duplicate-submit protection
-   low-confidence fallback responses
-   friendly connection errors
-   responsive layout

During a request, the provider selector, input, and Send button are
disabled to prevent accidental duplicate submissions. The assistant
message is created immediately and progressively updated as streamed
text arrives.

------------------------------------------------------------------------

## Error Handling

If the backend cannot be reached, React displays:

``` text
Sorry, I could not connect to the support service. Please try again.
```

No source badge is displayed for an error response.

The API also validates provider selection and distinguishes
unsupported-provider errors from unexpected server errors.

------------------------------------------------------------------------

## Retrieval Evaluation

The project includes:

``` text
backend/eval_retrieval.py
```

The current evaluation set contains:

``` text
10 handcrafted resolved-ticket queries
```

Metric:

``` text
Recall@3
```

Current result:

``` text
10 / 10
Recall@3 = 100%
```

The expected ticket was retrieved within the top three results for all
current evaluation questions.

> This result describes the current small handcrafted evaluation set and
> should not be interpreted as a production-scale benchmark.

------------------------------------------------------------------------

## Example Queries

### FAQ

``` text
How do I activate 4G/LTE on my phone?
```

Expected source:

``` text
FAQ 3
```

### Resolved Ticket

``` text
My 4G speed is below 1 Mbps in the city centre.
```

Expected source:

``` text
Ticket TK-008
```

### Telecom Guide

``` text
What is SIM swap fraud?
```

Expected source:

``` text
Guide p. 6
```

### International Roaming

``` text
How can I activate international roaming?
```

Expected source:

``` text
FAQ 9
```

### Low-Confidence Query

``` text
How do I bake a chocolate cake?
```

Expected result:

``` text
I don't know based on the available knowledge base. Please call 611 for assistance.
```

------------------------------------------------------------------------

## Project Structure

``` text
telecom-rag-chatbot/
├── backend/
│   ├── __init__.py
│   ├── api.py
│   ├── chroma_store/          # generated locally
│   ├── data/
│   │   ├── faq.csv
│   │   ├── telecom_guide.pdf
│   │   └── tickets.db
│   ├── debug_retrieval.py
│   ├── eval_retrieval.py
│   ├── ingest_faq.py
│   ├── ingest_pdf.py
│   ├── ingest_tickets.py
│   ├── rag_chain.py
│   └── retriever.py
├── docs/
│   ├── ARCHITECTURE.md
│   └── screenshots/
│       ├── 01-faq-response.png
│       ├── 02-ticket-response.png
│       ├── 03-fallback-response.png
│       ├── 04-groq-model-selection.png
│       └── 05-openai-model-selection.png
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── assets/
│   │   ├── App.css
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   ├── eslint.config.js
│   ├── index.html
│   ├── package-lock.json
│   ├── package.json
│   └── vite.config.js
├── .env.example
├── .gitignore
├── .python-version
├── BUILD_LOG.md
├── README.md
├── pyproject.toml
├── requirements.txt
└── uv.lock
```

Generated/local files such as `.env`, `.venv`, `frontend/node_modules`,
`frontend/dist`, and `backend/chroma_store` are excluded from Git.

------------------------------------------------------------------------

## Local Setup

### 1. Clone the Repository

``` bash
git clone https://github.com/ujoy100/telecom-rag-chatbot.git
cd telecom-rag-chatbot
```

### 2. Create the Python Environment

Install Python dependencies using `uv`:

``` bash
uv sync
```

Activate the environment if required:

``` bash
source .venv/bin/activate
```

### 3. Configure LLM API Keys

Create a local `.env` file:

``` bash
cp .env.example .env
```

Add the provider keys you intend to use:

``` env
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

Never commit the real `.env` file.

`LLM_PROVIDER` provides a default/fallback provider for the backend. The
React interface sends the selected provider with each chat request.

### 4. Build the Vector Knowledge Base

``` bash
python backend/ingest_faq.py
python backend/ingest_tickets.py
python backend/ingest_pdf.py
```

This generates the local Chroma vector database.

### 5. Start the FastAPI Backend

From the project root:

``` bash
uvicorn backend.api:app
```

Backend:

``` text
http://127.0.0.1:8000
```

Swagger API documentation:

``` text
http://127.0.0.1:8000/docs
```

### 6. Start the React Frontend

Open another terminal:

``` bash
cd frontend
npm install
npm run dev
```

Frontend:

``` text
http://localhost:5173
```

------------------------------------------------------------------------

## Development Flow

Use two terminals during local development.

Terminal 1:

``` bash
cd /path/to/telecom-rag-chatbot
uvicorn backend.api:app
```

Terminal 2:

``` bash
cd /path/to/telecom-rag-chatbot/frontend
npm run dev
```

Then open:

``` text
http://localhost:5173
```

------------------------------------------------------------------------

## Validation

### Backend Syntax Check

``` bash
python -m py_compile backend/rag_chain.py backend/api.py
```

### Frontend Lint

``` bash
cd frontend
npm run lint
```

### Frontend Production Build

``` bash
npm run build
```

The production frontend is generated under:

``` text
frontend/dist/
```

------------------------------------------------------------------------

## Technology Stack

  Layer                      Technology
  -------------------------- -------------------------------------------------
  Frontend                   React
  Build Tool                 Vite
  Frontend Linting           ESLint
  Backend                    FastAPI
  Streaming                  FastAPI `StreamingResponse` + Fetch Streams API
  RAG Framework              LangChain
  Vector Database            Chroma
  Embeddings                 Hugging Face Sentence Transformers
  Embedding Model            `sentence-transformers/all-MiniLM-L6-v2`
  LLM Providers              Groq, OpenAI
  LLM Models                 Qwen `qwen/qwen3.8-27b`, OpenAI `gpt-4.1-mini`
  Ticket Database            SQLite
  PDF Processing             PyPDF
  Python Package Manager     uv
  Frontend Package Manager   npm
  Version Control            Git / GitHub

------------------------------------------------------------------------

## What This Project Demonstrates

This project demonstrates practical implementation of:

-   end-to-end RAG architecture
-   multi-source retrieval
-   vector search and semantic embeddings
-   retrieval confidence handling
-   hallucination reduction through fallback logic
-   prompt grounding and source attribution
-   multi-provider LLM integration
-   runtime provider selection
-   streamed LLM responses
-   React stream consumption and progressive rendering
-   FastAPI REST/streaming API design
-   React/FastAPI integration
-   retriever reuse/caching
-   frontend asynchronous state management
-   retrieval evaluation
-   secure API-key management
-   reproducible project organization

------------------------------------------------------------------------

## Future Improvements

Potential improvements include:

-   reranking retrieved documents
-   hybrid lexical + vector search
-   structured citation metadata from the backend
-   conversation memory
-   automated evaluation with larger datasets
-   authentication and rate limiting
-   Docker deployment
-   cloud deployment
-   observability and tracing
-   automated tests and CI/CD

------------------------------------------------------------------------

## Documentation

Detailed architecture:

``` text
docs/ARCHITECTURE.md
```

Development history:

``` text
BUILD_LOG.md
```

------------------------------------------------------------------------

## Status

The current portfolio version includes:

``` text
Multi-source retrieval           ✅
Confidence fallback              ✅
Source citations                 ✅
Retrieval evaluation             ✅
FastAPI backend                  ✅
React/Vite frontend              ✅
Groq Qwen provider               ✅
OpenAI GPT provider              ✅
Runtime model selector           ✅
Standard /chat endpoint          ✅
Streaming /chat/stream endpoint  ✅
Progressive React streaming      ✅
Shared cached retriever          ✅
Source badges                    ✅
Error handling                   ✅
Architecture documentation       ✅
Portfolio screenshots            ✅
```
