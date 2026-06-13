<div align="center">

# 📺 YouTube Video Digest

**Let Claude recap your YouTube subscriptions for you**

[![Claude Code Plugin](https://img.shields.io/badge/Claude%20Code-Plugin%20v2.0-blueviolet?style=for-the-badge&logo=anthropic)](https://claude.ai/code)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

---

*Auto-browse subscribed channels, fetch transcripts, generate summary reports — never miss a video worth watching*

</div>

## ✨ Features

- 🔍 **Smart Fetching** — Get latest videos from subscribed channels (any topic)
- 📝 **Transcript Extraction** — Auto-download video subtitles (including auto-generated)
- 📊 **Report Generation** — Generate structured Markdown reports
- 🔀 **Multi-Video Comparison** — Cross-video analysis with interactive dashboard
- 🖼️ **Frame Screenshots** — Capture video frames at any timestamp via ffmpeg
- 💬 **Agentic Chat** — Ask follow-up questions about compared videos (Claude subscription, Anthropic API key, or any local/custom OpenAI-compatible model)
- 📂 **Session History** — Browse and revisit past comparison sessions
- ⚡ **Slash Commands** — `/digest`, `/compare`, `/fetch` for zero-overhead invocation
- 🛡️ **Compaction Survival** — Session progress checkpoints survive long-context compaction
- 🖥️ **Claude Cowork Support** — Runs on Cowork via a local MCP server with an auto-bootstrapping venv (no terminal setup)
- 🔌 **Bundled ffmpeg** — Frame capture works out of the box via `imageio-ffmpeg`; no system install required

## 🚀 Quick Start

### Installation

**Option 1: Install via Claude Code (Recommended)**

```bash
claude install gh:TheDigitalGriot/ytmp4-ai-digest
```

**Option 2: Manual Clone**

```bash
git clone https://github.com/TheDigitalGriot/ytmp4-ai-digest.git
```

**Install Dependencies**

```bash
pip install -r requirements.txt
```

> Frame capture uses a **bundled `ffmpeg`** (the `imageio-ffmpeg` pip wheel) — no system install required. A system `ffmpeg` on PATH is used automatically if one is present.
>
> **On Claude Cowork**, you don't run `pip` at all — the MCP server auto-creates a virtual-env in `${CLAUDE_PLUGIN_DATA}` and installs dependencies on first use.

### Configure Channels

Edit `data/channels.json` to add your subscribed YouTube channels:

```json
{
  "channels": [
    {"name": "Two Minute Papers", "id": "UCbfYPyITQ-7l4upoX8nvctg"},
    {"name": "AI Explained", "id": "UCNJ1Ymd5yFuUPtn21xtRbbw"},
    {"name": "Yannic Kilcher", "id": "UCZHmQk67mN31gbHey6BVyNw"}
  ]
}
```

> 💡 **How to find Channel ID?** Open a YouTube channel page — the URL format is `youtube.com/channel/{CHANNEL_ID}`

## 🖥️ Claude Cowork Support

The plugin runs on both **Claude Code** and **Claude Cowork** from the same codebase.

- **Claude Code** keeps everything: slash commands, scripts, and hooks are unchanged.
- **Claude Cowork** (which has no Bash tool) uses a **local-stdio MCP server** that exposes the same operations as tools: `fetch_videos`, `get_transcript`, `compare_videos`, `launch_viewer`, `capture_frame`. Both surfaces share the same Python core and the same dashboard.

On first use, the MCP server **auto-bootstraps a virtual-env** in `${CLAUDE_PLUGIN_DATA}` and installs dependencies — no terminal, no manual `pip`.

### Choosing the chat model (⚙ Settings)

The in-viewer chat is powered by a pluggable provider, selectable in the dashboard's **⚙ Settings** panel (persisted to `${CLAUDE_PLUGIN_DATA}/settings.json`):

| Provider | Auth | Notes |
|----------|------|-------|
| **Claude — subscription** *(default)* | local `claude` CLI | No API key, no per-token cost (mirrors quiz-assistant) |
| **Claude — API key** | Anthropic API key | Fallback when the CLI isn't available (e.g. on a Cowork-only machine) |
| **Local / custom** | OpenAI-compatible endpoint | Point `base_url` + `model` at Ollama, llama.cpp, vLLM, LM Studio, or your own fine-tuned models |

Keys and the default endpoint can also be supplied at install time via the plugin's `userConfig` prompts.

## 💬 Usage

### Slash Commands (fastest — no skill loading overhead)

```
/digest <url>                    — Summarize a single video + launch viewer
/compare <url1> <url2> [url3...] — Cross-video analysis + launch viewer
/fetch --days 3 --keyword "AI"   — Fetch recent videos from subscribed channels
```

### Natural Language

```
User: What are the latest videos?
User: Show me recent Blender tutorials
User: Summarize this video: https://youtube.com/watch?v=...
User: Compare these videos: URL1, URL2, URL3
User: What do they disagree on?
User: Create a digest of this week's coding content
```

### Agent Routing

Three specialized agents handle requests automatically:

| Agent | Color | Model | Use For |
|-------|-------|-------|---------|
| `video-fetcher` | 🟢 Green | Haiku | Fetching video lists, channel queries |
| `digest-writer` | 🩵 Cyan | Sonnet | Single video summaries, batch digests |
| `video-comparator` | 🟣 Magenta | Opus (1M ctx) | Multi-video comparison, deep analysis |

## 📖 Manual Script Usage

```bash
# 1. Fetch videos from the past 7 days (any topic)
python scripts/fetch_videos.py --days 7 --all
python scripts/fetch_videos.py --days 7 --keyword "blender"

# 2. Get transcript for a specific video
python scripts/get_transcript.py --video-id dQw4w9WgXcQ

# 3. Generate Markdown report
python scripts/generate_report.py --video-id dQw4w9WgXcQ --summary "Your summary here"

# 4. Compare multiple videos
python scripts/compare_videos.py --urls URL1 URL2 URL3

# 5. Launch the interactive comparison viewer
python scripts/compare_server.py --port 5123

# 6. Capture a frame screenshot at a specific timestamp
python scripts/capture_frames.py --video-id dQw4w9WgXcQ --timestamps 60,120,300
```

## 📁 Directory Structure

```
ytmp4-ai-digest/
├── .claude-plugin/
│   ├── plugin.json            # Plugin manifest (v2.0.0)
│   └── marketplace.json       # Marketplace config
├── agents/
│   ├── digest-writer.md       # Sonnet agent — single video + batch digests
│   ├── video-fetcher.md       # Haiku agent — lightweight fetching
│   └── video-comparator.md    # Opus[1M] agent — cross-video analysis
├── commands/
│   ├── digest.md              # /digest <url> — zero-overhead single video
│   ├── compare.md             # /compare <urls> — zero-overhead comparison
│   └── fetch.md               # /fetch [options] — zero-overhead fetch
├── skills/
│   └── ytmp4-ai-digest/
│       ├── SKILL.md           # Skill definition + routing
│       └── references/
│           └── comparison-schema.md  # comparison_data.json field reference
├── output-styles/
│   └── digest-format.md       # Core Takeaway / Key Points / Why It Matters
├── hooks/
│   └── hooks.json             # SessionStart + PreCompact/PostCompact hooks
├── scripts/
│   ├── fetch_videos.py        # Fetch channel video list
│   ├── get_transcript.py      # Download video transcripts
│   ├── generate_report.py     # Generate Markdown reports
│   ├── digest_all.py          # Batch digest generation
│   ├── compare_videos.py      # Multi-video comparison orchestrator
│   ├── capture_frames.py      # Frame screenshot capture (ffmpeg)
│   ├── compare_server.py      # Flask server for interactive viewer
│   ├── save-session-state.py  # PreCompact hook — persist session progress
│   └── restore-session-state.py  # PostCompact hook — recover session state
├── viewer/
│   └── viewer.html            # Self-contained comparison dashboard
├── tests/
│   ├── test_capture_frames.py
│   ├── test_compare_videos.py
│   ├── test_compare_server.py
│   └── test_session_persistence.py
├── requirements.txt
└── data/
    ├── channels.json          # Subscribed channels config
    ├── videos.json            # Video list cache (auto-generated)
    └── sessions/              # Comparison session history (auto-generated)
```

## 📋 Output Examples

### Single Video Digest

```
**Core Takeaway**
GPT-4o's voice mode latency drop to ~300ms closes the gap with human response times,
making real-time conversation feel natural rather than transactional. The key
architectural change is end-to-end audio processing — bypassing the ASR→LLM→TTS pipeline.

**Key Points**
- Latency reduced from ~2.8s (GPT-4) to ~320ms average in voice mode
- End-to-end audio model eliminates transcription error accumulation
- Emotion and tone preserved across turns — previous models flattened prosody
- Context window extended to 128K, enabling longer reference conversations

**Why It Matters**
First voice AI model where interruption and turn-taking feel natural enough for
professional use cases — customer service, tutoring, accessibility applications.
```

### Video Comparison Dashboard

The interactive viewer provides three views:

- **Dashboard** — Stats overview, unified summary, topic coverage map, video cards, key moments grid
- **By Topic** — Accordion layout grouping all videos by shared themes, with per-video quotes and timestamps
- **By Video** — Split panel with video selector, topic tags, clickable timeline for on-demand frame capture

The viewer also includes a **chat widget** for asking follow-up questions about compared videos and a **session history panel** for browsing past comparisons.

## 🔧 Requirements

| Dependency | Version | Description |
|------------|---------|-------------|
| Python | 3.10+ | Runtime (3.10+ required for the MCP server + Agent SDK chat) |
| yt-dlp | latest | YouTube video/subtitle download |
| Flask | latest | Local server for comparison viewer |
| imageio-ffmpeg | latest | Bundled ffmpeg for frame capture (no system install) |
| mcp | latest | Local-stdio MCP server (Cowork bridge) |
| claude-agent-sdk | latest | In-viewer chat via Claude subscription |
| anthropic / requests | latest | API-key and local/custom chat providers |

> On Cowork these are installed automatically into a per-plugin venv. For the Claude Code slash-command path, run `pip install -r requirements.txt`.

## 📋 What's New in 2.1.0

- **Claude Cowork support** — a local-stdio MCP server (`.mcp.json`) exposes `fetch_videos`, `get_transcript`, `compare_videos`, `launch_viewer`, and `capture_frame` so the plugin works on Cowork, which has no Bash tool. Claude Code is unchanged.
- **Self-bootstrapping venv** — first MCP use builds a venv in `${CLAUDE_PLUGIN_DATA}` and installs dependencies with zero terminal action.
- **Real in-viewer chat** — `/api/chat` is now wired to a streaming, pluggable provider layer (Claude subscription via the Agent SDK, Anthropic API-key fallback, or any OpenAI-compatible local/custom endpoint).
- **⚙ Settings panel** — choose the chat provider/model in the dashboard; persisted to `${CLAUDE_PLUGIN_DATA}/settings.json`. Local models like Gemma/Kimi are a drop-in config row.
- **Bundled ffmpeg** — frame capture uses `imageio-ffmpeg`; no system ffmpeg required.

## 📋 What's New in 2.0.0

- **Slash commands** — `/digest`, `/compare`, `/fetch` bypass skill loading for the three most common operations, reducing invocation overhead significantly
- **Agent color identities** — digest-writer (🩵 cyan), video-fetcher (🟢 green), video-comparator (🟣 magenta)
- **Opus 4.8 + 1M context** — video-comparator upgraded to `opus[1m]` with `xhigh` effort for deep cross-video reasoning; loads all transcripts simultaneously before analyzing
- **Compaction survival** — `PreCompact`/`PostCompact` hooks write and restore session progress to disk; long comparison sessions recover cleanly after context window compaction
- **Digest output style** — centralized `digest-format` style eliminates the triplication of format rules across skill and agent files
- **Schema reference** — `comparison_data.json` field reference extracted to a single canonical file; both agents point to it instead of duplicating inline JSON
- **Manifest fixes** — removed invalid `owner.url` field from marketplace.json; added discovery keywords to plugin.json

## 🤝 Contributing

Issues and Pull Requests are welcome!

## 📄 License

[MIT License](LICENSE)

---

<div align="center">

**If you find this project helpful, please give it a ⭐ Star!**

</div>
