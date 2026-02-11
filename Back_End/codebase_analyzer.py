"""
Read-only codebase analyzer for repository structure, file summaries,
and dependency mapping. No execution, no writes.
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional


class CodebaseAnalyzer:
    """Read-only codebase analysis (no modifications)"""

    EXCLUDED_DIRS = {
        ".git",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        "dist",
        "build",
        ".idea",
        ".vscode",
    }

    EXCLUDED_FILES = {".env", ".env.example"}

    SUPPORTED_CODE_EXTS = {".py", ".js", ".ts", ".jsx", ".tsx"}

    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path).resolve()

    def get_repo_index(self) -> Dict:
        """Analyze overall repository structure"""
        structure = {}
        total_lines = 0
        languages = set()

        for item in self.root_path.iterdir():
            if item.is_dir() and not self._is_excluded_dir(item):
                files = [f for f in item.glob("*.*") if f.is_file() and not self._is_excluded_file(f)]
                subdirs = [d.name for d in item.iterdir() if d.is_dir() and not self._is_excluded_dir(d)]

                dir_lines = 0
                for f in files:
                    if f.suffix in self.SUPPORTED_CODE_EXTS:
                        dir_lines += self._count_lines(f)
                        languages.add(self._language_from_suffix(f.suffix))

                total_lines += dir_lines

                structure[item.name] = {
                    "files": [f.name for f in files if f.suffix in self.SUPPORTED_CODE_EXTS],
                    "subdirs": subdirs,
                    "total_files": len(files),
                    "description": self._infer_dir_description(item.name),
                }

        return {
            "type": "repo_index",
            "structure": structure,
            "total_lines_of_code": total_lines,
            "languages": sorted([l for l in languages if l]),
            "entry_points": self._find_entry_points(),
        }

    def get_file_summary(self, filepath: str) -> Dict:
        """Summarize a specific file without executing it"""
        path = self._resolve_safe(filepath)
        if not path:
            return {"error": f"File not found or not allowed: {filepath}"}

        if path.suffix == ".py":
            return self._summarize_python_file(path)
        if path.suffix in {".js", ".ts", ".jsx", ".tsx"}:
            return self._summarize_js_file(path)

        return {"error": f"Unsupported file type: {path.suffix}"}

    def get_dependency_map(self) -> Dict:
        """Analyze how modules depend on each other"""
        dependency_graph: Dict[str, Dict] = {}
        python_files = list(self._iter_code_files(exts={".py"}))

        module_map = {
            self._module_name_from_path(f): self._rel_path(f)
            for f in python_files
        }

        for py_file in python_files:
            filepath = self._rel_path(py_file)
            content = self._safe_read_text(py_file)
            imports = re.findall(r"^(?:from|import)\s+([\w.]+)", content, re.MULTILINE)
            imports = [imp.split(".")[0] for imp in imports]

            dependency_graph[filepath] = {
                "imports": list(sorted(set(imports))),
                "is_imported_by": [],
            }

        for filepath, deps in dependency_graph.items():
            for imp in deps["imports"]:
                if imp in module_map:
                    imported_file = module_map[imp]
                    if imported_file in dependency_graph:
                        dependency_graph[imported_file]["is_imported_by"].append(filepath)

        return {
            "type": "dependency_map",
            "analysis": dependency_graph,
            "circular_dependencies": self._detect_circular_deps(dependency_graph),
            "orphaned_files": self._find_orphaned_files(dependency_graph),
            "core_modules": self._identify_core_modules(dependency_graph),
        }

    def _summarize_python_file(self, path: Path) -> Dict:
        content = self._safe_read_text(path)
        lines = content.split("\n")

        classes = re.findall(r"^class\s+(\w+)", content, re.MULTILINE)
        functions = re.findall(r"^def\s+(\w+)", content, re.MULTILINE)
        imports = re.findall(r"^(?:from|import)\s+([\w.]+)", content, re.MULTILINE)

        docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
        docstring = docstring_match.group(1).strip() if docstring_match else "No docstring"

        return {
            "type": "file_summary",
            "file": self._rel_path(path),
            "lines_of_code": len(lines),
            "docstring": docstring[:200],
            "classes": classes,
            "functions": functions,
            "imports": list(sorted(set(imports))),
            "purpose": self._infer_file_purpose(self._rel_path(path), classes, functions),
            "integration_points": self._find_integration_points(self._rel_path(path), content),
            "dependencies_on_me": self._find_dependents(self._rel_path(path)),
        }

    def _summarize_js_file(self, path: Path) -> Dict:
        content = self._safe_read_text(path)
        lines = content.split("\n")

        components = re.findall(r"(?:class|function)\s+(\w+)", content)
        imports = re.findall(r"(?:import|from)\s+[\"']([\w/.-]+)[\"']", content)

        return {
            "type": "file_summary",
            "file": self._rel_path(path),
            "lines_of_code": len(lines),
            "components": list(sorted(set(components))),
            "imports": list(sorted(set(imports))),
            "purpose": self._infer_file_purpose(self._rel_path(path), [], []),
            "integration_points": self._find_integration_points(self._rel_path(path), content),
        }

    def _count_lines(self, filepath: Path) -> int:
        try:
            with open(filepath, "r", errors="ignore") as f:
                return sum(1 for _ in f)
        except Exception:
            return 0

    def _infer_dir_description(self, dirname: str) -> str:
        descriptions = {
            "backend": "Core agent logic and tools",
            "frontend": "UI dashboard",
            "tests": "Test scripts",
            "docs": "Documentation",
        }
        return descriptions.get(dirname, f"{dirname} module")

    def _infer_file_purpose(self, filepath: str, classes: List[str], functions: List[str]) -> str:
        if filepath.endswith("agent.py"):
            return "Main agent execution engine"
        if "tool_selector" in filepath:
            return "Intelligent tool selection logic"
        if "tool_registry" in filepath:
            return "Tool registration and execution"
        if "memory" in filepath:
            return "Memory subsystem"
        if "main.py" in filepath:
            return "API entry point"
        return f"Module with {len(classes)} classes and {len(functions)} functions"

    def _find_integration_points(self, filepath: str, content: str) -> List[str]:
        points = []
        if filepath.endswith("agent.py"):
            points.append("Called by API endpoints")
        if "tool_registry" in filepath:
            points.append("Used by agent step execution")
        if "tool_selector" in filepath:
            points.append("Used by agent for tool choice")
        return points

    def _find_dependents(self, filepath: str) -> List[str]:
        dependents = []
        module_name = filepath.replace("/", ".").replace(".py", "")
        for py_file in self._iter_code_files(exts={".py"}):
            rel = self._rel_path(py_file)
            if rel == filepath:
                continue
            content = self._safe_read_text(py_file)
            if re.search(rf"\bimport\s+{re.escape(module_name)}\b", content) or re.search(
                rf"\bfrom\s+{re.escape(module_name)}\b", content
            ):
                dependents.append(rel)
        return sorted(list(set(dependents)))

    def _detect_circular_deps(self, graph: Dict[str, Dict]) -> List[List[str]]:
        cycles = []
        visited = set()
        stack = []

        def visit(node: str):
            if node in stack:
                cycle = stack[stack.index(node):] + [node]
                cycles.append(cycle)
                return
            if node in visited:
                return
            visited.add(node)
            stack.append(node)
            for dep in graph.get(node, {}).get("imports", []):
                # map import to file path if exists
                for file_path in graph.keys():
                    if file_path.replace("/", ".").replace(".py", "").endswith(dep):
                        visit(file_path)
            stack.pop()

        for node in graph.keys():
            visit(node)

        return cycles

    def _find_orphaned_files(self, graph: Dict[str, Dict]) -> List[str]:
        orphaned = []
        for filepath, deps in graph.items():
            if filepath.endswith("__init__.py"):
                continue
            if "test" in Path(filepath).name:
                continue
            if not deps.get("is_imported_by"):
                orphaned.append(filepath)
        return sorted(orphaned)

    def _identify_core_modules(self, graph: Dict[str, Dict]) -> List[str]:
        core = []
        for filepath, deps in graph.items():
            if len(deps.get("is_imported_by", [])) >= 2:
                core.append(filepath)
        return sorted(core)

    def _detect_languages(self) -> List[str]:
        languages = set()
        for f in self._iter_code_files(exts=self.SUPPORTED_CODE_EXTS):
            languages.add(self._language_from_suffix(f.suffix))
        return sorted([l for l in languages if l])

    def _find_entry_points(self) -> List[str]:
        candidates = [
            "backend/main.py",
            "frontend/src/index.js",
            "frontend/src/main.tsx",
            "app.py",
        ]
        existing = []
        for c in candidates:
            path = self.root_path / c
            if path.exists():
                existing.append(c)
        return existing

    def _iter_code_files(self, exts: Set[str]) -> List[Path]:
        files = []
        for path in self.root_path.rglob("*"):
            if path.is_file() and path.suffix in exts and not self._is_excluded_file(path):
                if not self._is_excluded_dir(path.parent):
                    files.append(path)
        return files

    def _language_from_suffix(self, suffix: str) -> str:
        mapping = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
        }
        return mapping.get(suffix, "")

    def _module_name_from_path(self, path: Path) -> str:
        rel = self._rel_path(path)
        if rel.endswith("/__init__.py"):
            rel = rel.replace("/__init__.py", "")
        return rel.replace("/", ".").replace(".py", "")

    def _safe_read_text(self, path: Path, max_bytes: int = 200_000) -> str:
        try:
            if path.stat().st_size > max_bytes:
                logging.debug(f"Skipping large file: {path}")
                with open(path, "r", errors="ignore") as f:
                    return f.read(max_bytes)
            with open(path, "r", errors="ignore") as f:
                return f.read()
        except Exception:
            return ""

    def _resolve_safe(self, filepath: str) -> Optional[Path]:
        try:
            path = (self.root_path / filepath).resolve()
            if not path.exists() or not path.is_file():
                return None
            if self.root_path not in path.parents and path != self.root_path:
                return None
            if self._is_excluded_file(path) or self._is_excluded_dir(path.parent):
                return None
            return path
        except Exception:
            return None

    def _rel_path(self, path: Path) -> str:
        return str(path.relative_to(self.root_path)).replace("\\", "/")

    def _is_excluded_dir(self, path: Path) -> bool:
        return path.name in self.EXCLUDED_DIRS or path.name.startswith(".")

    def _is_excluded_file(self, path: Path) -> bool:
        return path.name in self.EXCLUDED_FILES

