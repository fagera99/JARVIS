"""
File manager tool for JARVIS.
Handles file reading, writing, and listing operations.
"""

import os
from pathlib import Path


def _safe_path(path: str) -> Path:
    """Resolve and validate a path to prevent directory traversal."""
    resolved = Path(path).expanduser().resolve()
    return resolved


def file_manager_tool(
    operation: str,
    path: str,
    content: str = "",
    encoding: str = "utf-8",
) -> str:
    """
    Perform file system operations.

    Args:
        operation: One of 'read', 'write', 'append', 'list', 'exists', 'delete', 'info'
        path: File or directory path
        content: Content to write (for write/append operations)
        encoding: File encoding (default: utf-8)

    Returns:
        Result of the operation as a string
    """
    try:
        safe = _safe_path(path)
        op = operation.lower()

        if op == "read":
            if not safe.exists():
                return f"❌ File not found: {path}"
            if not safe.is_file():
                return f"❌ Path is not a file: {path}"
            size = safe.stat().st_size
            if size > 1_000_000:  # 1MB limit
                return f"❌ File too large ({size:,} bytes). Maximum is 1MB."
            text = safe.read_text(encoding=encoding)
            return f"📄 Contents of {path}:\n\n{text}"

        elif op == "write":
            safe.parent.mkdir(parents=True, exist_ok=True)
            safe.write_text(content, encoding=encoding)
            return f"✅ Written {len(content):,} characters to {path}"

        elif op == "append":
            safe.parent.mkdir(parents=True, exist_ok=True)
            with safe.open("a", encoding=encoding) as f:
                f.write(content)
            return f"✅ Appended {len(content):,} characters to {path}"

        elif op == "list":
            if not safe.exists():
                return f"❌ Directory not found: {path}"
            if not safe.is_dir():
                return f"❌ Path is not a directory: {path}"
            items = sorted(safe.iterdir(), key=lambda p: (p.is_file(), p.name))
            lines = [f"📁 Contents of {path}:\n"]
            for item in items[:100]:  # limit to 100 items
                icon = "📄" if item.is_file() else "📁"
                size = f" ({item.stat().st_size:,} B)" if item.is_file() else ""
                lines.append(f"  {icon} {item.name}{size}")
            if len(list(safe.iterdir())) > 100:
                lines.append("  ... (truncated at 100 items)")
            return "\n".join(lines)

        elif op == "exists":
            exists = safe.exists()
            kind = "file" if safe.is_file() else "directory" if safe.is_dir() else "unknown"
            return f"{'✅ Exists' if exists else '❌ Does not exist'}: {path}" + (
                f" ({kind})" if exists else ""
            )

        elif op == "delete":
            if not safe.exists():
                return f"❌ Path not found: {path}"
            if safe.is_file():
                safe.unlink()
                return f"✅ Deleted file: {path}"
            else:
                return f"❌ Can only delete files, not directories. Got: {path}"

        elif op == "info":
            if not safe.exists():
                return f"❌ Path not found: {path}"
            stat = safe.stat()
            import datetime
            modified = datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
            created = datetime.datetime.fromtimestamp(stat.st_ctime).isoformat()
            kind = "File" if safe.is_file() else "Directory"
            return (
                f"📊 Info for {path}:\n"
                f"  Type: {kind}\n"
                f"  Size: {stat.st_size:,} bytes\n"
                f"  Modified: {modified}\n"
                f"  Created: {created}\n"
                f"  Readable: {os.access(safe, os.R_OK)}\n"
                f"  Writable: {os.access(safe, os.W_OK)}"
            )

        else:
            return (
                f"❌ Unknown operation: '{operation}'. "
                "Valid operations: read, write, append, list, exists, delete, info"
            )

    except PermissionError:
        return f"❌ Permission denied: {path}"
    except Exception as e:
        return f"❌ File operation failed: {str(e)}"


# Tool definition for OpenAI function calling
FILE_MANAGER_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "file_manager",
        "description": (
            "Read, write, list, or manage files and directories. "
            "Use for reading configuration files, writing notes, "
            "or exploring file system contents."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["read", "write", "append", "list", "exists", "delete", "info"],
                    "description": "The file operation to perform",
                },
                "path": {
                    "type": "string",
                    "description": "The file or directory path",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write (for write/append operations)",
                    "default": "",
                },
            },
            "required": ["operation", "path"],
        },
    },
}
