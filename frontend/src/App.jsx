import { useState } from 'react'
import './App.css'


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

    setMessages((currentMessages) => [
      ...currentMessages,
      userMessage,
    ])

    setQuestion('')
    setIsLoading(true)

    try {
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

      if (!response.ok) {
        throw new Error(
          `API request failed: ${response.status}`,
        )
      }

      const data = await response.json()

      const { answer, source } =
        splitAnswerAndSource(data.answer)

      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        text: answer,
        source,
      }

      setMessages((currentMessages) => [
        ...currentMessages,
        assistantMessage,
      ])
    } catch (error) {
      console.error('Chat request failed:', error)

      const errorMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        text: 'Sorry, I could not connect to the support service. Please try again.',
        source: null,
      }

      setMessages((currentMessages) => [
        ...currentMessages,
        errorMessage,
      ])
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


          {isLoading && (
            <div className="message-row assistant">
              <div className="message-bubble assistant loading-message">
                <span className="message-role">
                  Telecom Assistant
                </span>

                <p>Thinking...</p>
              </div>
            </div>
          )}

        </main>


        <form
          className="chat-input-area"
          onSubmit={handleSubmit}
        >
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