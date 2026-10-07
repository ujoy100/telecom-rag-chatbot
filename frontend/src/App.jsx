import { useState } from 'react'
import './App.css'

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"

function splitAnswerAndSource(text) {
  const citationPattern =
    /\[(FAQ \d+|Ticket [^\]]+|Guide p\. [^\]]+)\]\s*$/

  const match = text.match(citationPattern)

  if (!match) {
    return {
      answer: text,
      source: null,
    }
  }

  return {
    answer: text.slice(0, match.index).trim(),
    source: match[1],
  }
}


function App() {
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


  async function handleSubmit(event) {
    event.preventDefault()
  
    const trimmedQuestion = question.trim()
  
    if (!trimmedQuestion || isLoading) {
      return
    }
  
    const userMessage = {
      id: Date.now(),
      role: 'user',
      text: trimmedQuestion,
      source: null,
    }
  
    const assistantMessageId = Date.now() + 1
  
    const assistantMessage = {
      id: assistantMessageId,
      role: 'assistant',
      text: '',
      source: null,
    }
  
    setMessages((currentMessages) => [
      ...currentMessages,
      userMessage,
      assistantMessage,
    ])
  
    setQuestion('')
    setIsLoading(true)
  
    try {
      const response = await fetch(
        `${API_BASE_URL}/chat/stream`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            question: trimmedQuestion,
            provider,
          }),
        },
      )
  
      if (!response.ok) {
        throw new Error(
          `API request failed: ${response.status}`,
        )
      }
  
      if (!response.body) {
        throw new Error('Streaming response is not available.')
      }
  
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
  
      let fullText = ''
  
      while (true) {
        const { value, done } = await reader.read()
  
        if (done) {
          break
        }
  
        const chunk = decoder.decode(value, {
          stream: true,
        })
  
        fullText += chunk
  
        setMessages((currentMessages) =>
          currentMessages.map((message) =>
            message.id === assistantMessageId
              ? {
                  ...message,
                  text: fullText,
                }
              : message,
          ),
        )
      }
  
      fullText += decoder.decode()
  
      const { answer, source } =
        splitAnswerAndSource(fullText)
  
      setMessages((currentMessages) =>
        currentMessages.map((message) =>
          message.id === assistantMessageId
            ? {
                ...message,
                text: answer,
                source,
              }
            : message,
        ),
      )
    } catch (error) {
      console.error('Chat request failed:', error)
  
      setMessages((currentMessages) =>
        currentMessages.map((message) =>
          message.id === assistantMessageId
            ? {
                ...message,
                text: 'Sorry, I could not connect to the support service. Please try again.',
                source: null,
              }
            : message,
        ),
      )
    } finally {
      setIsLoading(false)
    }
  } 


  return (
    <div className="app">
      <div className="chat-container">

        <header className="chat-header">
          <div className="brand-icon">
            AI
          </div>

          <div>
            <h1>Telecom AI Assistant</h1>
            <p>RAG-powered customer support</p>
          </div>
        </header>


        <main className="chat-messages">

          {messages.map((message) => (
            <div
              key={message.id}
              className={`message-row ${message.role}`}
            >
              <div
                className={`message-bubble ${message.role}`}
              >
                <span className="message-role">
                  {message.role === 'assistant'
                    ? 'Telecom Assistant'
                    : 'You'}
                </span>

                <p>{message.text}</p>

                {message.source && (
                  <div className="source-badge">
                    Source: {message.source}
                  </div>
                )}
              </div>
            </div>
          ))}

        </main>


        <form
          className="chat-input-area"
          onSubmit={handleSubmit}
        >
          <select
            value={provider}
            onChange={(event) => setProvider(event.target.value)}
            disabled={isLoading}
            aria-label="AI model"
          >

            <option value="groq">Groq Qwen</option>
            <option value="openai">OpenAI GPT</option>
          </select>

          <input
            type="text"
            value={question}
            onChange={(event) =>
              setQuestion(event.target.value)
            }
            placeholder={
              isLoading
                ? 'Waiting for response...'
                : 'Ask a telecom question...'
            }
            aria-label="Telecom question"
            disabled={isLoading}
          />

          <button
            type="submit"
            disabled={isLoading}
          >
            {isLoading ? 'Waiting...' : 'Send'}
          </button>
        </form>

      </div>
    </div>
  )
}

export default App