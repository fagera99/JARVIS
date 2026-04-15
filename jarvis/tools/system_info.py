"""
System information tool for JARVIS.
Provides current time, date, and basic system info.
"""

import platform
import sys
from datetime import datetime, timezone


def system_info_tool(info_type: str = "datetime") -> str:
    """
    Get system information.

    Args:
        info_type: Type of info - 'datetime', 'date', 'time', 'platform', 'all'

    Returns:
        System information as a string
    """
    now_utc = datetime.now(timezone.utc)
    now_local = datetime.now()
    info_type = info_type.lower()

    if info_type in ("datetime", "all", "now"):
        dt_info = (
            f"🕐 Current Date & Time:\n"
            f"  Local: {now_local.strftime('%A, %B %d, %Y %H:%M:%S')}\n"
            f"  UTC:   {now_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            f"  Unix:  {int(now_local.timestamp())}"
        )
        if info_type == "datetime":
            return dt_info

    if info_type in ("date",):
        return f"📅 Today's date: {now_local.strftime('%A, %B %d, %Y')}"

    if info_type in ("time",):
        return f"🕐 Current time: {now_local.strftime('%H:%M:%S')}"

    if info_type in ("platform",):
        return (
            f"💻 System Information:\n"
            f"  OS: {platform.system()} {platform.release()}\n"
            f"  Architecture: {platform.machine()}\n"
            f"  Python: {sys.version.split()[0]}"
        )

    if info_type == "all":
        return (
            f"{dt_info}\n\n"
            f"💻 System:\n"
            f"  OS: {platform.system()} {platform.release()}\n"
            f"  Architecture: {platform.machine()}\n"
            f"  Python: {sys.version.split()[0]}"
        )

    return f"Unknown info type: '{info_type}'. Valid types: datetime, date, time, platform, all"


# Tool definition for OpenAI function calling
SYSTEM_INFO_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "system_info",
        "description": (
            "Get current system information including date, time, and platform details. "
            "Use when the user asks about the current time, date, or system info."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "info_type": {
                    "type": "string",
                    "enum": ["datetime", "date", "time", "platform", "all"],
                    "description": "Type of system information to retrieve",
                    "default": "datetime",
                },
            },
            "required": [],
        },
    },
}
