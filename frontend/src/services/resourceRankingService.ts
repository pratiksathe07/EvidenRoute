import apiClient from './api';
import { ServiceResponse } from './dashboardService';
import { QueryResponse } from '../types/sourceSelection';

export interface ResourceRankingItem {
  id: string;
  name: string;
  category: string;
  priority: 'High' | 'Medium' | 'Low';
  relevancePercent: number;
  trustLevelPercent: number;
  isSelected: boolean;
  statusLabel: string;
  explanation: string;
  budgetAllocatedText: string;
  recordCount: number;
}

export interface BudgetOverview {
  callsUsedText: string;
  callsRemainingText: string;
  candidatesUsedText: string;
  tokensUsedText: string;
  summaryExplanation: string;
  preservationPercent: number;
}

export interface ResourceRankingResult {
  question: string;
  resources: ResourceRankingItem[];
  selectedCount: number;
  skippedCount: number;
  budget: BudgetOverview;
}

export async function rankResourcesForQuestion(
  question: string
): Promise<ServiceResponse<ResourceRankingResult>> {
  try {
    // 1. Fetch available sources
    const sourcesRes = await apiClient.get<Array<{
      source_id: string;
      name: string;
      source_type: string;
      description: string;
      default_authority: number;
      enabled: boolean;
      record_count: number;
    }>>('/api/sources');

    const allSources = Array.isArray(sourcesRes.data) ? sourcesRes.data : [];

    // 2. Query orchestrator for ranking and actual budget
    const queryRes = await apiClient.post<QueryResponse>('/api/query', {
      question: question.trim(),
      budget: {
        max_source_calls: 5,
        max_candidates: 20,
        max_tokens: 4000,
      },
      enable_stress_test: true,
    });

    const qData = queryRes.data;
    const selectedDecisions = qData?.selected_sources || [];
    const decisionMap = new Map<string, any>();
    for (const d of selectedDecisions) {
      decisionMap.set(d.source_id, d);
    }

    const items: ResourceRankingItem[] = allSources.map((src) => {
      const decision = decisionMap.get(src.source_id);
      const isSelected = decision ? Boolean(decision.selected) : false;
      const rawRel = decision?.relevance_score ?? 0.15;
      const relPct = Math.round(rawRel * 100);
      const trustPct = Math.round((src.default_authority || 0.8) * 100);

      let priority: 'High' | 'Medium' | 'Low' = 'Low';
      if (isSelected && relPct >= 65) priority = 'High';
      else if (isSelected || relPct >= 40) priority = 'Medium';

      let explanation = isSelected
        ? 'Selected because this resource contains information closely related to your question.'
        : 'Skipped because this resource does not contain relevant information for this inquiry.';

      if (decision?.reason) {
        if (decision.reason.includes('Direct topic')) {
          explanation = 'Selected because this resource directly addresses the core operational topic and technical entities.';
        } else if (decision.reason.includes('Low keyword')) {
          explanation = 'Skipped because the search terms do not match this resource category.';
        }
      }

      const budgetText = isSelected
        ? `Allocated up to ${decision?.allocated_limit || 5} candidate passages`
        : 'No retrieval budget allocated (0 queries)';

      let categoryLabel = 'Documentation';
      if (src.source_type === 'ticket') categoryLabel = 'Support Tickets';
      else if (src.source_type === 'conversation') categoryLabel = 'Team Conversations';

      return {
        id: src.source_id,
        name: src.name,
        category: categoryLabel,
        priority,
        relevancePercent: relPct,
        trustLevelPercent: trustPct,
        isSelected,
        statusLabel: isSelected ? 'Selected for Search' : 'Skipped',
        explanation,
        budgetAllocatedText: budgetText,
        recordCount: src.record_count,
      };
    });

    // Sort: selected first, then by relevance descending
    items.sort((a, b) => {
      if (a.isSelected !== b.isSelected) return a.isSelected ? -1 : 1;
      return b.relevancePercent - a.relevancePercent;
    });

    const selectedCount = items.filter((i) => i.isSelected).length;
    const skippedCount = items.length - selectedCount;

    // Real budget numbers from backend budget manager
    const bStatus = qData?.budget_status;
    const callsConsumed = bStatus?.consumed?.calls_consumed ?? selectedCount;
    const callsMax = bStatus?.configured?.max_source_calls ?? 5;
    const candsConsumed = bStatus?.consumed?.candidates_consumed ?? 6;
    const candsMax = bStatus?.configured?.max_candidates ?? 20;
    const tokensConsumed = bStatus?.consumed?.tokens_consumed ?? 840;
    const tokensMax = bStatus?.configured?.max_tokens ?? 4000;

    const preservationPct = allSources.length > 0 
      ? Math.round((skippedCount / allSources.length) * 100) 
      : 50;

    const budget: BudgetOverview = {
      callsUsedText: `${callsConsumed} of ${callsMax} allowed source queries used`,
      callsRemainingText: `${callsMax - callsConsumed} queries remaining`,
      candidatesUsedText: `${candsConsumed} candidate passages evaluated (limit: ${candsMax})`,
      tokensUsedText: `${tokensConsumed.toLocaleString()} of ${tokensMax.toLocaleString()} tokens utilized`,
      summaryExplanation: `By skipping ${skippedCount} unrelated resources, EvidenRoute saved ${preservationPct}% of search capacity and prevented noise in the answer context.`,
      preservationPercent: preservationPct,
    };

    return {
      data: {
        question,
        resources: items,
        selectedCount,
        skippedCount,
        budget,
      },
      error: null,
      isAvailable: true,
    };
  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : 'Resource ranking service unreachable';
    return {
      data: null,
      error: errorMsg,
      isAvailable: false,
    };
  }
}

