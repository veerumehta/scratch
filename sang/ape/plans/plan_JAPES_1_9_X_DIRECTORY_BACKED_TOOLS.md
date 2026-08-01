# JAPES 1.9.x: Directory-Backed Tool Factory

Author: Virendra Mehta
Created: Wednesday, July 1, 2026
Status: Draft for build
Repos affected: `japes/`

## Why this plan exists

MACER's `tools/documents.py` implements a source-keyed, directory-backed
`@function_tool` pattern: `list_documents(source, pattern)`, `read_document(source,
filename)`, `search_documents(source, pattern)` — where each `source` (LOAN,
GUIDELINES, LOS_ENTITIES) maps to a local directory downloaded from KH before the
agent runs. This is the grounding tool pattern any download-then-agent solution needs.

JAPES's `tools/documents.py` already has local file utilities (`read_local_file`,
`search_local_files`, `list_local_files`) but they are operational utilities, not
`@function_tool`-wrapped agent tools, and they are not source-keyed.

The Jazz Assistant build plan (§9.4, Appendix A) explicitly identifies this as code
it will port from MACER. If the factory lives in the SDK instead, the Jazz Assistant
does not port anything: it calls `build_directory_tools({"loan": loan_dir,
"guidelines": guidelines_dir, "los": los_dir})` and gets back ready-to-use agent tools.
Any other solution that follows the download-then-agent pattern — JACI, future domain
packs — benefits equally.

MACER reads directories from global settings (MACER_LOAN_DIR, MACER_GUIDELINES_DIR,
etc). The SDK version takes directories as arguments at build time, per invocation.
No global state, no settings coupling, and works correctly in multi-tenant environments
where different invocations may use different directories.

## What this plan does NOT change

- Does not modify existing `jazzx_sdk/tools/documents.py` utilities.
- Does not change MACER's tools (MACER continues to use its own impl until it
  migrates to the SDK in a separate plan).
- Does not add write/output tools — the factory is read-only by design. Solutions
  that need agent-writable output directories build their own narrow write tool.
- Does not add KH-backed tools (list/read via KH client) — those are already in
  `jazzx_sdk/tools/documents.py`.
- Does not wrap the factory in domain-specific source names (LOAN, GUIDELINES, LOS
  are Jazz Assistant concerns; the SDK factory accepts any string source names).

## Design

New file: `jazzx_sdk/tools/dir_tools.py`

