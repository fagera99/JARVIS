"""
JARVIS - Core AI Agent

The main brain of JARVIS: orchestrates the LLM, memory system, and tools
to provide an intelligent, persistent AI companion.
"""

import json
import uuid
from datetime import datetime
from typing import Any, Iterator

from openai import OpenAI

from .config import config
from .memory.memory_manager import MemoryManager
from .memory.models import Memory, Message, UserProfile
from .tools.calculator import CALCULATOR_TOOL_SCHEMA, calculator_tool
from .tools.code_executor import CODE_EXECUTOR_TOOL_SCHEMA, code_executor_tool
from .tools.file_manager import FILE_MANAGER_TOOL_SCHEMA, file_manager_tool
from .tools.system_info import SYSTEM_INFO_TOOL_SCHEMA, system_info_tool
from .tools.web_search import (
    WEB_FETCH_TOOL_SCHEMA,
    WEB_SEARCH_TOOL_SCHEMA,
    web_fetch_tool,
    web_search_tool,
)

# Memory extraction system prompt
MEMORY_EXTRACTION_PROMPT = """
You are a memory extraction system. Analyze the conversation and extract important information
that JARVIS should remember long-term.

Extract memories in these categories:
- 'fact': Factual information about the user (name, job, location, skills, etc.)
- 'preference': User preferences and likes/dislikes
- 'work_style': How the user works, their methods, tools they use
- 'context': Current projects, goals, or tasks the user is working on
- 'event': Important events or milestones mentioned

Return a JSON array of memories, each with:
{
  "content": "The memory content as a clear, concise statement",
  "memory_type": "fact|preference|work_style|context|event",
  "importance": 0.0-1.0,
  "tags": ["tag1", "tag2"]
}

Only include genuinely useful long-term memories. Skip trivial conversation details.
If nothing important to remember, return an empty array [].
"""

PROFILE_UPDATE_PROMPT = """
Analyze this conversation and extract user profile information.
Return a JSON object with any of these fields (only include fields with new information):
{
  "name": "user's name if mentioned",
  "language": "ar|en|auto - detected primary language",
  "work_style_updates": {"key": "value"} - work habits and style,
  "preference_updates": {"key": "value"} - user preferences,
  "new_topics": ["topic1", "topic2"] - main topics discussed
}
Return null if no profile updates needed.
"""


