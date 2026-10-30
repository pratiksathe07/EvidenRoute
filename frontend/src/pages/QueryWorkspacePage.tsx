import React, { useState, useRef, useEffect, KeyboardEvent } from 'react';
import {
  Send,
  Sparkles,
  Bot,
  User,
  Plus,
  BookOpen,
  ArrowRight,
} from 'lucide-react';
import apiClient from '../services/api';
import { QueryResponse } from '../types/sourceSelection';
import './QueryWorkspacePage.css';

interface CitationItem {
  id: string;
  title: string;
  sourceName?: string;
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: CitationItem[];
  outcome?: 'ANSWER' | 'ABSTAIN' | 'RETRIEVE_MORE' | 'ERROR';
  timestamp: string;
  isError?: boolean;
}

const STARTER_PROMPTS = [
  'Why did the payment API fail after deployment?',
  'What is the database connection timeout limit?',
  'What is the employee leave policy for parental leave?',
  'How do quantum warp drives operate on Mars?',
];

export const QueryWorkspacePage: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom of conversation
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Adjust textarea height automatically
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputValue(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setInputValue('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.focus();
    }
  };

  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend ?? inputValue).trim();
    if (!query || isLoading) return;

    const userMessageId = `user_${Date.now()}`;
    const userMessage: ChatMessage = {
      id: userMessageId,
      role: 'user',
      content: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
    setIsLoading(true);

    try {
      // Send question to actual backend /api/query
      const response = await apiClient.post<QueryResponse>('/api/query', {
        question: query,
        budget: {
          max_source_calls: 5,
          max_candidates: 20,
          max_tokens: 4000,
        },
        enable_stress_test: true,
      });

      const data = response.data;
      const outcome = (data.outcome as 'ANSWER' | 'ABSTAIN' | 'RETRIEVE_MORE') || 'ANSWER';
      let assistantContent = '';
      const citations: CitationItem[] = [];

      if (outcome === 'ANSWER') {
        if (data.final_answer && data.final_answer.trim()) {
          assistantContent = data.final_answer;
        } else {
          // Honest missing capability report when LLM is unconfigured
          assistantContent =
            'The backend identified relevant evidence passages across selected sources, but LLM generative answer synthesis is not configured on this server (GEMINI_API_KEY is not set). You can explore the retrieved passages in the Evidence Explorer.';
        }
      } else if (outcome === 'ABSTAIN') {
        assistantContent =
          data.abstention_reason ||
          'The system abstained: Insufficient authoritative evidence was found to answer this question reliably.';
      } else {
        assistantContent =
          data.abstention_reason ||
          data.final_answer ||
          'Additional context retrieval is required before a definitive answer can be determined.';
      }

      // Extract actual citations returned by backend
      if (Array.isArray(data.citations) && data.citations.length > 0) {
        data.citations.forEach((citeId) => {
          const matchedEvidence = data.retrieved_evidence?.find(
            (e) => e.evidence_id === citeId
          );
          citations.push({
            id: citeId,
            title: matchedEvidence?.title || citeId,
            sourceName: matchedEvidence?.source_id,
          });
        });
      }

      const assistantMessage: ChatMessage = {
        id: `asst_${Date.now()}`,
        role: 'assistant',
        content: assistantContent,
        citations: citations.length > 0 ? citations : undefined,
        outcome,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: unknown) {
      const errorMsg =
        err instanceof Error
          ? err.message
          : 'Backend query service is unreachable (POST /api/query). Ensure the server is running on port 8000.';

      const errorMessage: ChatMessage = {
        id: `err_${Date.now()}`,
        role: 'assistant',
        content: `Error: ${errorMsg}`,
        outcome: 'ERROR',
        isError: true,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="qw-chat-container">
      {/* 1. Header */}
      <header className="qw-chat-header">
        <div className="qw-chat-header-info">
          <div className="qw-chat-avatar-brand">
            <Bot size={20} />
          </div>
          <div className="qw-chat-title-group">
            <h2 className="qw-chat-title">
              Query Workspace
              <span className="qw-status-pill-mini">
                <span className="qw-status-dot-mini" />
                Live
              </span>
            </h2>
            <p className="qw-chat-subtitle">
              Ask questions to receive verified answers grounded in your enterprise knowledge
            </p>
          </div>
        </div>

        <div className="qw-chat-header-actions">
          <button
            type="button"
            className="qw-new-chat-btn"
            onClick={handleNewChat}
            title="Start a new chat conversation"
          >
            <Plus size={15} />
            <span>New Chat</span>
          </button>
        </div>
      </header>

      {/* 2. Messages Feed */}
      <div className="qw-chat-messages-container" aria-label="Conversation Feed">
        {messages.length === 0 ? (
          <div className="qw-chat-empty-state">
            <div className="qw-empty-brand-icon">
              <Sparkles size={28} />
            </div>
            <h3 className="qw-empty-headline">How can I help you today?</h3>
            <p className="qw-empty-subtext">
              Type any question below. EvidenRoute will evaluate context relevance, score evidence,
              and return the verified backend answer.
            </p>

            <div className="qw-empty-prompt-chips">
              {STARTER_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  className="qw-empty-prompt-chip"
                  onClick={() => handleSendMessage(prompt)}
                >
                  <span>{prompt}</span>
                  <ArrowRight size={14} className="qw-empty-prompt-chip-icon" />
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div key={msg.id} className={`qw-message-row ${msg.role}`}>
              <div className={`qw-message-avatar ${msg.role}`}>
                {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
              </div>

              <div
                className={`qw-message-bubble ${
                  msg.outcome === 'ABSTAIN' ? 'abstain' : ''
                } ${msg.isError ? 'error' : ''}`}
              >
                <p className="qw-message-text">{msg.content}</p>

                {/* Actual Citations Returned by Backend */}
                {msg.citations && msg.citations.length > 0 && (
                  <div className="qw-citations-container">
                    <span className="qw-citations-label">
                      <BookOpen size={12} />
                      Citations
                    </span>
                    <div className="qw-citations-list">
                      {msg.citations.map((cite) => (
                        <span
                          key={cite.id}
                          className="qw-citation-chip"
                          title={cite.sourceName ? `Source: ${cite.sourceName}` : undefined}
                        >
                          {cite.title}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <span className="qw-message-timestamp">{msg.timestamp}</span>
              </div>
            </div>
          ))
        )}

        {/* Loading Indicator */}
        {isLoading && (
          <div className="qw-message-row assistant">
            <div className="qw-message-avatar assistant">
              <Bot size={16} />
            </div>
            <div className="qw-message-bubble">
              <div className="qw-typing-indicator" aria-label="EvidenRoute is generating answer">
                <span className="qw-typing-dot" />
                <span className="qw-typing-dot" />
                <span className="qw-typing-dot" />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 3. Message Input at Bottom */}
      <footer className="qw-chat-input-bar">
        <form
          className="qw-chat-form"
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
        >
          <textarea
            ref={textareaRef}
            className="qw-chat-textarea"
            placeholder="Ask a question about deployments, APIs, policies, or database issues..."
            rows={1}
            value={inputValue}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
          />
          <button
            type="submit"
            className="qw-send-btn"
            disabled={!inputValue.trim() || isLoading}
            aria-label="Send message"
            title="Send message"
          >
            <Send size={16} />
          </button>
        </form>
        <p className="qw-input-helper-text">
          Press Enter to send, Shift + Enter for a new line. Answers are verified from local knowledge.
        </p>
      </footer>
    </div>
  );
};

export default QueryWorkspacePage;
