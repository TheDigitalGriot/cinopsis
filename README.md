<div align="center">

# 📺 YouTube Video Digest

**Let Claude recap your YouTube subscriptions for you**

[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet?style=for-the-badge&logo=anthropic)](https://claude.ai/code)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

**English** | [简体中文](./README.md)

---

*Auto-browse subscribed channels, fetch transcripts, generate summary reports — never miss a video worth watching*

</div>

## ✨ Features

- 🔍 **Smart Fetching** — Get latest videos from subscribed channels (any topic)
- 📝 **Transcript Extraction** — Auto-download video subtitles (including auto-generated)
- 📊 **Report Generation** — Generate structured Markdown reports
- 🖼️ **Thumbnail Download** — Auto-save video thumbnails
- 🔀 **Multi-Video Comparison** — Cross-video analysis with interactive dashboard
- 🖼️ **Frame Screenshots** — Capture video frames at any timestamp via ffmpeg
- 💬 **Agentic Chat** — Ask follow-up questions about compared videos
- 📂 **Session History** — Browse and revisit past comparison sessions

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

> Requires `ffmpeg` on your system PATH for frame screenshot capture. Install via `winget install Gyan.FFmpeg` or `choco install ffmpeg` (Windows), `brew install ffmpeg` (macOS), or `apt install ffmpeg` (Linux).

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

> 💡 **How to find Channel ID?** Open a YouTube channel page, the URL format is `youtube.com/channel/{CHANNEL_ID}`

### Usage

Chat with Claude Code directly:

```
User: What are the latest videos?
User: Show me recent Blender tutorials
User: Summarize the first video
User: Create a digest of this week's coding content
User: Compare these videos: URL1, URL2, URL3
User: What do they disagree on?
```

## 📖 Manual Usage

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
youtube-ai-digest/
├── .claude-plugin/
│   └── marketplace.json   # Plugin marketplace config
├── skills/
│   └── ytmp4-ai-digest/
│       └── SKILL.md       # Claude Code skill definition
├── scripts/
│   ├── fetch_videos.py    # Fetch channel video list
│   ├── get_transcript.py  # Download video transcripts
│   ├── generate_report.py # Generate Markdown reports
│   ├── digest_all.py      # Batch digest generation
│   ├── compare_videos.py  # Multi-video comparison orchestrator
│   ├── capture_frames.py  # Frame screenshot capture (ffmpeg)
│   └── compare_server.py  # Flask server for interactive viewer
├── viewer/
│   └── viewer.html        # Self-contained comparison dashboard
├── tests/
│   ├── test_capture_frames.py
│   ├── test_compare_videos.py
│   ├── test_compare_server.py
│   └── test_session_persistence.py
├── requirements.txt       # Python dependencies
├── README.md              # Documentation (Chinese)
├── README.en.md           # Documentation (English)
└── data/
    ├── channels.json      # Subscribed channels config
    ├── videos.json        # Video list cache (auto-generated)
    └── sessions/          # Comparison session history (auto-generated)
```

## 📋 Output Examples

### Single Video Report

```markdown
# Understanding GPT-4's Reasoning

![Thumbnail](thumbnail.webp)

## Video Info
- Channel: AI Explained
- Published: 2024-01-15
- Duration: 12:34
- Link: https://youtube.com/watch?v=...

## Summary
This video provides an in-depth analysis of GPT-4's reasoning capabilities...

## Transcript
[00:00] Welcome back to AI Explained...
[01:30] Today we're going to discuss...
```

### Video Comparison Dashboard

The interactive viewer provides three views:

- **Dashboard** — Stats overview, unified summary, topic coverage map, video cards, key moments grid
- **By Topic** — Accordion layout grouping all videos by shared themes, with per-video quotes and screenshots
- **By Video** — Split panel with video selector, topic tags, clickable timeline for on-demand frame capture

The viewer also includes a **chat widget** for asking follow-up questions about the compared videos and a **session history panel** for browsing past comparisons.

## 🔧 Requirements

| Dependency | Version | Description |
|------------|---------|-------------|
| Python | 3.9+ | Runtime environment |
| yt-dlp | latest | YouTube video/subtitle download |
| Flask | latest | Local server for comparison viewer |
| ffmpeg | latest | Frame screenshot capture (system binary) |

## 🤝 Contributing

Issues and Pull Requests are welcome!

## 📄 License

[MIT License](LICENSE)

---

<div align="center">

**If you find this project helpful, please give it a ⭐ Star!**

</div>
