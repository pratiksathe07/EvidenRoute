import React, { useState, useEffect, useCallback } from 'react';
import {
  Settings,
  Sparkles,
  Sliders,
  Database,
  Plug,
  CheckCircle2,
  AlertCircle,
  Eye,
  EyeOff,
  Check,
  ShieldCheck,
  RefreshCw,
} from 'lucide-react';
import {
  fetchSystemSettings,
  testGeminiConnection,
  saveGeminiSettings,
  toggleSourceAvailability,
  SettingsPayload,
  GeminiTestResult,
} from '../services/settingsService';
import { getAvailableSources } from '../services/sourceSelectionService';
import { SourceMetadata } from '../types/sourceSelection';
import './SettingsPage.css';

export const SettingsPage: React.FC = () => {
  const [settings, setSettings] = useState<SettingsPayload | null>(null);
  const [sources, setSources] = useState<SourceMetadata[]>([]);
  const [apiKeyInput, setApiKeyInput] = useState<string>('');
  const [showApiKey, setShowApiKey] = useState<boolean>(false);
  const [selectedModel, setSelectedModel] = useState<string>('gemini-1.5-flash');
  const [aiEnabled, setAiEnabled] = useState<boolean>(false);

  // General settings state
  const [searchDepth, setSearchDepth] = useState<string>('balanced');
  const [autoExpandCitations, setAutoExpandCitations] = useState<boolean>(true);
  const [themePreference, setThemePreference] = useState<string>('dark');

  // Status feedback
  const [testResult, setTestResult] = useState<GeminiTestResult | null>(null);
  const [isTesting, setIsTesting] = useState<boolean>(false);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    const [settingsRes, sourcesRes] = await Promise.all([
      fetchSystemSettings(),
      getAvailableSources(),
    ]);

    if (settingsRes.data) {
      setSettings(settingsRes.data);
      setSelectedModel(settingsRes.data.ai_provider.active_model);
      setAiEnabled(settingsRes.data.ai_provider.ai_generation_enabled);
      setSearchDepth(settingsRes.data.general.default_search_depth);
      setAutoExpandCitations(settingsRes.data.general.auto_expand_citations);
      setThemePreference(settingsRes.data.general.theme);
    }

    if (sourcesRes.data) {
      setSources(sourcesRes.data);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Handle Testing Gemini Key
  const handleTestGemini = async () => {
    setIsTesting(true);
    setTestResult(null);
    setSaveSuccessMsg(null);

    const res = await testGeminiConnection(apiKeyInput || undefined, selectedModel);
    if (res.data) {
      setTestResult(res.data);
    } else {
      setTestResult({
        success: false,
        message: res.error || 'Connection probe failed.',
      });
    }
    setIsTesting(false);
  };

  // Handle Saving Gemini Settings
  const handleSaveGemini = async () => {
    setIsSaving(true);
    setSaveSuccessMsg(null);

    const res = await saveGeminiSettings(
      apiKeyInput.trim() || undefined,
      selectedModel,
      aiEnabled
    );

    if (res.isAvailable) {
      setSaveSuccessMsg('AI Provider settings saved successfully.');
      setApiKeyInput(''); // Clear input for security
      loadData();
    }
    setIsSaving(false);
  };

  // Handle Source Toggle
  const handleToggleSource = async (sourceId: string) => {
    const res = await toggleSourceAvailability(sourceId);
    if (res.isAvailable) {
      const updated = await getAvailableSources();
      if (updated.data) {
        setSources(updated.data);
      }
    }
  };

  return (
    <div className="set-container">
      {/* 1. Header */}
      <header className="set-header">
        <div className="set-header-content">
          <div className="set-badge-row">
            <span className="set-badge">
              <Settings size={13} />
              <span>System & Provider Configuration</span>
            </span>
          </div>
          <h1 className="set-title">Settings</h1>
          <p className="set-subtitle">
            Configure application preferences, AI model routing, resource availability, and external service adapters.
          </p>
        </div>
      </header>

      {/* 2. AI Provider Settings (Google Gemini) */}
      <section className="set-section">
        <div className="set-section-header">
          <div className="set-section-title-wrap">
            <Sparkles size={16} className="text-blue" />
            <h2 className="set-section-title">AI Provider Settings</h2>
          </div>
          <span className="set-section-desc">Google Gemini Answer Generation</span>
        </div>

        <div className="set-card">
          {/* Status banner */}
          <div className="set-provider-status-row">
            <div>
              <div className="set-provider-name">Google Gemini</div>
              <div className="set-provider-desc">
                {settings?.ai_provider.description}
              </div>
            </div>
            <div className={`set-status-badge ${settings?.ai_provider.is_configured ? 'configured' : 'offline'}`}>
              <span className={`status-indicator-dot ${settings?.ai_provider.is_configured ? 'pulse' : ''}`} />
              <span>{settings?.ai_provider.status_label}</span>
            </div>
          </div>

          {/* Configuration Form */}
          <div className="set-form-grid">
            <div className="set-form-group">
              <label className="set-label">Gemini API Key</label>
              <div className="set-input-password-wrap">
                <input
                  type={showApiKey ? 'text' : 'password'}
                  className="set-input"
                  placeholder={
                    settings?.ai_provider.is_configured
                      ? '•••••••••••••••••••••••••••••••••••• (Configured)'
                      : 'Enter Google Gemini API Key (starts with AIza...)'
                  }
                  value={apiKeyInput}
                  onChange={(e) => setApiKeyInput(e.target.value)}
                  autoComplete="off"
                />
                <button
                  type="button"
                  className="set-show-btn"
                  onClick={() => setShowApiKey(!showApiKey)}
                  title={showApiKey ? 'Hide' : 'Show'}
                >
                  {showApiKey ? <EyeOff size={14} /> : <Eye size={14} />}
                </button>
              </div>
              <span className="set-hint">
                <ShieldCheck size={12} className="text-emerald" />
                <span>Keys are stored in memory and never echoed in API responses.</span>
              </span>
            </div>

            <div className="set-form-group">
              <label className="set-label">Model Selection</label>
              <select
                className="set-select"
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
              >
                {settings?.ai_provider.supported_models.map((m) => (
                  <option key={m} value={m}>
                    {m} (Google DeepMind)
                  </option>
                ))}
              </select>
              <span className="set-hint">Choose between high-speed Flash or deep-reasoning Pro models.</span>
            </div>

            <div className="set-form-group full-width">
              <label className="set-toggle-label">
                <input
                  type="checkbox"
                  className="set-checkbox"
                  checked={aiEnabled}
                  onChange={(e) => setAiEnabled(e.target.checked)}
                />
                <span className="set-toggle-text">
                  <strong>Enable Live AI Generation</strong> — when enabled with an active key, answers are synthesized by Gemini grounded in retrieved citations.
                </span>
              </label>
            </div>
          </div>

          {/* Test & Save Actions */}
          <div className="set-actions-row">
            <div className="set-actions-left">
              <button
                type="button"
                className="set-btn secondary"
                onClick={handleTestGemini}
                disabled={isTesting}
              >
                <RefreshCw size={13} className={isTesting ? 'spin' : ''} />
                <span>{isTesting ? 'Testing Connection...' : 'Test Connection'}</span>
              </button>

              <button
                type="button"
                className="set-btn primary"
                onClick={handleSaveGemini}
                disabled={isSaving}
              >
                <Check size={13} />
                <span>{isSaving ? 'Saving...' : 'Save AI Settings'}</span>
              </button>
            </div>

            {saveSuccessMsg && (
              <span className="set-success-msg">
                <CheckCircle2 size={13} />
                <span>{saveSuccessMsg}</span>
              </span>
            )}
          </div>

          {/* Connection Test Output */}
          {testResult && (
            <div className={`set-test-banner ${testResult.success ? 'success' : 'failed'}`}>
              {testResult.success ? <CheckCircle2 size={14} /> : <AlertCircle size={14} />}
              <span>{testResult.message}</span>
            </div>
          )}
        </div>
      </section>

      {/* 3. Resource Settings (Enable/Disable Connections) */}
      <section className="set-section">
        <div className="set-section-header">
          <div className="set-section-title-wrap">
            <Database size={16} className="text-emerald" />
            <h2 className="set-section-title">Resource Settings</h2>
          </div>
          <span className="set-section-desc">Manage Grounding Knowledge Sources</span>
        </div>

        <div className="set-card">
          <div className="set-sources-list">
            {sources.map((src) => {
              const isEnabled = src.availability === 'online' || src.availability === 'healthy';
              return (
                <div key={src.source_id} className="set-source-row">
                  <div className="set-source-left">
                    <div className="set-source-name-wrap">
                      <span className="set-source-name">{src.source_name || src.name}</span>
                      <span className="set-source-cat">{src.source_type}</span>
                    </div>
                    <p className="set-source-desc">{src.description}</p>
                    <div className="set-source-meta">
                      <span>Trust Level: {Math.round(Number(src.authority_level ?? 0.8) * 100)}%</span>
                      <span>•</span>
                      <span>Records: {src.record_count ?? 'Indexed'}</span>
                    </div>
                  </div>

                  <div className="set-source-right">
                    <button
                      type="button"
                      className={`set-toggle-btn ${isEnabled ? 'active' : 'inactive'}`}
                      onClick={() => handleToggleSource(src.source_id)}
                    >
                      <span>{isEnabled ? 'Enabled' : 'Disabled'}</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* 4. General Preferences */}
      <section className="set-section">
        <div className="set-section-header">
          <div className="set-section-title-wrap">
            <Sliders size={16} className="text-orange" />
            <h2 className="set-section-title">General Preferences</h2>
          </div>
          <span className="set-section-desc">Response Behavior & Appearance</span>
        </div>

        <div className="set-card">
          <div className="set-form-grid">
            <div className="set-form-group">
              <label className="set-label">Default Search Depth</label>
              <select
                className="set-select"
                value={searchDepth}
                onChange={(e) => setSearchDepth(e.target.value)}
              >
                <option value="quick">Quick (Top 3 candidates)</option>
                <option value="balanced">Balanced (Top 5 candidates - Recommended)</option>
                <option value="exhaustive">Exhaustive (Top 10 candidates)</option>
              </select>
            </div>

            <div className="set-form-group">
              <label className="set-label">Application Theme</label>
              <select
                className="set-select"
                value={themePreference}
                onChange={(e) => setThemePreference(e.target.value)}
              >
                <option value="dark">Dark Theme (Default)</option>
                <option value="slate">Slate Modern</option>
              </select>
            </div>

            <div className="set-form-group full-width">
              <label className="set-toggle-label">
                <input
                  type="checkbox"
                  className="set-checkbox"
                  checked={autoExpandCitations}
                  onChange={(e) => setAutoExpandCitations(e.target.checked)}
                />
                <span className="set-toggle-text">
                  Auto-expand verified citation previews in chatbot answers
                </span>
              </label>
            </div>
          </div>
        </div>
      </section>

      {/* 5. External Integrations & Adapters */}
      <section className="set-section">
        <div className="set-section-header">
          <div className="set-section-title-wrap">
            <Plug size={16} className="text-purple" />
            <h2 className="set-section-title">External Integrations & Adapters</h2>
          </div>
          <span className="set-section-desc">Supported Service Adapters</span>
        </div>

        <div className="set-card">
          <div className="set-integrations-grid">
            {settings?.integrations.map((conn) => (
              <div key={conn.id} className="set-conn-card">
                <div className="set-conn-top">
                  <div>
                    <h3 className="set-conn-name">{conn.name}</h3>
                    <span className="set-conn-category">{conn.category}</span>
                  </div>
                  <span className={`set-conn-status ${conn.status}`}>
                    {conn.status === 'connected' ? 'Connected' : conn.status === 'standby' ? 'Ready' : 'Offline'}
                  </span>
                </div>
                <p className="set-conn-desc">{conn.description}</p>
                <div className="set-conn-footer">
                  <span className="set-conn-adapter-tag">Adapter: {conn.id}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
};

export default SettingsPage;