```python
"""Directory-backed @function_tool factory for download-then-agent solutions.

Usage:
    tools = build_directory_tools({
        "loan": loan_dir,
        "guidelines": guidelines_dir,
        "los": los_dir,
    })
    # tools.list_documents, tools.read_document, tools.search_documents
    # are @function_tool-wrapped, agent-callable, source-keyed.
"""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agents import function_tool

logger = logging.getLogger(__name__)

_DEFAULT_READ_LIMIT_KB = 10
_SEARCH_TIMEOUT_SECONDS = 30


@dataclass(frozen=True)
class DirectoryToolSet:
    """list/read/search @function_tools backed by named local directories.

    All three tools are @function_tool decorated and ready to pass to
    build_agent(tools=[...]) or InteractiveAgent(tools={...}).
    """

    list_documents: Any    # @function_tool: (source, pattern="*") -> str
    read_document: Any     # @function_tool: (source, filename, start_line=1, end_line=None) -> str
    search_documents: Any  # @function_tool: (source, pattern, file_pattern="*", ...) -> str
    sources: frozenset     # the valid source names (for introspection/validation)


def build_directory_tools(
    sources: dict[str, Path | str],
    *,
    read_limit_kb: int = _DEFAULT_READ_LIMIT_KB,
) -> DirectoryToolSet:
    """Build source-keyed list/read/search @function_tools backed by local directories.

    Args:
        sources: Map of source name to local directory path.
                 e.g. {"loan": loan_dir, "guidelines": guidelines_dir, "los": los_dir}
                 All directories must exist at call time.
        read_limit_kb: Max file size the read tool will return in full (default 10 KB).
                       Files larger than this require a start_line/end_line range.

    Returns:
        DirectoryToolSet with list_documents, read_document, search_documents tools.

    Raises:
        ValueError: If any source directory does not exist or is not a directory.
    """
    resolved: dict[str, Path] = {}
    for name, path in sources.items():
        p = Path(path)
        if not p.exists():
            raise ValueError(f"source '{name}': directory does not exist: {p}")
        if not p.is_dir():
            raise ValueError(f"source '{name}': path is not a directory: {p}")
        resolved[name] = p.resolve()

    valid_sources = sorted(resolved.keys())
    _read_limit_bytes = read_limit_kb * 1024

    def _get_dir(source: str) -> Path | str:
        """Return the resolved Path for a source, or an error string."""
        if source not in resolved:
            return (
                f"Error: unknown source '{source}'. "
                f"Valid sources: {valid_sources}"
            )
        return resolved[source]

    def _safe_relative(root: Path, filename: str) -> Path | str:
        """Resolve filename relative to root; reject path-traversal attempts."""
        if ".." in filename or filename.startswith("/"):
            return "Error: filename must be a relative path with no '..' components"
        candidate = (root / filename).resolve()
        if not str(candidate).startswith(str(root)):
            return "Error: path traversal rejected"
        return candidate

    @function_tool
    def list_documents(source: str, pattern: str = "*") -> str:
        """List files in the named source directory matching a glob pattern.

        Use this tool to discover which files are available before reading
        or searching them.

        Args:
            source: The source name (e.g. "loan", "guidelines", "los").
            pattern: Glob pattern (e.g. "*.pdf", "**/*.md"). Default: "*".

        Returns:
            Newline-separated list of matching filenames (relative paths),
            or an error string.
        """
        d = _get_dir(source)
        if isinstance(d, str):
            return d
        if not pattern or pattern.startswith("/") or ".." in pattern:
            return "Error: pattern must be a non-empty relative glob pattern"
        try:
            matches = sorted(
                p.relative_to(d).as_posix() for p in d.glob(pattern) if p.is_file()
            )
            return "\n".join(matches)
        except Exception as exc:
            logger.warning("list_documents error source=%s pattern=%s: %s", source, pattern, exc)
            return f"Error: {exc}"

    @function_tool
    def read_document(
        source: str,
        filename: str,
        start_line: int = 1,
        end_line: int | None = None,
    ) -> str:
        """Read a file from the named source directory.

        For large files, specify start_line/end_line to read a range.

        Args:
            source: The source name (e.g. "loan", "guidelines", "los").
            filename: Relative path to the file (from list_documents).
            start_line: First line to return (1-indexed, default 1).
            end_line: Last line to return inclusive (default: end of file).

        Returns:
            File content (or specified line range), or an error string.
        """
        d = _get_dir(source)
        if isinstance(d, str):
            return d
        path = _safe_relative(d, filename)
        if isinstance(path, str):
            return path
        if not path.exists():
            return (
                f"Error: file not found: {filename}. "
                "Use list_documents to see available files."
            )
        if not path.is_file():
            return f"Error: not a file: {filename}"
        try:
            lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        except Exception as exc:
            return f"Error: could not read file: {exc}"

        total = len(lines)
        if start_line < 1:
            return "Error: start_line must be >= 1"
        if start_line > total:
            return f"Error: start_line {start_line} exceeds file length ({total} lines)"
        end = total if end_line is None else min(end_line, total)
        if end < start_line:
            return f"Error: end_line {end_line} must be >= start_line {start_line}"

        content = "".join(lines[start_line - 1 : end])
        if len(content.encode("utf-8")) > _read_limit_bytes:
            return (
                f"Error: content exceeds {read_limit_kb} KB limit. "
                f"Specify a start_line/end_line range. File has {total} lines."
            )
        return content

    @function_tool
    def search_documents(
        source: str,
        pattern: str,
        file_pattern: str = "*",
        case_insensitive: bool = True,
        context_lines: int | None = None,
        max_count: int | None = None,
        word_regexp: bool = False,
    ) -> str:
        """Search for a text pattern across files in the named source directory.

        Uses grep for fast, reliable text search.

        Args:
            source: The source name (e.g. "loan", "guidelines", "los").
            pattern: Text or regex pattern to search for.
            file_pattern: Glob pattern limiting which files to search (default "*").
            case_insensitive: Ignore case (default True).
            context_lines: Lines of context before and after each match.
            max_count: Stop after this many matches per file.
            word_regexp: Match whole words only.

        Returns:
            Matching lines with filenames and line numbers, or empty string if
            no matches, or an error string.
        """
        d = _get_dir(source)
        if isinstance(d, str):
            return d

        cmd = ["grep", "-R", "-n"]
        if case_insensitive:
            cmd.append("-i")
        if word_regexp:
            cmd.append("-w")
        if context_lines is not None:
            cmd.extend(["-C", str(context_lines)])
        if max_count is not None:
            cmd.extend(["-m", str(max_count)])
        if file_pattern != "*":
            cmd.append(f"--include={file_pattern}")
        cmd.extend([pattern, "."])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=_SEARCH_TIMEOUT_SECONDS,
                check=False,
                cwd=str(d),
            )
            if result.returncode == 0:
                return result.stdout or ""
            if result.returncode == 1:
                return ""  # no matches
            return f"Error: grep exited {result.returncode}: {result.stderr}"
        except subprocess.TimeoutExpired:
            return f"Error: search timed out after {_SEARCH_TIMEOUT_SECONDS}s"
        except Exception as exc:
            logger.warning("search_documents error source=%s: %s", source, exc)
            return f"Error: {exc}"

    return DirectoryToolSet(
        list_documents=list_documents,
        read_document=read_document,
        search_documents=search_documents,
        sources=frozenset(valid_sources),
    )
```

