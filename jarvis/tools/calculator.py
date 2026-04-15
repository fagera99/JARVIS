"""
Calculator tool for JARVIS.
Safe mathematical expression evaluation.
"""

import math
import operator


def calculator_tool(expression: str) -> str:
    """
    Evaluate a mathematical expression safely.

    Args:
        expression: Mathematical expression to evaluate

    Returns:
        Result of the calculation
    """
    # Safe math functions and constants
    safe_env = {
        # Constants
        "pi": math.pi,
        "e": math.e,
        "inf": math.inf,
        "tau": math.tau,
        # Basic math
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "pow": pow,
        "divmod": divmod,
        # Math functions
        "sqrt": math.sqrt,
        "cbrt": lambda x: x ** (1 / 3),
        "ceil": math.ceil,
        "floor": math.floor,
        "trunc": math.trunc,
        "factorial": math.factorial,
        "gcd": math.gcd,
        "lcm": getattr(math, "lcm", lambda a, b: abs(a * b) // math.gcd(a, b)),
        "log": math.log,
        "log2": math.log2,
        "log10": math.log10,
        "exp": math.exp,
        # Trig
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "asin": math.asin,
        "acos": math.acos,
        "atan": math.atan,
        "atan2": math.atan2,
        "degrees": math.degrees,
        "radians": math.radians,
        "sinh": math.sinh,
        "cosh": math.cosh,
        "tanh": math.tanh,
        # Combinatorics
        "comb": math.comb,
        "perm": math.perm,
        # Types
        "int": int,
        "float": float,
        "complex": complex,
    }

    try:
        # Clean the expression
        cleaned = expression.strip()

        # Basic safety check - block dangerous patterns
        dangerous = ["import", "exec", "eval", "open", "os.", "sys.", "__"]
        for d in dangerous:
            if d in cleaned.lower():
                return f"❌ Expression contains disallowed pattern: '{d}'"

        result = eval(cleaned, {"__builtins__": {}}, safe_env)  # noqa: S307

        # Format result nicely
        if isinstance(result, float):
            if result == int(result) and abs(result) < 1e15:
                formatted = str(int(result))
            else:
                formatted = f"{result:.10g}"
        else:
            formatted = str(result)

        return f"🧮 {expression} = {formatted}"

    except ZeroDivisionError:
        return "❌ Division by zero"
    except ValueError as e:
        return f"❌ Math error: {str(e)}"
    except SyntaxError:
        return f"❌ Invalid expression: '{expression}'"
    except Exception as e:
        return f"❌ Calculation failed: {str(e)}"


# Tool definition for OpenAI function calling
CALCULATOR_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": (
            "Evaluate mathematical expressions. "
            "Supports basic arithmetic, algebra, trigonometry, logarithms, "
            "and other mathematical functions."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": (
                        "Mathematical expression to evaluate. "
                        "Examples: '2 + 2', 'sqrt(144)', 'sin(pi/2)', "
                        "'factorial(10)', 'log(100, 10)'"
                    ),
                },
            },
            "required": ["expression"],
        },
    },
}
