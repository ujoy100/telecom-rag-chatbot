# Telecom RAG Chatbot

React Frontend Creation, New Features & Git Documentation Technical
implementation notes covering React/Vite setup, FastAPI integration,
runtime LLM selection, performance optimization, streaming responses,
testing, production build, and Git/GitHub workflow.  1. Frontend
Technology - React - Vite - JavaScript / JSX - CSS - FastAPI backend -
Fetch API - Streaming responses - Runtime LLM selection: Groq Qwen /
OpenAI GPT Backend development URL:

```text
http://127.0.0.1:8000
```

Vite frontend development URL:

```text
http://localhost:5173
```

## Project Initialization with uv and Git

At the beginning of the Python project, `uv init` can be used to
initialize the project:

```bash
cd /Users/ushajoy/SEM4/telecom-rag-chatbot
uv init
```

`uv init` initializes the uv/Python project and, by default, can also
initialize a local Git repository when Git is available. It does **not**
create a repository on GitHub.

Check whether Git is already initialized:

```bash
git status
```

You can also check for the hidden `.git` directory:

```bash
ls -a
```

If `.git` exists, the folder is already a local Git repository.

If Git was not initialized by `uv init`, or if the project was created
without Git, initialize it manually:

```bash
git init
```

Therefore, the relationship is:

```text
uv init
   ↓
Initialize the uv/Python project
   ↓
May also initialize local Git (.git) by default
   ↓
git init
   ↓
Use manually if Git is not already initialized
   ↓
Neither command creates a GitHub repository
```

Running `git init` in an already initialized Git repository is normally
unnecessary. For this project, first use `git status` to confirm whether
the repository already exists.

## 2. Create the React Frontend

From the project root:

```text
cd /Users/ushajoy/SEM4/telecom-rag-chatbot
```

Create the Vite React application: Create a new React application using
the latest Vite setup and put it inside a folder called frontend.

```text
npm create vite@latest frontend -- --template react
```

Move into the frontend and install dependencies:

```text
cd frontend
npm install
```

Start the development server:

```text
npm run dev
```

Open the frontend in a browser:

```text
http://localhost:5173
```



## 3. Main Frontend Files

```text
frontend/
├── src/
│   ├── App.jsx
│   ├── App.css
│   └── main.jsx
├── package.json
├── package-lock.json
├── eslint.config.js
├── index.html
└── vite.config.js
```

App.jsx contains the chatbot logic and UI. App.css contains the visual
design. main.jsx mounts the React application.

## 4. React State

The frontend uses React useState for the question, selected provider,
messages, and loading state.

```text
import { useState } from 'react'

const [question, setQuestion] = useState('')
const [provider, setProvider] = useState('groq')
const [messages, setMessages] = useState([
  {
    id: 1,
    role: 'assistant',
    text: 'Hello! I am your Telecom AI Assistant. How can I help you today?',
    source: null,
  },
])
const [isLoading, setIsLoading] = useState(false)
```



## 5. Initial Non-Streaming API Integration

The first React version called POST /chat and waited for the complete
JSON response.

```text
const response = await fetch(
  'http://127.0.0.1:8000/chat',
  {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      question: trimmedQuestion,
    }),
  },
)
```



## 6. Source Citation Handling

RAG answers can end with citations such as FAQ 9, Ticket 123, or Guide
p. 4.

```text
function splitAnswerAndSource(text) {
  const citationPattern =
    /\[(FAQ \d+|Ticket [^\]]+|Guide p\. [^\]]+)\]\s*$/

  const match = text.match(citationPattern)

  if (!match) {
    return { answer: text, source: null }
  }

  return {
    answer: text.slice(0, match.index).trim(),
    source: match[1],
  }
}
```

The extracted citation is displayed as a separate Source badge in the
assistant message.

# 7. Runtime LLM Selection

The project was enhanced to allow the user to choose between Groq Qwen
and OpenAI GPT at runtime.

```text
const [provider, setProvider] = useState('groq')

<select
  value={provider}
  onChange={(event) => setProvider(event.target.value)}
  disabled={isLoading}
  aria-label="AI model"
>
  <option value="groq">Groq Qwen</option>
  <option value="openai">OpenAI GPT</option>
</select>
```

The selected provider is sent with each request:

```text
body: JSON.stringify({
  question: trimmedQuestion,
  provider,
})
```



## 8. Backend Multi-Provider Support

FastAPI accepts the provider field and the RAG layer creates the
appropriate LLM.

```text
provider: str = Field(
    default="groq",
    description="LLM provider: groq or openai",
)
```

