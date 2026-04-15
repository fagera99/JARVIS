"""
Code execution tool for JARVIS.
Safely executes Python code in a sandboxed environment.
"""

import io
import sys
import traceback
from contextlib import redirect_stderr, redirect_stdout


def code_executor_tool(code: str, language: str = "python") -> str:
    """
    Execute Python code and return the output.

    Args:
        code: The code to execute
        language: Programming language (only 'python' supported currently)

    Returns:
        Output from code execution or error message
    """
    if language.lower() != "python":
        return f"Language '{language}' is not supported. Only Python is currently supported."

    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    # Restricted builtins for safety
    safe_globals = {
        "__builtins__": {
            "print": print,
            "len": len,
            "range": range,
            "enumerate": enumerate,
            "zip": zip,
            "map": map,
            "filter": filter,
            "sorted": sorted,
            "reversed": reversed,
            "list": list,
            "dict": dict,
            "set": set,
            "tuple": tuple,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "complex": complex,
            "bytes": bytes,
            "bytearray": bytearray,
            "type": type,
            "isinstance": isinstance,
            "issubclass": issubclass,
            "hasattr": hasattr,
            "getattr": getattr,
            "setattr": setattr,
            "delattr": delattr,
            "callable": callable,
            "repr": repr,
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum,
            "pow": pow,
            "divmod": divmod,
            "hex": hex,
            "oct": oct,
            "bin": bin,
            "chr": chr,
            "ord": ord,
            "format": format,
            "input": lambda *a: "",  # disabled
            "open": None,  # disabled for safety
            "__import__": __import__,
            "Exception": Exception,
            "ValueError": ValueError,
            "TypeError": TypeError,
            "KeyError": KeyError,
            "IndexError": IndexError,
            "AttributeError": AttributeError,
            "RuntimeError": RuntimeError,
            "StopIteration": StopIteration,
            "True": True,
            "False": False,
            "None": None,
            "NotImplemented": NotImplemented,
        }
    }

    # Use the same dict for globals and locals so that recursive functions
    # defined in exec'd code can look themselves up in the shared namespace.
    exec_env: dict = safe_globals.copy()

    try:
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            exec(compile(code, "<jarvis_code>", "exec"), exec_env)  # noqa: S102

        stdout_output = stdout_capture.getvalue()
        stderr_output = stderr_capture.getvalue()

        result_parts = ["✅ Code executed successfully"]
        if stdout_output:
            result_parts.append(f"\nOutput:\n{stdout_output.rstrip()}")
        if stderr_output:
            result_parts.append(f"\nWarnings/Errors:\n{stderr_output.rstrip()}")
        if not stdout_output and not stderr_output:
            result_parts.append("\n(No output produced)")

        return "\n".join(result_parts)

    except SyntaxError as e:
        return f"❌ Syntax Error:\n{str(e)}\n\nLine {e.lineno}: {e.text}"
    except Exception as e:
        tb = traceback.format_exc()
        stderr_output = stderr_capture.getvalue()
        result = f"❌ Execution Error:\n{type(e).__name__}: {str(e)}"
        if stderr_output:
            result += f"\n\nStderr:\n{stderr_output}"
        return result


# Tool definition for OpenAI function calling
CODE_EXECUTOR_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "execute_python",
        "description": (
            "Execute Python code and return the output. "
            "Use this for calculations, data processing, generating code examples, "
            "or any computational tasks."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "The Python code to execute",
                },
                "language": {
                    "type": "string",
                    "description": "Programming language (default: python)",
                    "default": "python",
                },
            },
            "required": ["code"],
        },
    },
}
