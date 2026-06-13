#!/usr/bin/env python3
"""Flask server for the video comparison viewer with on-demand screenshot API."""
import argparse
import json
import os
import webbrowser
from pathlib import Path

from flask import Flask, jsonify, request, send_file, abort, Response, stream_with_context

from capture_frames import capture_frame, extract_video_id


def create_app(data_dir=None):
    """Create and configure the Flask app."""
    from _utils import canonical_data_dir
    data_dir = Path(data_dir) if data_dir else canonical_data_dir()
    sessions_dir = data_dir / "sessions"
    plugin_root = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", Path(__file__).parent.parent))
    viewer_path = plugin_root / "viewer" / "viewer.html"

    app = Flask(__name__)
    app.json.ensure_ascii = False

    @app.route("/")
    def index():
        if viewer_path.exists():
            return send_file(viewer_path)
        return "<h1>cinopsis Video Comparison</h1><p>viewer.html not found</p>", 200

    @app.route("/api/sessions")
    def get_sessions():
        index_file = sessions_dir / "index.json"
        if not index_file.exists():
            return jsonify([])
        with open(index_file, encoding="utf-8") as f:
            return jsonify(json.load(f))

    @app.route("/api/session/<session_id>")
    def get_session(session_id):
        index_file = sessions_dir / "index.json"
        if not index_file.exists():
            abort(404)

        with open(index_file, encoding="utf-8") as f:
            index = json.load(f)

        dir_name = None
        for entry in index:
            if entry["id"] == session_id:
                dir_name = entry["dir_name"]
                break

        if not dir_name:
            abort(404)

        data_file = sessions_dir / dir_name / "comparison_data.json"
        if not data_file.exists():
            abort(404)

        with open(data_file, encoding="utf-8") as f:
            return jsonify(json.load(f))

    @app.route("/api/screenshot", methods=["POST"])
    def take_screenshot():
        body = request.get_json()
        if not body or "video_id" not in body or "timestamp" not in body:
            return jsonify({"error": "video_id and timestamp required"}), 400

        video_id = extract_video_id(body["video_id"])
        timestamp = int(body["timestamp"])

        frames_dir = data_dir / "frames"
        b64 = capture_frame(video_id, timestamp, frames_dir)

        if b64:
            return jsonify({"video_id": video_id, "timestamp": timestamp, "screenshot_base64": b64})
        return jsonify({"error": "Failed to capture frame"}), 500

    def _session_data(session_id):
        """Load comparison_data.json for a session id, or None."""
        index_file = sessions_dir / "index.json"
        if not session_id or not index_file.exists():
            return None
        with open(index_file, encoding="utf-8") as f:
            index = json.load(f)
        entry = next((e for e in index if e["id"] == session_id), None)
        if not entry:
            return None
        data_file = sessions_dir / entry["dir_name"] / "comparison_data.json"
        if not data_file.exists():
            return None
        with open(data_file, encoding="utf-8") as f:
            return json.load(f)

    def _chat_context(session_id):
        """Build the system context for the chat from a session's analysis + transcripts."""
        parts = [
            "You are an assistant helping a user understand and compare YouTube videos.",
            "Answer using the analysis and transcript excerpts below. Be concise and specific.\n",
        ]
        data = _session_data(session_id)
        if not data:
            parts.append("(No specific session is loaded.)")
            return "\n".join(parts)
        analysis = data.get("analysis", {})
        if analysis.get("unified_summary"):
            parts.append("# Unified Summary\n" + analysis["unified_summary"] + "\n")
        topics = analysis.get("topics") or []
        if topics:
            parts.append("# Topics")
            for t in topics:
                parts.append(f"- {t.get('name','')}: {t.get('consensus','')}")
            parts.append("")
        for v in data.get("videos", []):
            parts.append(f"# Video: {v.get('title','?')} ({v.get('channel','?')}) [{v.get('id','')}]")
            dg = v.get("digest") or {}
            if dg.get("core_takeaway"):
                parts.append("Core takeaway: " + dg["core_takeaway"])
            if dg.get("key_points"):
                parts.append("Key points: " + "; ".join(dg["key_points"]))
            tr = v.get("transcript") or []
            if tr:
                text = " ".join(e.get("text", "") for e in tr)[:3000]
                parts.append("Transcript excerpt: " + text)
            parts.append("")
        return "\n".join(parts)

    @app.route("/api/chat", methods=["POST"])
    def chat():
        body = request.get_json() or {}
        question = (body.get("message") or body.get("question") or "").strip()
        if not question:
            return jsonify({"error": "message required"}), 400

        from app_settings import load_settings
        from providers import chat_stream

        settings = load_settings()
        context = _chat_context(body.get("session_id"))

        @stream_with_context
        def generate():
            for chunk in chat_stream(settings, context, question):
                yield chunk

        return Response(generate(), mimetype="text/plain; charset=utf-8")

    @app.route("/api/settings", methods=["GET", "POST"])
    def settings_route():
        from app_settings import public_settings, save_settings
        if request.method == "POST":
            return jsonify(save_settings(request.get_json() or {}))
        return jsonify(public_settings())

    def _build_video_lookup():
        """Return dict mapping video_id -> video metadata across all sessions."""
        index_file = sessions_dir / "index.json"
        if not index_file.exists():
            return {}, []
        with open(index_file, encoding="utf-8") as f:
            index = json.load(f)
        all_videos = {}
        entries = []
        for entry in index:
            data_file = sessions_dir / entry["dir_name"] / "comparison_data.json"
            if not data_file.exists():
                continue
            with open(data_file, encoding="utf-8") as f:
                data = json.load(f)
            for v in data.get("videos", []):
                vid = v.get("id")
                if vid and vid not in all_videos:
                    all_videos[vid] = v
                    entries.append({"video": v, "session_id": entry["id"], "session_title": entry["title"]})
        return all_videos, entries

    @app.route("/api/videos")
    def get_all_videos():
        """Return deduplicated list of all videos across all sessions."""
        _, entries = _build_video_lookup()
        return jsonify([{
            "id": e["video"].get("id"),
            "title": e["video"].get("title", "Unknown"),
            "channel": e["video"].get("channel", "Unknown"),
            "duration": e["video"].get("duration", ""),
            "upload_date": e["video"].get("upload_date", ""),
            "thumbnail_base64": e["video"].get("thumbnail_base64"),
            "session_id": e["session_id"],
            "session_title": e["session_title"],
        } for e in entries])

    @app.route("/api/sessions/compose", methods=["POST"])
    def compose_session():
        """Create a new session from library videos + new URLs."""
        body = request.get_json()
        if not body:
            return jsonify({"error": "Request body required"}), 400

        title = body.get("title", "")
        video_ids = body.get("video_ids", [])
        new_urls = body.get("new_urls", [])

        if not video_ids and not new_urls:
            return jsonify({"error": "Provide video_ids and/or new_urls"}), 400

        videos = []

        # Load cached videos from existing sessions
        if video_ids:
            all_videos, _ = _build_video_lookup()
            for vid in video_ids:
                if vid in all_videos:
                    videos.append(all_videos[vid])

        # Fetch new videos from URLs
        if new_urls:
            from compare_videos import parse_urls, process_video
            for url in new_urls:
                try:
                    vid_id = parse_urls([url])[0]
                    video_data = process_video(vid_id)
                    videos.append(video_data)
                except Exception as e:
                    return jsonify({"error": f"Failed to process {url}: {str(e)}"}), 500

        if not videos:
            return jsonify({"error": "No valid videos found"}), 400

        # Build and save session
        from compare_videos import build_comparison_data, save_session
        if not title:
            title = f"Comparison: {', '.join(v.get('channel', '?') for v in videos[:3])}"
            if len(videos) > 3:
                title += f" +{len(videos) - 3}"

        comparison_data = build_comparison_data(videos, title)
        save_session(comparison_data)

        return jsonify(comparison_data), 201

    @app.route("/api/session/<session_id>/add-videos", methods=["POST"])
    def add_videos(session_id):
        """Add videos to an existing session."""
        body = request.get_json()
        if not body:
            return jsonify({"error": "Request body required"}), 400

        video_ids = body.get("video_ids", [])
        new_urls = body.get("new_urls", [])

        if not video_ids and not new_urls:
            return jsonify({"error": "Provide video_ids and/or new_urls"}), 400

        new_videos = []

        # Load cached videos from library
        if video_ids:
            all_videos, _ = _build_video_lookup()
            for vid in video_ids:
                if vid in all_videos:
                    new_videos.append(all_videos[vid])

        # Fetch new videos from URLs
        if new_urls:
            from compare_videos import parse_urls, process_video
            for url in new_urls:
                try:
                    vid_id = parse_urls([url])[0]
                    video_data = process_video(vid_id)
                    new_videos.append(video_data)
                except Exception as e:
                    return jsonify({"error": f"Failed to process {url}: {str(e)}"}), 500

        if not new_videos:
            return jsonify({"error": "No valid videos found"}), 400

        # Add to existing session
        from compare_videos import add_videos_to_session
        try:
            add_videos_to_session(session_id, new_videos)
        except (FileNotFoundError, ValueError) as e:
            return jsonify({"error": str(e)}), 404

        # Return updated session data
        index_file = sessions_dir / "index.json"
        with open(index_file, encoding="utf-8") as f:
            index = json.load(f)
        entry = next((e for e in index if e["id"] == session_id), None)
        if entry:
            data_file = sessions_dir / entry["dir_name"] / "comparison_data.json"
            with open(data_file, encoding="utf-8") as f:
                return jsonify(json.load(f))

        return jsonify({"error": "Session updated but could not reload"}), 500

    return app


def main():
    parser = argparse.ArgumentParser(description="Start the video comparison viewer server")
    parser.add_argument("--port", type=int, default=5123, help="Port to serve on")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--no-open", action="store_true", help="Don't open browser automatically")
    parser.add_argument("--session", help="Session ID to open directly")
    parser.add_argument("--data-dir", default=None, help="Data dir to read sessions from (default: canonical)")
    args = parser.parse_args()

    app = create_app(data_dir=args.data_dir)

    url = f"http://{args.host}:{args.port}"
    if args.session:
        url += f"?session={args.session}"

    if not args.no_open:
        import threading
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    print(f"Serving viewer at {url}", flush=True)
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
