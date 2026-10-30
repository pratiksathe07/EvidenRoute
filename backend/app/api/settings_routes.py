"""
EvidenRoute - Settings and Integration Management Routes
Secure endpoints for AI provider configuration, Gemini testing, and system preferences.
Never echoes or logs raw API keys.
"""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

try:
    from backend.app.core.config import settings
except ImportError:
    from ..core.config import settings

logger = logging.getLogger("evidenroute.settings")

router = APIRouter(prefix="/api/settings", tags=["settings"])

# In-memory runtime settings state (with safe defaults)
_runtime_settings = {
    "default_search_depth": "balanced",
    "auto_expand_citations": True,
    "show_confidence_scores": True,
    "theme": "dark",
    "active_model": "gemini-1.5-flash",
    "ai_generation_enabled": bool(settings.GEMINI_API_KEY and settings.LLM_PROVIDER != "none"),
}


class GeminiTestRequest(BaseModel):
    api_key: Optional[str] = Field(None, description="Optional key to test before saving")
    model: Optional[str] = Field("gemini-1.5-flash", description="Model name to probe")


class GeminiConfigRequest(BaseModel):
    api_key: Optional[str] = Field(None, description="New Gemini API key to save")
    model: Optional[str] = Field(None, description="Default model selection")
    ai_generation_enabled: Optional[bool] = Field(None, description="Toggle AI answer synthesis")


class GeneralSettingsRequest(BaseModel):
    default_search_depth: Optional[str] = None
    auto_expand_citations: Optional[bool] = None
    show_confidence_scores: Optional[bool] = None
    theme: Optional[str] = None


@router.get("", summary="Get System Settings")
def get_settings() -> Dict[str, Any]:
    """
    Returns non-sensitive system settings, AI provider status, and available connectors.
    """
    is_gemini_active = bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip())
    
    return {
        "ai_provider": {
            "provider": "Google Gemini",
            "is_configured": is_gemini_active,
            "active_model": _runtime_settings["active_model"],
            "supported_models": [
                "gemini-1.5-flash",
                "gemini-1.5-pro",
                "gemini-2.0-flash",
            ],
            "ai_generation_enabled": _runtime_settings["ai_generation_enabled"] and is_gemini_active,
            "status_label": (
                "Connected (Live Gemini Generation)"
                if is_gemini_active and _runtime_settings["ai_generation_enabled"]
                else "Offline Grounding Mode (Deterministic Synthesis)"
            ),
            "description": (
                "Google Gemini synthesizes conversational answers strictly grounded in retrieved evidence."
                if is_gemini_active
                else "Operating in local deterministic grounding mode. Provide an API key to enable live Gemini answers."
            ),
        },
        "general": {
            "default_search_depth": _runtime_settings["default_search_depth"],
            "auto_expand_citations": _runtime_settings["auto_expand_citations"],
            "show_confidence_scores": _runtime_settings["show_confidence_scores"],
            "theme": _runtime_settings["theme"],
        },
        "resource_categories": [
            {"id": "documents", "name": "Official Documentation", "description": "Technical specifications, API guides, and company handbooks"},
            {"id": "tickets", "name": "Bug Reports & Tickets", "description": "Customer issues, Jira tickets, and incident reports"},
            {"id": "conversations", "name": "Team Conversations", "description": "War room chats and decision discussions"},
        ],
        "integrations": [
            {
                "id": "sqlite_local",
                "name": "SQLite Knowledge Store",
                "category": "Database",
                "status": "connected",
                "is_enabled": True,
                "description": "Embedded local evidence database storing verified documentation and tickets.",
            },
            {
                "id": "postgres_pgvector",
                "name": "PostgreSQL & pgvector",
                "category": "Database",
                "status": "standby",
                "is_enabled": False,
                "description": "Enterprise vector and relational store adapter for high-scale retrieval.",
            },
            {
                "id": "jira_bug_tracker",
                "name": "Jira Bug Tracker Connector",
                "category": "Ticketing",
                "status": "connected",
                "is_enabled": True,
                "description": "Indexes bug resolutions, error traces, and deployment fixes.",
            },
            {
                "id": "slack_war_room",
                "name": "Incident War Room Connector",
                "category": "Communications",
                "status": "connected",
                "is_enabled": True,
                "description": "Indexes live troubleshooting threads and post-deployment updates.",
            },
            {
                "id": "github_docs",
                "name": "GitHub Specs Connector",
                "category": "Documentation",
                "status": "connected",
                "is_enabled": True,
                "description": "Synchronizes markdown specifications directly from code repositories.",
            },
        ],
    }


@router.post("/test-gemini", summary="Test Gemini Connection")
def test_gemini_connection(payload: GeminiTestRequest) -> Dict[str, Any]:
    """
    Tests connection to Google Gemini using either the submitted key or the currently configured key.
    Never returns or logs the raw API key.
    """
    test_key = payload.api_key.strip() if payload.api_key else settings.GEMINI_API_KEY
    if not test_key:
        return {
            "success": False,
            "message": "No API key provided or currently configured in environment.",
        }

    try:
        import google.generativeai as genai
        genai.configure(api_key=test_key)
        # Test generation with minimal prompt
        model_name = payload.model or _runtime_settings["active_model"]
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Ping")
        
        return {
            "success": True,
            "model": model_name,
            "message": f"Successfully verified connection to Google Gemini ({model_name}).",
        }
    except Exception as e:
        err_msg = str(e)
        logger.warning(f"Gemini connection test failed: {err_msg}")
        return {
            "success": False,
            "message": f"Connection test failed: {err_msg}",
        }


@router.post("/gemini", summary="Save Gemini Settings")
def save_gemini_settings(payload: GeminiConfigRequest) -> Dict[str, Any]:
    """
    Saves Gemini configuration in memory and updates runtime provider status.
    """
    if payload.api_key is not None:
        cleaned_key = payload.api_key.strip()
        settings.GEMINI_API_KEY = cleaned_key
        if cleaned_key:
            settings.LLM_PROVIDER = "gemini"
        else:
            settings.LLM_PROVIDER = "none"

    if payload.model:
        _runtime_settings["active_model"] = payload.model

    if payload.ai_generation_enabled is not None:
        _runtime_settings["ai_generation_enabled"] = payload.ai_generation_enabled

    is_configured = bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip())
    
    return {
        "status": "success",
        "is_configured": is_configured,
        "active_model": _runtime_settings["active_model"],
        "ai_generation_enabled": _runtime_settings["ai_generation_enabled"] and is_configured,
        "message": "AI Provider settings updated successfully.",
    }


@router.post("/general", summary="Save General Settings")
def save_general_settings(payload: GeneralSettingsRequest) -> Dict[str, Any]:
    """
    Updates general system preferences.
    """
    if payload.default_search_depth:
        _runtime_settings["default_search_depth"] = payload.default_search_depth
    if payload.auto_expand_citations is not None:
        _runtime_settings["auto_expand_citations"] = payload.auto_expand_citations
    if payload.show_confidence_scores is not None:
        _runtime_settings["show_confidence_scores"] = payload.show_confidence_scores
    if payload.theme:
        _runtime_settings["theme"] = payload.theme

    return {
        "status": "success",
        "general": _runtime_settings,
        "message": "Preferences saved successfully.",
    }

