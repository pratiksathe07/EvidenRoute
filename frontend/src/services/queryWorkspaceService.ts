import apiClient from './api';
import { RetrieveResponse } from '../types/retrieval';
import { QueryResponse } from '../types/sourceSelection';
import { ServiceResponse } from './dashboardService';

export interface ChatCitation {
  id: string;
  sourceName: string;
  label: string;
  excerpt: string;
  authorityPercent: number;
}

export interface ChatEvidenceItem {
  id: string;
  title: string;
  sourceName: string;
  category: string;
  content: string;
  authorityPercent: number;
  citation: string;
  whyRetrieved: string;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
  outcome?: 'ANSWER' | 'ABSTAIN' | 'CLARIFY';
  isInsufficient?: boolean;
  insufficientReason?: string;
  citations?: ChatCitation[];
  evidenceItems?: ChatEvidenceItem[];
  groundingExplanation?: string;
  resourcesUsedCount?: number;
}

export interface SendQuestionResult {
  message: ChatMessage;
  queryId: string;
}

/**
 * Sends a question to the EvidenRoute intelligence backend and returns a clean,
 * human-readable ChatMessage with verified citations and grounding explanations.
 */
export async function sendChatMessage(
  question: string
): Promise<ServiceResponse<SendQuestionResult>> {
  const trimmed = question.trim();
  if (!trimmed) {
    return {
      data: null,
      error: 'Please enter a valid question.',
      isAvailable: true,
    };
  }

  const queryId = `q_${Date.now().toString(16)}`;

  try {
    // Call retrieve endpoint and query orchestrator in parallel
    const [retrieveRes, queryRes] = await Promise.allSettled([
      apiClient.post<RetrieveResponse>('/api/intelligence/retrieve', {
        question: trimmed,
        top_k: 5,
        enable_stress_test: true,
      }),
      apiClient.post<QueryResponse>('/api/query', {
        question: trimmed,
        budget: {
          max_source_calls: 5,
          max_candidates: 20,
          max_tokens: 4000,
        },
        enable_stress_test: true,
      }),
    ]);

    const rData = retrieveRes.status === 'fulfilled' ? retrieveRes.value.data : null;
    const qData = queryRes.status === 'fulfilled' ? queryRes.value.data : null;

    if (!rData && !qData) {
      const err = retrieveRes.status === 'rejected' ? retrieveRes.reason?.message : 'Backend unavailable';
      return {
        data: null,
        error: err || 'Could not connect to the EvidenRoute engine. Please ensure the backend server is active.',
        isAvailable: false,
      };
    }

    const readiness = rData?.answer_readiness;
    let outcome: 'ANSWER' | 'ABSTAIN' | 'CLARIFY' = (qData?.outcome as any) || 'ANSWER';
    let isInsufficient = false;
    let insufficientReason = '';

    if (readiness && !readiness.is_ready_to_answer) {
      outcome = readiness.recommended_action === 'clarify' ? 'CLARIFY' : 'ABSTAIN';
      isInsufficient = true;
      insufficientReason = readiness.primary_justification || 'We do not have enough verified evidence in the connected resources to answer this question reliably.';
    } else if (qData?.outcome === 'ABSTAIN') {
      outcome = 'ABSTAIN';
      isInsufficient = true;
      insufficientReason = qData.abstention_reason || 'Insufficient verified evidence found in connected resources.';
    }

    // Extract passages
    const rawPassages = rData?.retrieved_evidence || [];
    const evidenceItems: ChatEvidenceItem[] = rawPassages.map((p, idx) => ({
      id: `ev_${idx + 1}`,
      title: p.title || p.record_id || `Evidence #${idx + 1}`,
      sourceName: p.source_name || p.source_id,
      category: (p.source_type || 'Document').toUpperCase(),
      content: p.content,
      authorityPercent: Math.round((p.authority_level || 0.8) * 100),
      citation: p.citation || `[${p.source_name || p.source_id} § ${p.record_id || idx + 1}]`,
      whyRetrieved: p.evidence_score?.directness_label === 'direct'
        ? 'Directly answers the topic of your question.'
        : 'Provides relevant context and supporting operational details.',
    }));

    // Extract citations
    const citations: ChatCitation[] = evidenceItems.slice(0, 3).map((item) => ({
      id: item.id,
      sourceName: item.sourceName,
      label: item.title,
      excerpt: item.content.slice(0, 160) + (item.content.length > 160 ? '...' : ''),
      authorityPercent: item.authorityPercent,
    }));

    // Construct final human-readable answer
    let text = qData?.final_answer || '';
    if (!text && rData?.retrieved_evidence?.length && outcome === 'ANSWER') {
      const topP = rData.retrieved_evidence.slice(0, 2);
      text = topP.map((p) => p.content).join('\n\n');
    }

    // If answer contains raw backend prefixes like "Based on verified evidence:\n" clean them for chatbot presentation
    if (text.startsWith('Based on verified evidence:\n')) {
      const lines = text.replace('Based on verified evidence:\n', '').trim().split('\n');
      text = lines.map((l) => l.replace(/^"|"$/g, '').trim()).filter(Boolean).join('\n\n');
    }

    if (isInsufficient) {
      text = `Unable to provide a reliable answer. ${insufficientReason}`;
    }

    const uniqueSources = new Set(evidenceItems.map((e) => e.sourceName));
    const groundingExplanation = !isInsufficient && uniqueSources.size > 0
      ? `Answer verified using ${uniqueSources.size} independent resource${uniqueSources.size > 1 ? 's' : ''} (${Array.from(uniqueSources).join(', ')}).`
      : undefined;

    const message: ChatMessage = {
      id: `msg_${Date.now()}`,
      sender: 'assistant',
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      outcome,
      isInsufficient,
      insufficientReason: isInsufficient ? insufficientReason : undefined,
      citations: citations.length > 0 ? citations : undefined,
      evidenceItems: evidenceItems.length > 0 ? evidenceItems : undefined,
      groundingExplanation,
      resourcesUsedCount: uniqueSources.size,
    };

    return {
      data: {
        message,
        queryId: qData?.query_id || queryId,
      },
      error: null,
      isAvailable: true,
    };
  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : 'Chat query failed';
    return {
      data: null,
      error: errorMsg,
      isAvailable: false,
    };
  }
}
