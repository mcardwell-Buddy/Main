"""
Artifact Preview Generator

Deterministic previews for artifacts (no execution, no LLM).
"""

from __future__ import annotations

from typing import Dict, Any, List


class ArtifactPreviewGenerator:
    """Generate lightweight previews for artifacts."""

    def generate_preview(self, artifact: Dict[str, Any]) -> Dict[str, Any]:
        """Generate preview based on artifact type."""
        artifact_type = artifact.get("artifact_type") or "unknown"
        handler = {
            "web_extraction_result": self._preview_web_extraction,
            "web_search_result": self._preview_web_search,
            "web_navigation_result": self._preview_web_navigation,
            "calculation_result": self._preview_calculation,
        }.get(artifact_type, self._preview_generic)

        return handler(artifact)

    def _preview_web_extraction(self, artifact: Dict[str, Any]) -> Dict[str, Any]:
        extracted = artifact.get("extracted_data", {}) if isinstance(artifact.get("extracted_data"), dict) else {}
        sections = extracted.get("sections") if isinstance(extracted.get("sections"), list) else []
        summary = extracted.get("summary") or extracted.get("title") or "Extraction complete"
        items_preview: List[Dict[str, Any]] = []

        if sections:
            items_preview = [
                {
                    "title": s.get("title") or "Section",
                    "text": (s.get("text") or "")[:200],
                }
                for s in sections[:3]
            ]

        return {
            "type": "web_extraction",
            "summary": summary[:300],
            "section_count": len(sections),
            "items_preview": items_preview,
        }

    def _preview_web_search(self, artifact: Dict[str, Any]) -> Dict[str, Any]:
        results = artifact.get("results") if isinstance(artifact.get("results"), list) else []
        preview = []
        for item in results[:3]:
            if isinstance(item, dict):
                preview.append({
                    "title": item.get("title") or item.get("name"),
                    "url": item.get("url") or item.get("link"),
                    "snippet": (item.get("snippet") or "")[:200],
                })
            else:
                preview.append({"value": str(item)[:200]})
        return {
            "type": "web_search",
            "summary": f"{len(results)} results",
            "items_preview": preview,
        }

    def _preview_web_navigation(self, artifact: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "web_navigation",
            "summary": artifact.get("page_title") or "Navigation complete",
            "final_url": artifact.get("final_url") or artifact.get("starting_url"),
        }

    def _preview_calculation(self, artifact: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "calculation",
            "summary": f"{artifact.get('expression', 'expression')} = {artifact.get('result', 'N/A')}",
        }

    def _preview_generic(self, artifact: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "generic",
            "summary": artifact.get("artifact_type") or "artifact",
        }
