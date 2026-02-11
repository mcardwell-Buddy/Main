"""
Artifact Preview Generator: Phase 7 - Expanded Rich Media Support

Generates deterministic, rich previews for artifacts including:
- HTML rendering hints for structured content
- Chart configurations for data visualization
- Code syntax highlighting metadata
- Image gallery previews
- Table rendering parameters
- Markdown formatting guidance

No execution, no LLM - pure data transformation.
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional
import re


class ArtifactPreviewGenerator:
    """Generate enhanced previews for artifacts with rich media support."""
    
    # PHASE 7: Expanded artifact type handlers
    ARTIFACT_HANDLERS = {
        "web_extraction_result": "_preview_web_extraction",
        "web_search_result": "_preview_web_search",
        "web_navigation_result": "_preview_web_navigation",
        "calculation_result": "_preview_calculation",
        "data_table": "_preview_data_table",
        "chart_data": "_preview_chart_data",
        "code_snippet": "_preview_code_snippet",
        "image_gallery": "_preview_image_gallery",
        "html_content": "_preview_html_content",
        "json_data": "_preview_json_data",
    }

    def generate_preview(self, artifact: Dict[str, Any]) -> Dict[str, Any]:
        """Generate preview based on artifact type."""
        artifact_type = artifact.get("artifact_type") or "unknown"
        handler_name = self.ARTIFACT_HANDLERS.get(artifact_type, "_preview_generic")
        handler = getattr(self, handler_name, self._preview_generic)
        return handler(artifact)

    def _preview_web_extraction(self, artifact: Dict[str, Any]) -> Dict[str, Any]:
        """PHASE 7: Enhanced extraction preview with HTML rendering."""
        extracted = artifact.get("extracted_data", {}) if isinstance(artifact.get("extracted_data"), dict) else {}
        sections = extracted.get("sections") if isinstance(extracted.get("sections"), list) else []
        summary = extracted.get("summary") or extracted.get("title") or "Extraction complete"
        items_preview: List[Dict[str, Any]] = []
        
        # PHASE 7: Generate HTML rendered sections
        html_sections: List[Dict[str, Any]] = []

        if sections:
            items_preview = [
                {
                    "title": s.get("title") or "Section",
                    "text": (s.get("text") or "")[:200],
                }
                for s in sections[:3]
            ]
            
            # Generate HTML for rich rendering
            for section in sections[:5]:
                html_sections.append({
                    "heading": section.get("title") or "Section",
                    "html": f"<div class='extraction-section'><h3>{self._escape_html(section.get('title', ''))}</h3><p>{self._escape_html(section.get('text', '')[:500])}</p></div>",
                    "markdown": f"### {section.get('title', '')}\n\n{section.get('text', '')[:500]}",
                })

        return {
            "type": "web_extraction",
            "summary": summary[:300],
            "section_count": len(sections),
            "items_preview": items_preview,
            # PHASE 7: Rich media expansion
            "html_sections": html_sections,
            "rendering_hint": "document",  # Hint for frontend
            "format": "markdown",  # Recommended format
            "supports_syntax_highlighting": False,
        }

    def _preview_web_search(self, artifact: Dict[str, Any]) -> Dict[str, Any]:
        """PHASE 7: Enhanced search preview with link metadata."""
        results = artifact.get("results") if isinstance(artifact.get("results"), list) else []
        preview = []
        
        # PHASE 7: Generate table rendering data
        table_rows: List[Dict[str, str]] = []
        
        for item in results[:10]:
            if isinstance(item, dict):
                preview_item = {
                    "title": item.get("title") or item.get("name") or "Result",
                    "url": item.get("url") or item.get("link") or "",
                    "snippet": (item.get("snippet") or "")[:200],
                }
                preview.append(preview_item)
                
                # For table rendering
                table_rows.append({
                    "title": preview_item["title"][:80],
                    "url": preview_item["url"][:100],
                    "snippet": preview_item["snippet"][:200],
                })
            else:
                preview.append({"value": str(item)[:200]})
        
        return {
            "type": "web_search",
            "summary": f"{len(results)} results found",
            "result_count": len(results),
            "items_preview": preview,
            # PHASE 7: Rich media expansion
            "table_data": {
                "headers": ["Title", "URL", "Snippet"],
                "rows": table_rows,
                "sortable": True,
                "filterable": True,
            },
            "rendering_hint": "table",
            "pagination_size": 10,
        }

    def _preview_web_navigation(self, artifact: Dict[str, Any]) -> Dict[str, Any]:
        """PHASE 7: Enhanced navigation preview with page snapshot."""
        page_title = artifact.get("page_title") or "Navigation complete"
        final_url = artifact.get("final_url") or artifact.get("starting_url") or ""
        page_content = artifact.get("page_content") or artifact.get("html") or ""
        
        # Extract snippet from page content
        snippet = self._extract_page_snippet(page_content)
        
        return {
            "type": "web_navigation",
            "summary": page_title,
            "final_url": final_url,
            # PHASE 7: Rich media expansion
            "page_title": page_title,
            "content_preview": snippet[:500],
            "has_content": bool(page_content),
            "rendering_hint": "document",
        }

    def _preview_calculation(self, artifact: Dict[str, Any]) -> Dict[str, Any]:
        """PHASE 7: Enhanced calculation preview with result formatting."""
        expression = artifact.get("expression", "expression")
        result = artifact.get("result", "N/A")
        
        return {
            "type": "calculation",
            "summary": f"{expression} = {result}",
            "expression": expression,
            "result": result,
            # PHASE 7: Rich media expansion
            "rendering_hint": "text",
            "is_numeric": self._is_numeric(result),
        }

    # PHASE 7: NEW PREVIEW HANDLERS
    
    def _preview_data_table(self, artifact: Dict[str, Any]) -> Dict[str, Any]:
        """Generate preview for tabular data."""
        data = artifact.get("data", [])
        columns = artifact.get("columns", [])
        title = artifact.get("title", "Data Table")
        
        rows = data if isinstance(data, list) else []
        headers = columns if isinstance(columns, list) else list(data[0].keys()) if rows and isinstance(rows[0], dict) else []
        
        return {
            "type": "data_table",
            "summary": f"{title} ({len(rows)} rows)",
            "title": title,
            "row_count": len(rows),
            "column_count": len(headers),
            # PHASE 7: Table rendering hints
            "table_data": {
                "headers": headers[:10],  # Limit columns for preview
                "rows": rows[:5],  # Limit rows for preview
                "total_rows": len(rows),
                "sortable": True,
                "filterable": len(rows) > 10,
                "paginated": len(rows) > 50,
            },
            "rendering_hint": "table",
            "export_formats": ["csv", "json", "xlsx"],
        }
    
    def _preview_chart_data(self, artifact: Dict[str, Any]) -> Dict[str, Any]:
        """Generate preview for chart data with visualization config."""
        chart_type = artifact.get("chart_type", "bar")
        title = artifact.get("title", "Chart")
        data = artifact.get("data", {})
        
        # PHASE 7: Generate chart configuration
        chart_config = {
            "type": chart_type,
            "title": title,
            "data": data,
            "options": {
                "responsive": True,
                "maintainAspectRatio": False,
                "plugins": {
                    "legend": {"display": True},
                    "title": {"display": True, "text": title},
                },
            },
        }
        
        return {
            "type": "chart_data",
            "summary": f"{title} ({chart_type} chart)",
            "title": title,
            "chart_type": chart_type,
            # PHASE 7: Chart rendering configuration
            "chart_config": chart_config,
            "rendering_hint": "chart",
            "supported_chart_types": ["line", "bar", "pie", "scatter", "radar"],
        }
    
    def _preview_code_snippet(self, artifact: Dict[str, Any]) -> Dict[str, Any]:
        """Generate preview for code with syntax highlighting."""
        code = artifact.get("code", "")
        language = artifact.get("language", "python")
        title = artifact.get("title", "Code Snippet")
        
        # PHASE 7: Code syntax highlighting metadata
        return {
            "type": "code_snippet",
            "summary": f"{title} ({language})",
            "title": title,
            "language": language,
            # PHASE 7: Rich media expansion
            "code_preview": code[:500],
            "code_length": len(code),
            "line_count": len(code.split("\n")),
            "rendering_hint": "code",
            "syntax_highlighting": True,
            "supported_languages": ["python", "javascript", "java", "cpp", "sql", "html", "css", "json"],
        }
    
    def _preview_image_gallery(self, artifact: Dict[str, Any]) -> Dict[str, Any]:
        """Generate preview for image galleries."""
        images = artifact.get("images", [])
        title = artifact.get("title", "Image Gallery")
        
        # PHASE 7: Image gallery preview
        image_previews = []
        for img in images[:6]:  # Show first 6
            if isinstance(img, dict):
                image_previews.append({
                    "src": img.get("src") or img.get("url"),
                    "alt": img.get("alt") or img.get("title") or "Image",
                    "title": img.get("title") or "",
                })
            else:
                image_previews.append({
                    "src": str(img),
                    "alt": "Image",
                })
        
        return {
            "type": "image_gallery",
            "summary": f"{title} ({len(images)} images)",
            "title": title,
            "image_count": len(images),
            # PHASE 7: Rich media expansion
            "images_preview": image_previews,
            "rendering_hint": "gallery",
            "gallery_type": "grid",
        }
    
    def _preview_html_content(self, artifact: Dict[str, Any]) -> Dict[str, Any]:
        """Generate preview for HTML content."""
        html = artifact.get("html") or artifact.get("content", "")
        title = artifact.get("title", "HTML Content")
        
        # Extract text snippet from HTML
        text_snippet = self._extract_html_text(html)
        
        return {
            "type": "html_content",
            "summary": text_snippet[:300],
            "title": title,
            # PHASE 7: HTML rendering
            "html_preview": html[:1000],  # Limited preview
            "has_html": bool(html),
            "text_length": len(text_snippet),
            "rendering_hint": "document",
            "can_render_html": True,
        }
    
    def _preview_json_data(self, artifact: Dict[str, Any]) -> Dict[str, Any]:
        """Generate preview for JSON data."""
        data = artifact.get("data") or artifact.get("json", {})
        title = artifact.get("title", "JSON Data")
        
        return {
            "type": "json_data",
            "summary": f"{title} (JSON object)",
            "title": title,
            # PHASE 7: JSON rendering
            "data": data,
            "rendering_hint": "json",
            "keys": list(data.keys()) if isinstance(data, dict) else [],
            "is_array": isinstance(data, list),
        }

    def _preview_generic(self, artifact: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback preview for unknown types."""
        return {
            "type": "generic",
            "summary": artifact.get("artifact_type") or "artifact",
            "rendering_hint": "text",
        }
    
    # PHASE 7: UTILITY METHODS
    
    @staticmethod
    def _escape_html(text: str) -> str:
        """Escape HTML special characters."""
        if not isinstance(text, str):
            text = str(text)
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#39;"))
    
    @staticmethod
    def _extract_page_snippet(html: str) -> str:
        """Extract text snippet from HTML."""
        if not html:
            return ""
        
        # Remove script and style tags
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', html)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text[:500]
    
    @staticmethod
    def _extract_html_text(html: str) -> str:
        """Extract plain text from HTML for preview."""
        if not html:
            return ""
        
        # Remove script and style tags
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html)
        
        # Decode common HTML entities
        text = (text
                .replace("&amp;", "&")
                .replace("&lt;", "<")
                .replace("&gt;", ">")
                .replace("&quot;", '"')
                .replace("&#39;", "'")
                .replace("&nbsp;", " "))
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    @staticmethod
    def _is_numeric(value: Any) -> bool:
        """Check if a value is numeric."""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False
