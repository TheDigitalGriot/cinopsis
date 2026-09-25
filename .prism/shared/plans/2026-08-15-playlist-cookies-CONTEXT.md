# implement stage — fetch_playlist private-playlist reachability (cinopsis)

One job: add cookies support to fetch_playlist so it can reach PRIVATE playlists, and document the agent-scrape fallback. Additive only. Griot plugin change: conform to cl-plugin-structure. Do NOT bump versions. Do NOT commit.

Repo: C:\Users\digit\GriotApps\cinopsis.

## Context
yt-dlp returns 0 on Gavin's private playlists unauthenticated (YouTube: "playlist does not exist"), and --cookies-from-browser chrome fails on Windows with "Failed to decrypt with DPAPI" (Chrome App-Bound Encryption, yt-dlp #10927). A cookies.txt exported from the logged-in profile + yt-dlp --cookies <file> sidesteps it. The agent-side claude-in-chrome scrape is the interactive fallback (proven pulling the private "AI News" 1,703-video playlist).

## Inputs (pull via code-intel)
- scripts/fetch_playlist.py (the fetch + yt-dlp flat-playlist call), scripts/get_transcript.py (how the transcript ladder already handles yt-dlp cookie fallbacks — reuse that pattern), scripts/_utils.py (find_ytdlp/get_env/DATA_DIR), scripts/mcp_server.py (the fetch_playlist tool), skills/cinopsis/SKILL.md, commands/playlist.md.

## Decisions (locked — do not ask)
- Add a --cookies <path> CLI flag to fetch_playlist.py, threaded into the yt-dlp flat-playlist command as --cookies <path>.
- Also auto-discover: if --cookies is absent, use env CINOPSIS_COOKIES if set, else a default DATA_DIR/cookies.txt if it exists; otherwise run without cookies (public playlists still work).
- Mirror the transcript ladder's existing cookie handling in get_transcript.py — do not invent a second style.
- Thread the cookies param through the fetch_playlist MCP tool too (optional arg).
- When a private playlist returns 0 entries and no cookies were available, print a clear hint: export a cookies.txt (Get cookies.txt LOCALLY extension) and pass --cookies, or use the agent-side Chrome scrape.
- Document the reachability options in SKILL.md (a short note) and commands/playlist.md.

## Process
1. Edit scripts/fetch_playlist.py: add --cookies, the auto-discovery, thread into the yt-dlp cmd, and the private-playlist hint on 0 entries.
2. Update the fetch_playlist MCP tool in scripts/mcp_server.py to accept + pass an optional cookies path.
3. Add the reachability note to skills/cinopsis/SKILL.md and commands/playlist.md.
4. cl-plugin-structure validate . + fix minimally.

## Success criteria
- python scripts/fetch_playlist.py --help shows --cookies
- from scripts/, python -c "import fetch_playlist" clean
- mcp_server.py --list-tools still includes fetch_playlist
- git status shows only the intended edits; no downstream changes; nothing committed
- claude plugin validate . passes

## Heartbeat
Append one timestamped line to .prism/playlist-cookies-progress.txt per step. Tokens: cookies-start, edited-fetch-playlist, wired-mcp-tool, edited-surfaces, ran-cl-plugin-structure, selfcheck-pass, selfcheck-fail, DONE files=N. On block: BLOCKED-<short reason> then stop.