```text
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
```



## 9. Performance Problem and Optimization

An early runtime-selection implementation called
build_chain(provider=request.provider) inside every /chat request. This
repeatedly rebuilt RAG components and caused noticeable latency. The
optimized version builds both chains once when FastAPI starts:

```text
rag_chains = {
    "groq": build_chain(provider="groq"),
    "openai": build_chain(provider="openai"),
}
```

Each request then selects and reuses the already-built chain:

```text
provider = request.provider.strip().lower()
rag_chain = rag_chains.get(provider)
answer = rag_chain.invoke(request.question)
```



## 10. Backend Syntax Checks

```text
python -m py_compile backend/api.py
```

```text
python -m py_compile backend/rag_chain.py backend/api.py
```

No output means the Python syntax check passed. # 11. Start FastAPI

```text
cd /Users/ushajoy/SEM4/telecom-rag-chatbot
uvicorn backend.api:app
```

Successful startup includes:

```text
INFO: Waiting for application startup.
INFO: Application startup complete.
INFO: Uvicorn running on http://127.0.0.1:8000
```

During development testing, the backend was generally run without
--reload because reload had intermittently caused slower startup in this
environment. # 12. Streaming Response Feature The standard POST /chat
endpoint was retained and a second POST /chat/stream endpoint was added.
This preserves a conventional REST response while providing a streaming
option.

```text
POST /chat
→ complete response

POST /chat/stream
→ progressive streamed response
```

FastAPI streaming uses:

```text
from fastapi.responses import StreamingResponse
```

The existing LangChain pipeline can stream because the normal answer
path ends with prompt → llm → StrOutputParser. The low-confidence
fallback remains separate and does not call the LLM. # 13. Test
Streaming with curl Groq:

```text
curl -N -X POST http://127.0.0.1:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"question":"How can I activate international roaming?","provider":"groq"}'
```

OpenAI:

```text
curl -N -X POST http://127.0.0.1:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"question":"How can I activate international roaming?","provider":"openai"}'
```

The -N option tells curl not to buffer the response. # 14. React
Streaming Implementation The frontend now calls:

```text
http://127.0.0.1:8000/chat/stream
```

The Fetch API response body is read with a stream reader:

```text
const reader = response.body.getReader()
const decoder = new TextDecoder()

let fullText = ''

while (true) {
  const { value, done } = await reader.read()

  if (done) {
    break
  }

  const chunk = decoder.decode(value, { stream: true })
  fullText += chunk

  setMessages((currentMessages) =>
    currentMessages.map((message) =>
      message.id === assistantMessageId
        ? { ...message, text: fullText }
        : message,
    ),
  )
}
```

The same assistant bubble is updated as chunks arrive. When streaming
finishes, splitAnswerAndSource() separates the final citation and
displays it as the source badge. # 15. Frontend Styling - Blue/teal
gradient header - Assistant and user message bubbles - Source citation
badge - Styled Groq/OpenAI model selector - Question input and Send
button - Loading and disabled states - Responsive mobile layout The
model selector was styled with the same border radius, blue accent,
hover/focus treatment, and disabled state as the rest of the chat
controls. # 16. Run Frontend and Backend Together Terminal 1 ---
backend:

```text
cd /Users/ushajoy/SEM4/telecom-rag-chatbot
uvicorn backend.api:app
```

Terminal 2 --- frontend:

```text
cd /Users/ushajoy/SEM4/telecom-rag-chatbot/frontend
npm run dev
```

Open:

```text
http://localhost:5173
```



## 17. Frontend Validation

Lint: 'npm run lint' runs ESLint, which checks your JavaScript/React
code for coding problems such as syntax/style issues, unused variables,
problematic React patterns, and other potential mistakes.

```text
cd frontend
npm run lint → Check the source code for problems
```

Production build: This tells Vite to create the production version of
your React application.

```text
npm run build
```

The latest production build completed successfully with Vite 8.3.3.
Generated production files are placed under:

```text
frontend/dist/  → Final generated production frontend files
```



## 18. .gitignore and Secrets

Important generated or sensitive files should not be committed:

```text
.env
.venv/
__pycache__/
*.pyc
backend/chroma_store/
frontend/node_modules/
frontend/dist/
```

Never commit the real .env file because it contains API keys. Use an
.env.example file with placeholders:

```text
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```



## 19. Git --- First Commit from the Beginning

Go to the project root:

```bash
cd /Users/ushajoy/SEM4/telecom-rag-chatbot
```

First check whether `uv init` has already initialized Git:

```bash
git status
```

If Git is not initialized, initialize the local repository manually:

