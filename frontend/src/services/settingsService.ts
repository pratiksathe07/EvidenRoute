import apiClient from './api';
import { ServiceResponse } from './dashboardService';

export interface AIProviderConfig {
  provider: string;
  is_configured: boolean;
  active_model: string;
  supported_models: string[];
  ai_generation_enabled: boolean;
  status_label: string;
  description: string;
}

export interface GeneralPreferences {
  default_search_depth: string;
  auto_expand_citations: boolean;
  show_confidence_scores: boolean;
  theme: string;
}

export interface ResourceCategoryInfo {
  id: string;
  name: string;
  description: string;
}

export interface IntegrationConnector {
  id: string;
  name: string;
  category: string;
  status: 'connected' | 'standby' | 'disconnected';
  is_enabled: boolean;
  description: string;
}

export interface SettingsPayload {
  ai_provider: AIProviderConfig;
  general: GeneralPreferences;
  resource_categories: ResourceCategoryInfo[];
  integrations: IntegrationConnector[];
}

export interface GeminiTestResult {
  success: boolean;
  message: string;
  model?: string;
}

export async function fetchSystemSettings(): Promise<ServiceResponse<SettingsPayload>> {
  try {
    const res = await apiClient.get<SettingsPayload>('/api/settings');
    return {
      data: res.data,
      error: null,
      isAvailable: true,
    };
  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : 'Settings endpoint unreachable';
    // Return honest fallback state
    return {
      data: {
        ai_provider: {
          provider: 'Google Gemini',
          is_configured: false,
          active_model: 'gemini-1.5-flash',
          supported_models: ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-2.0-flash'],
          ai_generation_enabled: false,
          status_label: 'Offline Grounding Mode (Deterministic Synthesis)',
          description: 'Operating in local deterministic grounding mode. Configure an API key to enable live Gemini answers.',
        },
        general: {
          default_search_depth: 'balanced',
          auto_expand_citations: true,
          show_confidence_scores: true,
          theme: 'dark',
        },
        resource_categories: [
          { id: 'documents', name: 'Official Documentation', description: 'Technical specifications, API guides, and company handbooks' },
          { id: 'tickets', name: 'Bug Reports & Tickets', description: 'Customer issues, Jira tickets, and incident reports' },
          { id: 'conversations', name: 'Team Conversations', description: 'War room chats and decision discussions' },
        ],
        integrations: [
          { id: 'sqlite_local', name: 'SQLite Knowledge Store', category: 'Database', status: 'connected', is_enabled: true, description: 'Embedded local evidence database storing verified documentation and tickets.' },
          { id: 'postgres_pgvector', name: 'PostgreSQL & pgvector', category: 'Database', status: 'standby', is_enabled: false, description: 'Enterprise vector and relational store adapter for high-scale retrieval.' },
          { id: 'jira_bug_tracker', name: 'Jira Bug Tracker Connector', category: 'Ticketing', status: 'connected', is_enabled: true, description: 'Indexes bug resolutions, error traces, and deployment fixes.' },
          { id: 'slack_war_room', name: 'Incident War Room Connector', category: 'Communications', status: 'connected', is_enabled: true, description: 'Indexes live troubleshooting threads and post-deployment updates.' },
          { id: 'github_docs', name: 'GitHub Specs Connector', category: 'Documentation', status: 'connected', is_enabled: true, description: 'Synchronizes markdown specifications directly from code repositories.' },
        ],
      },
      error: errorMsg,
      isAvailable: false,
    };
  }
}

export async function testGeminiConnection(
  apiKey?: string,
  model?: string
): Promise<ServiceResponse<GeminiTestResult>> {
  try {
    const res = await apiClient.post<GeminiTestResult>('/api/settings/test-gemini', {
      api_key: apiKey || null,
      model: model || 'gemini-1.5-flash',
    });
    return {
      data: res.data,
      error: null,
      isAvailable: true,
    };
  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : 'Connection test failed';
    return {
      data: { success: false, message: errorMsg },
      error: errorMsg,
      isAvailable: false,
    };
  }
}

export async function saveGeminiSettings(
  apiKey?: string,
  model?: string,
  enabled?: boolean
): Promise<ServiceResponse<{ status: string; message: string }>> {
  try {
    const res = await apiClient.post('/api/settings/gemini', {
      api_key: apiKey,
      model,
      ai_generation_enabled: enabled,
    });
    return {
      data: res.data,
      error: null,
      isAvailable: true,
    };
  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : 'Failed to save provider settings';
    return {
      data: null,
      error: errorMsg,
      isAvailable: false,
    };
  }
}

export async function toggleSourceAvailability(
  sourceId: string
): Promise<ServiceResponse<{ source_id: string; enabled: boolean; status: string }>> {
  try {
    const res = await apiClient.patch(`/api/sources/${encodeURIComponent(sourceId)}/toggle`);
    return {
      data: res.data,
      error: null,
      isAvailable: true,
    };
  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : `Failed to toggle source ${sourceId}`;
    return {
      data: null,
      error: errorMsg,
      isAvailable: false,
    };
  }
}

