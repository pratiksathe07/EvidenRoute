import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  AlertTriangle,
  RotateCcw,
  ChevronDown,
  ChevronUp,
  FileText,
  User,
  Bot,
  Info,
  CheckCircle2,
  Sparkles,
} from 'lucide-react';
import {
  sendChatMessage,
  ChatMessage,
} from '../services/queryWorkspaceService';
import './QueryWorkspacePage.css';

const SUGGESTED_QUESTIONS = [
  'Why did the payment API fail after deployment?',
  'What was decided in the product planning meeting?',
  'What is the employee leave policy for parental leave?',
  'How do I resolve database connection timeout issues?',
];

export const QueryWorkspacePage: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [expandedEvidenceId, setExpandedEvidenceId] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSend = async (questionToSend?: string) => {
    const q = (questionToSend || inputText).trim();
    if (!q || isLoading) return;

    setErrorMessage(null);
    setInputText('');

    // Add user message to conversation thread
    const userMsg: ChatMessage = {
      id: `usr_${Date.now()}`,
      sender: 'user',
      text: q,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const res = await sendChatMessage(q);
      const newMsg = res.data?.message;
      if (res.isAvailable && newMsg) {
        setMessages((prev) => [...prev, newMsg]);
      } else {
        const errorMsg: ChatMessage = {
          id: `err_${Date.now()}`,
          sender: 'assistant',
          text: res.error || 'Sorry, I was unable to connect to the EvidenRoute engine. Please ensure the backend server is active.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          outcome: 'ABSTAIN',
          isInsufficient: true,
          insufficientReason: 'Backend connectivity error.',
        };
        setMessages((prev) => [...prev, errorMsg]);
      }
    } catch {
      setErrorMessage('A network communication error occurred. Please try again.');
    } finally {
      setIsLoading(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleClearChat = () => {
    setMessages([]);
    setErrorMessage(null);
    setInputText('');
  };

  const toggleEvidenceDrawer = (msgId: string) => {
    setExpandedEvidenceId((prev) => (prev === msgId ? null : msgId));
  };

  return (
    <div className="qw-chatbot-container">
      {/* Top action bar (only shown during active conversation to reset) */}
      {messages.length > 0 && (
        <div className="qw-top-bar">
          <button
            type="button"
            className="qw-reset-btn"
            onClick={handleClearChat}
            title="Start new conversation"
          >
            <RotateCcw size={13} />
            <span>New Chat</span>
          </button>
        </div>
      )}

      {/* Messages Conversation Thread */}
      <div className="qw-chat-thread">
        {messages.length === 0 ? (
          <div className="qw-empty-state">
            <div className="qw-empty-icon-wrap">
              <Bot size={28} />
            </div>
            <h2 className="qw-empty-title">How can EvidenRoute help you verify today?</h2>
            <p className="qw-empty-subtitle">
              Ask a question to intelligently select resources, evaluate evidence, and receive explainable answers.
            </p>

            {/* Suggested questions displayed only when no active conversation */}
            <div className="qw-suggestions-container">
              <span className="qw-suggestions-label">Suggested Questions</span>
              <div className="qw-suggestions-grid">
                {SUGGESTED_QUESTIONS.map((suggestion, idx) => (
                  <button
                    key={idx}
                    type="button"
                    className="qw-suggestion-card"
                    onClick={() => handleSend(suggestion)}
                  >
                    <Sparkles size={14} className="qw-suggestion-icon" />
                    <span className="qw-suggestion-text">{suggestion}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`qw-message-row ${msg.sender === 'user' ? 'user-row' : 'bot-row'}`}
            >
              <div className={`qw-avatar ${msg.sender}`}>
                {msg.sender === 'user' ? <User size={15} /> : <Bot size={15} />}
              </div>

              <div className="qw-message-content">
                <div className="qw-message-header">
                  <span className="qw-sender-name">
                    {msg.sender === 'user' ? 'You' : 'EvidenRoute'}
                  </span>
                  <span className="qw-timestamp">{msg.timestamp}</span>
                </div>

                {/* Insufficient Evidence Warning Banner */}
                {msg.isInsufficient && (
                  <div className="qw-insufficient-banner">
                    <AlertTriangle size={15} className="text-warning" />
                    <div>
                      <div className="qw-insufficient-title">Unable to provide a reliable answer</div>
                      <div className="qw-insufficient-desc">
                        {msg.insufficientReason || 'Not enough verified information was found in the connected resources to answer this question with confidence.'}
                      </div>
                    </div>
                  </div>
                )}

                {/* Assistant / User Message Body */}
                <div className="qw-message-bubble">
                  <div className="qw-message-text">{msg.text}</div>

                  {/* Supporting Grounding Explanations & Citations */}
                  {msg.sender === 'assistant' && !msg.isInsufficient && (
                    <div className="qw-grounding-section">
                      {msg.groundingExplanation && (
                        <div className="qw-trust-pill">
                          <CheckCircle2 size={13} className="text-emerald" />
                          <span>{msg.groundingExplanation}</span>
                        </div>
                      )}

                      {/* Supporting Citations */}
                      {msg.citations && msg.citations.length > 0 && (
                        <div className="qw-citations-row">
                          <span className="qw-citations-label">Sources Cited:</span>
                          {msg.citations.map((cite, cIdx) => (
                            <span
                              key={cIdx}
                              className="qw-citation-chip"
                              title={`Authority: ${cite.authorityPercent}% • ${cite.excerpt}`}
                            >
                              <FileText size={12} />
                              <span>{cite.sourceName}</span>
                            </span>
                          ))}
                        </div>
                      )}

                      {/* Expandable Evidence Passages Toggle */}
                      {msg.evidenceItems && msg.evidenceItems.length > 0 && (
                        <div className="qw-evidence-toggle-area">
                          <button
                            type="button"
                            className="qw-evidence-toggle-btn"
                            onClick={() => toggleEvidenceDrawer(msg.id)}
                          >
                            <span>
                              {expandedEvidenceId === msg.id
                                ? 'Hide Supporting Evidence'
                                : `View ${msg.evidenceItems.length} Supporting Evidence Passages`}
                            </span>
                            {expandedEvidenceId === msg.id ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
                          </button>

                          {expandedEvidenceId === msg.id && (
                            <div className="qw-evidence-drawer">
                              {msg.evidenceItems.map((item) => (
                                <div key={item.id} className="qw-evidence-card">
                                  <div className="qw-evidence-card-top">
                                    <span className="qw-evidence-source-name">{item.sourceName}</span>
                                    <span className="qw-evidence-category-badge">{item.category}</span>
                                  </div>
                                  <div className="qw-evidence-passage-text">
                                    &ldquo;{item.content}&rdquo;
                                  </div>
                                  <div className="qw-evidence-why">
                                    <Info size={12} />
                                    <span>{item.whyRetrieved}</span>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
        )}

        {/* Loading Indicator */}
        {isLoading && (
          <div className="qw-message-row bot-row">
            <div className="qw-avatar assistant">
              <Bot size={15} />
            </div>
            <div className="qw-message-content">
              <div className="qw-loading-bubble">
                <span className="qw-loading-dot" />
                <span className="qw-loading-dot" />
                <span className="qw-loading-dot" />
                <span className="qw-loading-text">Selecting resources & verifying evidence...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Error Banner if any */}
      {errorMessage && (
        <div className="qw-error-banner">
          <AlertTriangle size={15} />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Fixed / Sticky Bottom Composer */}
      <footer className="qw-composer-footer">
        <div className="qw-composer-container">
          <textarea
            ref={inputRef}
            className="qw-textarea"
            placeholder="Ask a question or follow-up (e.g. 'Why did the payment API fail?')..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
            disabled={isLoading}
          />
          <button
            type="button"
            className="qw-send-btn"
            onClick={() => handleSend()}
            disabled={!inputText.trim() || isLoading}
            aria-label="Send question"
          >
            <Send size={15} />
          </button>
        </div>
        <div className="qw-composer-hint">
          Press <strong>Enter</strong> to send • <strong>Shift + Enter</strong> for a new line • Grounded in verified evidence
        </div>
      </footer>
    </div>
  );
};

export default QueryWorkspacePage;