class JARVISAgent:
    """
    JARVIS AI Agent - Your intelligent, memory-powered AI companion.

    Features:
    - Persistent long-term memory across sessions
    - User profile learning and work style understanding
    - Tool use (web search, code execution, file ops, calculator)
    - Bilingual support (Arabic + English)
    - Conversation history management
    """

    SYSTEM_PROMPT = """You are JARVIS — a highly capable, intelligent AI agent with perfect memory and deep understanding of your user.

Your core traits:
1. **Iron Memory**: You remember everything. You know the user's name, preferences, work style, past conversations, and ongoing projects. Always reference relevant memories naturally.
2. **True Understanding**: You understand what the user really wants, even when they're vague or speaking casually. You read between the lines.
3. **Proactive Intelligence**: Anticipate needs, offer relevant suggestions, and connect information across conversations.
4. **Bilingual Fluency**: You respond in the same language the user uses. If they write in Arabic (including Egyptian dialect), respond in Arabic. If English, respond in English.
5. **Action-Oriented**: You don't just talk — you DO things. Use your tools to search the web, execute code, manage files, and get real information.
6. **Personality**: You're warm, direct, clever, and deeply loyal to your user. You're not a generic chatbot — you're THEIR personal AI.

When you have memories about the user, reference them naturally to show you remember.
When the user asks for something, think about what they actually need and deliver it fully.
Always be honest about what you can and cannot do.

Current date and time: {current_datetime}
{user_profile_section}
{relevant_memories_section}"""

    def __init__(self, session_id: str | None = None) -> None:
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.memory = MemoryManager()
        self.session_id = session_id or str(uuid.uuid4())
        self.conversation_history: list[Message] = []

        # Load existing conversation for this session
        self._load_session_history()

        # Load or initialize user profile
        self.user_profile = self.memory.get_user_profile()

        # Build tool registry
        self.tools = self._build_tools()
        self.tool_schemas = self._build_tool_schemas()

    def _load_session_history(self) -> None:
        """Load existing conversation history for the current session."""
        self.conversation_history = self.memory.get_conversation_history(
            self.session_id,
            limit=config.MAX_HISTORY,
        )

    def _build_tools(self) -> dict[str, Any]:
        """Build the tool function registry."""
        tools: dict[str, Any] = {
            "system_info": system_info_tool,
            "calculator": calculator_tool,
        }
        if config.ENABLE_WEB_SEARCH:
            tools["web_search"] = web_search_tool
            tools["web_fetch"] = web_fetch_tool
        if config.ENABLE_CODE_EXEC:
            tools["execute_python"] = code_executor_tool
        if config.ENABLE_FILE_OPS:
            tools["file_manager"] = file_manager_tool
        return tools

    def _build_tool_schemas(self) -> list[dict]:
        """Build the OpenAI tool schemas based on enabled tools."""
        schemas = [SYSTEM_INFO_TOOL_SCHEMA, CALCULATOR_TOOL_SCHEMA]
        if config.ENABLE_WEB_SEARCH:
            schemas.extend([WEB_SEARCH_TOOL_SCHEMA, WEB_FETCH_TOOL_SCHEMA])
        if config.ENABLE_CODE_EXEC:
            schemas.append(CODE_EXECUTOR_TOOL_SCHEMA)
        if config.ENABLE_FILE_OPS:
            schemas.append(FILE_MANAGER_TOOL_SCHEMA)
        return schemas

    def _build_system_prompt(self, relevant_memories: list[Memory]) -> str:
        """Build the dynamic system prompt with current context."""
        current_dt = datetime.now().strftime("%A, %B %d, %Y at %H:%M:%S")

        # User profile section
        profile_summary = self.user_profile.to_summary()
        if profile_summary and profile_summary != "No profile data yet.":
            user_profile_section = f"\n## User Profile\n{profile_summary}"
        else:
            user_profile_section = ""

        # Relevant memories section
        if relevant_memories:
            mem_lines = ["## Relevant Memories"]
            for mem in relevant_memories:
                mem_lines.append(f"- [{mem.memory_type}] {mem.content}")
            relevant_memories_section = "\n" + "\n".join(mem_lines)
        else:
            relevant_memories_section = ""

        return self.SYSTEM_PROMPT.format(
            current_datetime=current_dt,
            user_profile_section=user_profile_section,
            relevant_memories_section=relevant_memories_section,
        )

    def _execute_tool(self, tool_name: str, tool_args: dict) -> str:
        """Execute a tool and return its result."""
        if tool_name not in self.tools:
            return f"Tool '{tool_name}' is not available."

        tool_fn = self.tools[tool_name]
        try:
            return tool_fn(**tool_args)
        except Exception as e:
            return f"Tool execution error: {str(e)}"

    def _extract_and_save_memories(self, user_msg: str, assistant_msg: str) -> None:
        """Extract important information from the conversation and save to memory."""
        try:
            response = self.client.chat.completions.create(
                model=config.MODEL,
                messages=[
                    {"role": "system", "content": MEMORY_EXTRACTION_PROMPT},
                    {
                        "role": "user",
                        "content": (
                            f"User message: {user_msg}\n\n"
                            f"Assistant response: {assistant_msg}\n\n"
                            f"Extract important long-term memories from this exchange."
                        ),
                    },
                ],
                response_format={"type": "json_object"},
                max_tokens=800,
                temperature=0.1,
            )

            raw = response.choices[0].message.content or "[]"
            data = json.loads(raw)

            # Handle both {"memories": [...]} and [...] formats
            memories_data = data if isinstance(data, list) else data.get("memories", [])

            for mem_data in memories_data:
                if not isinstance(mem_data, dict):
                    continue
                content = mem_data.get("content", "").strip()
                if not content:
                    continue

                # Check for duplicates
                existing = self.memory.search_memories(content, limit=3)
                duplicate = any(
                    e.content.lower() == content.lower() for e in existing
                )
                if duplicate:
                    continue

                memory = Memory(
                    id=None,
                    content=content,
                    memory_type=mem_data.get("memory_type", "fact"),
                    importance=float(mem_data.get("importance", 0.5)),
                    tags=mem_data.get("tags", []),
                )
                self.memory.save_memory(memory)

        except Exception:
            pass  # Memory extraction is best-effort

    def _update_user_profile(self, user_msg: str, assistant_msg: str) -> None:
        """Update user profile based on conversation."""
        try:
            response = self.client.chat.completions.create(
                model=config.MODEL,
                messages=[
                    {"role": "system", "content": PROFILE_UPDATE_PROMPT},
                    {
                        "role": "user",
                        "content": (
                            f"User message: {user_msg}\n\n"
                            f"Assistant response: {assistant_msg}"
                        ),
                    },
                ],
                response_format={"type": "json_object"},
                max_tokens=400,
                temperature=0.1,
            )

            raw = response.choices[0].message.content or "null"
            data = json.loads(raw)

            if not data:
                return

            profile = self.user_profile
            changed = False

            if data.get("name") and not profile.name:
                profile.name = data["name"]
                changed = True

            if data.get("language") and data["language"] != "auto":
                profile.language = data["language"]
                changed = True

            if data.get("work_style_updates"):
                profile.work_style.update(data["work_style_updates"])
                changed = True

            if data.get("preference_updates"):
                profile.preferences.update(data["preference_updates"])
                changed = True

            if data.get("new_topics"):
                for topic in data["new_topics"]:
                    if topic not in profile.frequent_topics:
                        profile.frequent_topics.insert(0, topic)
                changed = True

            if changed:
                self.memory.update_user_profile(profile)

        except Exception:
            pass  # Profile update is best-effort

    def chat(self, user_input: str) -> str:
        """
        Send a message to JARVIS and get a response.

        Args:
            user_input: The user's message

        Returns:
            JARVIS's response
        """
        # Save user message
        user_message = Message(role="user", content=user_input)
        self.conversation_history.append(user_message)
        self.memory.save_message(self.session_id, user_message)
        self.memory.increment_interaction_count()

        # Search for relevant memories
        relevant_memories = self.memory.search_memories(user_input)

        # Build messages for API call
        system_prompt = self._build_system_prompt(relevant_memories)
        messages = [{"role": "system", "content": system_prompt}]

        # Add conversation history (last N messages)
        history_to_include = self.conversation_history[-config.MAX_HISTORY:]
        messages.extend([m.to_dict() for m in history_to_include])

        # Agentic loop - handle tool calls
        response_text = self._run_agent_loop(messages)

        # Save assistant response
        assistant_message = Message(role="assistant", content=response_text)
        self.conversation_history.append(assistant_message)
        self.memory.save_message(self.session_id, assistant_message)

        # Background memory extraction (non-blocking for performance)
        self._extract_and_save_memories(user_input, response_text)
        self._update_user_profile(user_input, response_text)

        return response_text

    def _run_agent_loop(self, messages: list[dict]) -> str:
        """Run the agentic loop, handling tool calls until a final response."""
        max_iterations = 5  # prevent infinite loops

        for _ in range(max_iterations):
            response = self.client.chat.completions.create(
                model=config.MODEL,
                messages=messages,
                tools=self.tool_schemas,
                tool_choice="auto",
                max_tokens=2000,
                temperature=0.7,
            )

            choice = response.choices[0]

            # No tool calls — we have the final response
            if choice.finish_reason == "stop" or not choice.message.tool_calls:
                return choice.message.content or ""

            # Process tool calls
            tool_calls = choice.message.tool_calls
            # Convert the OpenAI message object to a dict for subsequent API calls
            messages.append(choice.message.model_dump(exclude_unset=True))

            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                try:
                    tool_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    tool_args = {}

                tool_result = self._execute_tool(tool_name, tool_args)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result,
                })

        # Fallback: get response without tools after max iterations
        fallback_response = self.client.chat.completions.create(
            model=config.MODEL,
            messages=messages,
            max_tokens=2000,
            temperature=0.7,
        )
        return fallback_response.choices[0].message.content or ""

    def chat_stream(self, user_input: str) -> Iterator[str]:
        """
        Send a message and stream the response token by token.

        Args:
            user_input: The user's message

        Yields:
            Response text chunks
        """
        # Save user message
        user_message = Message(role="user", content=user_input)
        self.conversation_history.append(user_message)
        self.memory.save_message(self.session_id, user_message)
        self.memory.increment_interaction_count()

        # Search for relevant memories
        relevant_memories = self.memory.search_memories(user_input)

        # Build messages
        system_prompt = self._build_system_prompt(relevant_memories)
        messages = [{"role": "system", "content": system_prompt}]
        history_to_include = self.conversation_history[-config.MAX_HISTORY:]
        messages.extend([m.to_dict() for m in history_to_include])

        # Handle tool calls first (non-streaming), then stream final response
        tool_messages = self._handle_tool_calls(messages)
        if tool_messages:
            messages = tool_messages

        # Stream the final response
        full_response = ""
        stream = self.client.chat.completions.create(
            model=config.MODEL,
            messages=messages,
            stream=True,
            max_tokens=2000,
            temperature=0.7,
        )

        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                full_response += delta.content
                yield delta.content

        # Save and process the complete response
        assistant_message = Message(role="assistant", content=full_response)
        self.conversation_history.append(assistant_message)
        self.memory.save_message(self.session_id, assistant_message)
        self._extract_and_save_memories(user_input, full_response)
        self._update_user_profile(user_input, full_response)

    def _handle_tool_calls(self, messages: list[dict]) -> list[dict] | None:
        """
        Handle any tool calls needed before streaming the response.
        Returns updated messages if tools were called, None otherwise.
        """
        response = self.client.chat.completions.create(
            model=config.MODEL,
            messages=messages,
            tools=self.tool_schemas,
            tool_choice="auto",
            max_tokens=500,
            temperature=0.1,
        )

        choice = response.choices[0]
        if not choice.message.tool_calls:
            return None

        messages = messages.copy()
        # Convert the OpenAI message object to a dict for subsequent API calls
        messages.append(choice.message.model_dump(exclude_unset=True))

        for tool_call in choice.message.tool_calls:
            tool_name = tool_call.function.name
            try:
                tool_args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                tool_args = {}

            tool_result = self._execute_tool(tool_name, tool_args)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result,
            })

        return messages

    def remember(self, content: str, memory_type: str = "fact", importance: float = 0.7) -> str:
        """
        Explicitly add a memory to JARVIS's long-term storage.

        Args:
            content: What to remember
            memory_type: Type of memory (fact, preference, work_style, context, event)
            importance: Importance score (0.0-1.0)

        Returns:
            Confirmation message
        """
        memory = Memory(
            id=None,
            content=content,
            memory_type=memory_type,
            importance=importance,
        )
        mem_id = self.memory.save_memory(memory)
        return f"✅ Memory saved (ID: {mem_id}): {content}"

    def recall(self, query: str) -> str:
        """
        Search JARVIS's memory for relevant information.

        Args:
            query: What to search for

        Returns:
            Formatted memory results
        """
        memories = self.memory.search_memories(query, limit=10)
        if not memories:
            return f"No memories found for: '{query}'"

        lines = [f"🧠 Memories matching '{query}':\n"]
        for mem in memories:
            lines.append(
                f"  [{mem.memory_type}] (importance: {mem.importance:.1f}) {mem.content}"
            )
        return "\n".join(lines)

    def get_memory_stats(self) -> dict:
        """Get statistics about stored memories."""
        return self.memory.get_memory_stats()

    def new_session(self) -> str:
        """Start a new conversation session."""
        # Save current session
        self.memory.save_session(self.session_id)
        # Create new session
        self.session_id = str(uuid.uuid4())
        self.conversation_history = []
        return self.session_id

    @property
    def user_name(self) -> str:
        """Get the user's name if known."""
        return self.user_profile.name or config.USER_NAME or "there"