```bash
git init
```

If `git status` already works and the project contains a `.git`
directory, you do not need to run `git init` again.

Inspect the repository:

```bash
git status
```

Before staging files, make sure `.gitignore` excludes sensitive and
generated content such as `.env`, `.venv/`, `backend/chroma_store/`,
`frontend/node_modules/`, and `frontend/dist/`.

Stage the project files:

```bash
git add .
```

Check the staged files:

```bash
git status
```

Make sure `.env` and API keys are **not** staged.

Create the first local commit:

```bash
git commit -m "Initial commit: Telecom RAG chatbot"
```

The initial commit created for this project was:

```text
83bdb96  Initial commit: Telecom RAG chatbot
```

At this stage the commit exists in the **local Git repository**. It has
not yet been uploaded to GitHub.

## 20. Create the GitHub Repository

A local Git repository and a GitHub repository are different.

`uv init` and `git init` work locally. They do **not** create a
repository on GitHub.

To create the remote repository:

1. Sign in to GitHub.
2. Click **New repository**.
3. Enter the repository name:

```text
telecom-rag-chatbot
```

1. Choose **Public** if the repository is intended for a portfolio.
2. If README, `.gitignore`, and other project files already exist
  locally, do not initialize duplicate versions on GitHub.
3. Click **Create repository**.

The GitHub repository for this project is:

```text
https://github.com/ujoy100/telecom-rag-chatbot
```

Creating the GitHub repository does not automatically connect it to the
local Git repository.

## 21. Connect the Local Repository to GitHub

Add the GitHub repository as the remote named `origin`:

```bash
git remote add origin https://github.com/ujoy100/telecom-rag-chatbot.git
```

Verify the connection:

```bash
git remote -v
```

Rename the current branch to `main` if necessary:

```bash
git branch -M main
```

Push the first local commit to GitHub:

```bash
git push -u origin main
```

The `-u` option sets `origin/main` as the upstream branch. After this
first push, later commits can normally be uploaded with:

```bash
git push
```



### Complete Initial Git/GitHub Flow

```text
uv init
   ↓
Initialize uv/Python project
   ↓
Check local Git: git status
   ↓
If needed: git init
   ↓
Create/check .gitignore
   ↓
git add .
   ↓
git status
   ↓
git commit -m "Initial commit: Telecom RAG chatbot"
   ↓
Create telecom-rag-chatbot repository on GitHub
   ↓
git remote add origin https://github.com/ujoy100/telecom-rag-chatbot.git
   ↓
git remote -v
   ↓
git branch -M main
   ↓
git push -u origin main
```



## 22. Git Workflow After Making Changes

```text
git status
git diff
git add .
git status
git commit -m "Add runtime OpenAI and Groq model selection"
git push
```

Before every commit, check git status and make sure .env or other
secrets are not staged. # 23. Current Feature Commit The current
development batch includes: - OpenAI integration - Groq integration -
Runtime model selector - Styled model dropdown - Cached/reused RAG
chains - Reduced per-request latency - FastAPI streaming endpoint -
Streaming React UI - Source citation preserved after streaming
Recommended commit after the README is updated and final tests pass:

```text
git add .
git status
git commit -m "Add multi-provider LLM selection and streaming responses"
git push
```



## 24. Useful Git Commands

```text
git status             # Check repository status
git diff               # View unstaged changes
git diff --staged      # View staged changes
git add .              # Stage all changes
git add backend/api.py # Stage one file
git commit -m "..."    # Create a commit
git log --oneline      # View concise history
git remote -v          # View configured remotes
git branch             # View branches
git branch -M main     # Rename current branch to main
git push               # Push commits
git pull               # Pull remote changes
```



## 25. Current Architecture

```text
React + Vite
     |
     | question + provider
     v
FastAPI
     |
     +-- POST /chat
     |      +-- Standard response
     |
     +-- POST /chat/stream
             |
             v
       Reused RAG Chain
             |
             v
       Chroma Retriever
             |
             v
       Confidence Check
        |           |
    confident    low confidence
        |           |
        v           v
 Groq / OpenAI    Fallback
        |
        v
 Streaming response
        |
        v
 React progressively
 updates assistant bubble
        |
        v
 Source badge
 FAQ / Ticket / Guide
```



## 26. Portfolio Value

The project now demonstrates full-stack RAG development, multi-provider
LLM integration, retrieval confidence handling, fallback logic, FastAPI
API design, streaming responses, React state management,
frontend/backend integration, source citations, performance
optimization, production frontend builds, and Git/GitHub workflow.