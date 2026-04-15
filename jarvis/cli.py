"""
JARVIS CLI - The interactive command-line interface for your AI agent.

Features:
- Rich terminal UI with colors and formatting
- Streaming responses for a natural feel
- Special commands for memory management
- Both Arabic and English support
"""

import sys
import uuid
from datetime import datetime

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.style import Style
from rich.text import Text

from .config import config

console = Console()


def print_welcome(agent_name: str = "JARVIS", user_name: str = "") -> None:
    """Print the JARVIS welcome banner."""
    greeting = f"Hello, {user_name}!" if user_name and user_name != "there" else "Hello!"

    welcome_text = f"""[bold cyan]{agent_name}[/bold cyan] — Your AI Agent with Iron Memory 🧠

[dim]{greeting} I'm ready. I remember everything and I'm here to help you with anything.[/dim]

[dim]Type [bold]/help[/bold] to see available commands, or just start talking.[/dim]"""

    console.print(
        Panel(
            welcome_text,
            title=f"[bold blue]⚡ {agent_name} ONLINE ⚡[/bold blue]",
            border_style="blue",
            padding=(1, 2),
        )
    )
    console.print()


def print_help() -> None:
    """Print the help menu."""
    help_text = """[bold]Available Commands:[/bold]

[cyan]/help[/cyan]              - Show this help menu
[cyan]/memory[/cyan]            - Show memory statistics
[cyan]/recall <query>[/cyan]    - Search your memories
[cyan]/remember <text>[/cyan]   - Explicitly save something to memory
[cyan]/history[/cyan]           - Show current session conversation
[cyan]/new[/cyan]               - Start a new conversation session
[cyan]/profile[/cyan]           - Show your user profile
[cyan]/clear[/cyan]             - Clear the screen
[cyan]/exit[/cyan] or [cyan]/quit[/cyan]    - Exit JARVIS

[bold]Tips:[/bold]
• Talk to me naturally in English or Arabic (including Egyptian dialect)
• I remember everything across all your sessions
• I can search the web, run code, do math, and manage files
• The more we talk, the better I understand you"""

    console.print(
        Panel(
            help_text,
            title="[bold blue]JARVIS Help[/bold blue]",
            border_style="blue",
        )
    )


def format_response(text: str) -> None:
    """Format and print JARVIS's response with markdown rendering."""
    console.print()
    # Try to render as markdown for better formatting
    try:
        md = Markdown(text)
        console.print(md)
    except Exception:
        console.print(text)
    console.print()


def handle_special_command(command: str, agent: "JARVISAgent") -> bool:  # type: ignore[name-defined]  # noqa: F821
    """
    Handle special slash commands.

    Returns:
        True if command was handled, False if it's a regular message
    """
    cmd = command.strip().lower()
    parts = command.strip().split(None, 1)
    cmd_name = parts[0].lower()
    cmd_args = parts[1] if len(parts) > 1 else ""

    if cmd_name in ("/exit", "/quit", "/bye"):
        console.print("\n[bold blue]JARVIS:[/bold blue] Goodbye! I'll remember everything until next time. 🧠\n")
        sys.exit(0)

    elif cmd_name == "/help":
        print_help()
        return True

    elif cmd_name == "/clear":
        console.clear()
        return True

    elif cmd_name == "/memory":
        stats = agent.get_memory_stats()
        stats_text = (
            f"[bold]🧠 Memory Statistics:[/bold]\n\n"
            f"  Total memories: [cyan]{stats['total_memories']}[/cyan]\n"
            f"  Total messages: [cyan]{stats['total_messages']}[/cyan]\n"
            f"  Total sessions: [cyan]{stats['total_sessions']}[/cyan]\n"
            f"  Total interactions: [cyan]{stats['total_interactions']}[/cyan]\n"
        )
        if stats.get("memories_by_type"):
            stats_text += "\n  [bold]By type:[/bold]\n"
            for mem_type, count in stats["memories_by_type"].items():
                stats_text += f"    {mem_type}: {count}\n"
        console.print(Panel(stats_text, title="[blue]Memory Stats[/blue]", border_style="blue"))
        return True

    elif cmd_name == "/recall":
        if not cmd_args:
            console.print("[yellow]Usage: /recall <query>[/yellow]")
            return True
        result = agent.recall(cmd_args)
        console.print(Panel(result, title="[blue]Memory Recall[/blue]", border_style="blue"))
        return True

    elif cmd_name == "/remember":
        if not cmd_args:
            console.print("[yellow]Usage: /remember <what to remember>[/yellow]")
            return True
        result = agent.remember(cmd_args)
        console.print(f"[green]{result}[/green]")
        return True

    elif cmd_name == "/profile":
        profile = agent.user_profile
        summary = profile.to_summary()
        console.print(Panel(summary, title="[blue]Your Profile[/blue]", border_style="blue"))
        return True

    elif cmd_name == "/history":
        if not agent.conversation_history:
            console.print("[dim]No conversation history in this session.[/dim]")
        else:
            console.print(
                Panel(
                    "\n".join(
                        f"[{'cyan' if m.role == 'user' else 'blue'}][{m.role.upper()}][/{'cyan' if m.role == 'user' else 'blue'}] {m.content[:100]}{'...' if len(m.content) > 100 else ''}"
                        for m in agent.conversation_history[-10:]
                    ),
                    title="[blue]Recent History[/blue]",
                    border_style="blue",
                )
            )
        return True

    elif cmd_name == "/new":
        new_id = agent.new_session()
        console.print(f"[green]✅ New session started (ID: {new_id[:8]}...)[/green]")
        return True

    return False


def run_cli() -> None:
    """Run the JARVIS CLI interface."""
    from .agent import JARVISAgent

    # Validate configuration
    errors = config.validate()
    if errors:
        console.print("[bold red]Configuration Errors:[/bold red]")
        for error in errors:
            console.print(f"  [red]• {error}[/red]")
        console.print(
            "\n[yellow]Please copy [bold].env.example[/bold] to [bold].env[/bold] "
            "and set your OpenAI API key.[/yellow]"
        )
        sys.exit(1)

    # Initialize agent
    console.print("[dim]Initializing JARVIS...[/dim]")
    agent = JARVISAgent()
    stats = agent.get_memory_stats()

    # Print welcome
    print_welcome("JARVIS", agent.user_name)

    if stats["total_interactions"] > 0:
        console.print(
            f"[dim]📊 I remember {stats['total_memories']} facts and "
            f"{stats['total_interactions']} past interactions with you.[/dim]\n"
        )

    # Main conversation loop
    while True:
        try:
            # Get user input
            console.print("[bold cyan]You:[/bold cyan] ", end="")
            user_input = input().strip()

            if not user_input:
                continue

            # Handle special commands
            if user_input.startswith("/"):
                handle_special_command(user_input, agent)
                continue

            # Regular chat message
            console.print()
            console.print("[bold blue]JARVIS:[/bold blue]", end=" ")

            # Stream the response
            response_chunks = []
            try:
                for chunk in agent.chat_stream(user_input):
                    console.print(chunk, end="", highlight=False)
                    response_chunks.append(chunk)
                console.print("\n")
            except Exception as stream_error:
                # Fallback to non-streaming
                console.print()
                try:
                    response = agent.chat(user_input)
                    format_response(response)
                except Exception as e:
                    console.print(f"\n[red]Error: {str(e)}[/red]\n")

        except KeyboardInterrupt:
            console.print("\n\n[bold blue]JARVIS:[/bold blue] Session paused. Your memories are saved. 🧠\n")
            sys.exit(0)
        except EOFError:
            break
