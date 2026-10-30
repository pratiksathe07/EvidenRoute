"""
EvidenRoute - Intelligence Pipeline
Orchestrates the pre-retrieval context selection flow:
User Question -> Query Analyzer -> Source Registry -> Source Selector -> Decision Trace.
"""

import time
from typing import List, Optional
from .models import (
    PipelineDecisionTrace,
    QueryAnalysisResult,
    SelectionConfig,
    SelectionStatus,
    SourceMetadata,
    SourceRankResult,
)
from .query_analyzer import QueryAnalyzer
from .source_registry import BaseSourceRegistry, SourceRegistry
from .source_selector import SourceSelector


class IntelligencePipeline:
    """
    Coordinates query understanding and source ranking.
    Generates a full decision trace for explainability and downstream consumption.
    """

    def __init__(
        self,
        analyzer: Optional[QueryAnalyzer] = None,
        registry: Optional[BaseSourceRegistry] = None,
        selector: Optional[SourceSelector] = None,
    ):
        self.analyzer = analyzer or QueryAnalyzer()
        self.registry = registry or SourceRegistry
        self.selector = selector or SourceSelector()

    def run(
        self,
        question: str,
        config: Optional[SelectionConfig] = None,
        custom_sources: Optional[List[SourceMetadata]] = None,
    ) -> PipelineDecisionTrace:
        """
        Execute full context selection pipeline and produce an auditable decision trace.
        """
        start_time = time.perf_counter()

        # Step 1: Query Understanding
        analysis: QueryAnalysisResult = self.analyzer.analyze(question)

        # Step 2: Fetch Sources from Registry or custom input
        sources: List[SourceMetadata] = (
            custom_sources if custom_sources is not None else self.registry.list_sources()
        )
        total_available = len(sources)

        # Step 3: Source Ranking & Selection
        ranked_results: List[SourceRankResult] = self.selector.rank_and_select(
            analysis=analysis,
            sources=sources,
            config=config,
        )

        # Step 4: Aggregate Metrics & Trace
        selected_count = sum(
            1 for r in ranked_results if r.selection_status == SelectionStatus.SELECTED.value
        )
        skipped_count = len(ranked_results) - selected_count

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        notes: List[str] = [
            f"Evaluated {len(ranked_results)} sources using local-first scoring algorithm.",
            f"Query intent identified as '{analysis.intent}' with {analysis.confidence:.2f} confidence.",
        ]

        if selected_count == 0:
            notes.append(
                "No sources satisfied both the minimum relevance and final score selection thresholds."
            )

        return PipelineDecisionTrace(
            query=question,
            analysis=analysis,
            available_sources_count=total_available,
            evaluated_sources_count=len(ranked_results),
            selected_sources_count=selected_count,
            skipped_sources_count=skipped_count,
            ranked_sources=ranked_results,
            execution_time_ms=round(elapsed_ms, 2),
            config_used=config or self.selector.default_config,
            notes=notes,
        )
