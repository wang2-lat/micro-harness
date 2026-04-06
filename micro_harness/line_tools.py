"""
Line-based edit tools — bypass exact string matching.

Hypothesis: DeepSeek fails edit because of exact match.
line_edit uses line numbers instead. Read shows line numbers,
so the model just needs to say "replace line 42" instead of
copying exact text.
"""
from pathlib import Path


def tool_line_edit(path: str, line_start: int, line_end: int, new_content: str) -> str:
    """Replace lines by number. No exact match needed."""
    p = Path(path).expanduser()
    if not p.exists():
        return f"ERROR: File not found: {path}"
    lines = p.read_text().splitlines(keepends=True)
    if line_start < 1 or line_end > len(lines) or line_start > line_end:
        return f"ERROR: Invalid range {line_start}-{line_end} (file has {len(lines)} lines)"
    old = "".join(lines[line_start-1:line_end])
    new_lines = new_content if new_content.endswith("\n") else new_content + "\n"
    lines[line_start-1:line_end] = [new_lines]
    p.write_text("".join(lines))
    return f"Replaced lines {line_start}-{line_end}. Was:\n{old.rstrip()}"


def tool_insert_lines(path: str, after_line: int, content: str) -> str:
    """Insert text after a line number. 0 = insert at top."""
    p = Path(path).expanduser()
    if not p.exists():
        return f"ERROR: File not found: {path}"
    lines = p.read_text().splitlines(keepends=True)
    if after_line < 0 or after_line > len(lines):
        return f"ERROR: Invalid line {after_line} (file has {len(lines)} lines)"
    insert = content if content.endswith("\n") else content + "\n"
    lines.insert(after_line, insert)
    p.write_text("".join(lines))
    return f"Inserted after line {after_line}"


LINE_TOOLS_SCHEMA = [
    {
        "name": "line_edit",
        "description": "Replace lines by number range. Read the file first to see line numbers, then specify which lines to replace. Easier than edit — no exact string matching needed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "line_start": {"type": "integer", "description": "First line to replace (1-indexed)"},
                "line_end": {"type": "integer", "description": "Last line to replace (inclusive)"},
                "new_content": {"type": "string", "description": "New text for those lines"},
            },
            "required": ["path", "line_start", "line_end", "new_content"],
        },
    },
    {
        "name": "insert_lines",
        "description": "Insert new lines after a specific line number. Use 0 to insert at the top of the file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "after_line": {"type": "integer", "description": "Insert after this line (0 = top)"},
                "content": {"type": "string", "description": "Text to insert"},
            },
            "required": ["path", "after_line", "content"],
        },
    },
]

LINE_TOOLS_DISPATCH = {
    "line_edit": tool_line_edit,
    "insert_lines": tool_insert_lines,
}
