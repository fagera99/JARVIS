# JARVIS — AI Agent with Iron Memory 🧠

**JARVIS** is a powerful, fully-featured AI agent that acts as your personal "live brain". It remembers everything about you, understands your work style, and can perform real tasks — from searching the web to executing code.

> _"انا مش بس بتكلمك — أنا بفهمك وبفتكر كل حاجه عنك."_
> _"I'm not just talking to you — I understand you and remember everything about you."_

---

## ✨ Features

### 🧠 Iron Memory
- **Persistent long-term memory** stored in a local SQLite database
- Automatically extracts and stores important facts from every conversation
- Remembers your name, preferences, work style, ongoing projects, and more
- Memories persist across all sessions — JARVIS never forgets

### 🤖 True Intelligence
- Powered by **GPT-4o** (or any OpenAI model)
- Understands Arabic (including Egyptian dialect) and English
- Reads between the lines — understands what you *actually* want
- References memories naturally in conversation

### 🛠️ Full Tool Suite
| Tool | Description |
|------|-------------|
| 🔍 **Web Search** | Real-time web search via DuckDuckGo |
| 🌐 **Web Fetch** | Read and extract content from any URL |
| 🐍 **Code Executor** | Execute Python code safely |
| 🧮 **Calculator** | Full math: algebra, trig, stats, and more |
| 📁 **File Manager** | Read, write, list, and manage files |
| 🕐 **System Info** | Current date, time, and system information |

### 👤 User Profile Learning
- Learns your name automatically
- Tracks your work style and habits
- Remembers your preferences
- Builds a profile that grows with every interaction

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/fagera99/JARVIS.git
cd JARVIS
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
```

Edit `.env` and set your OpenAI API key:

```env
OPENAI_API_KEY=sk-your-key-here
```

### 3. Run JARVIS

```bash
python main.py
```

---

## 💬 Usage

### Talking to JARVIS

Just type naturally — in English or Arabic:

```
You: ايه اللي بنشتغل عليه دلوقتي؟
JARVIS: على حسب اللي قلتلي عنه من قبل، انت شغال على...

You: Search for the latest news about AI agents
JARVIS: 🔍 Searching the web for you...
```

### Special Commands

| Command | Description |
|---------|-------------|
| `/help` | Show help menu |
| `/memory` | Show memory statistics |
| `/recall <query>` | Search your memories |
| `/remember <text>` | Explicitly save something to memory |
| `/profile` | Show your user profile |
| `/history` | Show current session history |
| `/new` | Start a new conversation session |
| `/clear` | Clear the screen |
| `/exit` | Exit JARVIS |

---

## 🗂️ Project Structure

```
JARVIS/
├── main.py                    # Entry point
├── requirements.txt           # Python dependencies
├── .env.example               # Configuration template
├── jarvis/
│   ├── agent.py               # Core AI agent (LLM + memory + tools)
│   ├── cli.py                 # Interactive CLI interface
│   ├── config.py              # Configuration management
│   ├── memory/
│   │   ├── memory_manager.py  # Persistent memory system (SQLite)
│   │   └── models.py          # Data models (Message, Memory, UserProfile)
│   └── tools/
│       ├── web_search.py      # Web search & fetch
│       ├── code_executor.py   # Safe Python code execution
│       ├── file_manager.py    # File system operations
│       ├── calculator.py      # Mathematical calculations
│       └── system_info.py     # Date, time, system info
└── tests/
    ├── test_memory.py         # Memory system tests
    └── test_tools.py          # Tool tests
```

---

## ⚙️ Configuration

All settings are in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | *(required)* | Your OpenAI API key |
| `JARVIS_MODEL` | `gpt-4o` | OpenAI model to use |
| `JARVIS_MEMORY_DB` | `~/.jarvis/memory.db` | Memory database path |
| `JARVIS_MAX_HISTORY` | `20` | Messages to include in context |
| `JARVIS_MAX_MEMORIES` | `5` | Memories to retrieve per query |
| `JARVIS_USER_NAME` | *(auto-detected)* | Your name |
| `JARVIS_LANGUAGE` | `auto` | `ar`, `en`, or `auto` |
| `JARVIS_ENABLE_WEB_SEARCH` | `true` | Enable web search |
| `JARVIS_ENABLE_CODE_EXEC` | `true` | Enable code execution |
| `JARVIS_ENABLE_FILE_OPS` | `true` | Enable file operations |

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

---

## 🔒 Privacy & Security

- All memories are stored **locally** on your machine (`~/.jarvis/memory.db`)
- No data is sent anywhere except your OpenAI API calls
- Web search uses DuckDuckGo (no tracking)
- Code execution runs in a sandboxed environment with restricted builtins

---

## 📝 Memory Architecture

JARVIS uses a three-tier memory system:

1. **Short-term memory**: The active conversation context (last N messages)
2. **Long-term memories**: Extracted facts, preferences, events stored in SQLite
3. **User profile**: Continuously updated model of who you are and how you work

Every conversation automatically:
- Extracts important facts and stores them as long-term memories
- Updates your user profile with new preferences and patterns
- Uses semantic keyword search to find relevant memories for each query
