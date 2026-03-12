"""
ahrefs_hook.py — Ahrefs integration stub for Kolo SEO Agent
=============================================================
Defines the interface now, returns empty data.  When the Ahrefs MCP
connector (UUID: 098cb32a-ba21-4770-97dd-78bb54655419) is connected,
implement the functions here.  No other module needs to change.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class AhrefsMetrics:
    domain: str
    dr: int = 0
    backlinks: int = 0
    referring_domains: int = 0
    organic_traffic: int = 0
    organic_keywords: int = 0
    traffic_value: float = 0.0


def is_available() -> bool:
    """Check if Ahrefs integration is available."""
    return False  # flip when MCP is connected


def get_domain_metrics(domain: str, api_key: Optional[str] = None) -> Optional[AhrefsMetrics]:
    """Get Ahrefs metrics for a domain.  Returns None if not available."""
    if not is_available():
        return None
    # TODO: implement via Ahrefs MCP
    return None


def get_backlink_profile(
    target_domain: str = "kolo.in",
    api_key: Optional[str] = None,
) -> list[dict]:
    """Get backlinks pointing to target domain."""
    if not is_available():
        return []
    # TODO: implement via Ahrefs MCP
    return []


def get_keyword_rankings(
    domain: str = "kolo.in",
    keywords: Optional[list[str]] = None,
    api_key: Optional[str] = None,
) -> dict[str, int]:
    """Get current rankings for keywords.  Returns {keyword: position}."""
    if not is_available():
        return {}
    # TODO: implement via Ahrefs MCP
    return {}


def enrich_publication_result(result) -> None:
    """Enrich a PublicationResult in-place with Ahrefs data.

    Called from monthly_cycle.evaluate_month() when available.
    """
    if not is_available():
        return
    # TODO: populate result.ahrefs_* fields