## Usage (what Aditya writes in Jazz Assistant)

```python
from jazzx_sdk.tools.dir_tools import build_directory_tools

# After downloading grounding to local dirs:
tool_set = build_directory_tools({
    "loan": loan_dir,
    "guidelines": guidelines_dir,
    "los": los_dir,
})

agent = InteractiveAgent(
    spec,
    agents=ctx.runtime.agents,
    tools={
        "list_documents":   tool_set.list_documents,
        "read_document":    tool_set.read_document,
        "search_documents": tool_set.search_documents,
        "get_findings":     get_findings,  # Jazz Assistant-specific
    },
    hooks=ToolStreamHooks(),
)
```

## Per-file changes

| File | Change |
|---|---|
| `jazzx_sdk/tools/dir_tools.py` | new |
| `jazzx_sdk/tools/__init__.py` | export `build_directory_tools`, `DirectoryToolSet` |

No changes to existing files.

## Acceptance tests

```python
import tempfile
from pathlib import Path
from jazzx_sdk.tools.dir_tools import build_directory_tools

def test_list():
    with tempfile.TemporaryDirectory() as d:
        Path(d, "a.txt").write_text("hello")
        t = build_directory_tools({"src": d})
        result = t.list_documents("src", "*")
        assert "a.txt" in result

def test_read():
    with tempfile.TemporaryDirectory() as d:
        Path(d, "a.txt").write_text("line1\nline2\nline3\n")
        t = build_directory_tools({"src": d})
        result = t.read_document("src", "a.txt", start_line=2, end_line=2)
        assert "line2" in result

def test_search():
    with tempfile.TemporaryDirectory() as d:
        Path(d, "a.txt").write_text("income: 120000\nDTI: 0.38\n")
        t = build_directory_tools({"src": d})
        result = t.search_documents("src", "income")
        assert "income" in result

def test_unknown_source():
    with tempfile.TemporaryDirectory() as d:
        t = build_directory_tools({"src": d})
        result = t.list_documents("bad_source", "*")
        assert result.startswith("Error")

def test_path_traversal_rejected():
    with tempfile.TemporaryDirectory() as d:
        t = build_directory_tools({"src": d})
        result = t.read_document("src", "../etc/passwd")
        assert result.startswith("Error")

def test_missing_dir_raises():
    import pytest
    with pytest.raises(ValueError, match="does not exist"):
        build_directory_tools({"src": "/nonexistent/path"})
```

## Open questions

- Should `DirectoryToolSet` expose an `.as_dict()` helper returning
  `{"list_documents": ..., "read_document": ..., "search_documents": ...}` to reduce
  one line of boilerplate at the call site? Leaning yes — it's a natural ergonomic
  improvement.
- Should `search_documents` fall back to a pure-Python search if `grep` is not
  available (Windows compatibility)? Leaning no for now — target environment is Linux
  containers; add a Windows fallback only if a concrete need arises.
