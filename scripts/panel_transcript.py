#!/usr/bin/env python
"""panel_transcript.py -- fetch a YouTube transcript by reading the on-page
transcript PANEL (YouTube's internal in-browser pipeline), NOT the timedtext
endpoint. This is the ONE path that survives a residential-IP flag, because the
panel does not hit the blocked caption endpoints from our IP.

Same DOM action on every video: expand description -> Show transcript ->
read ytd-transcript-segment-renderer rows -> clean. Coded, not prompted.

Usage:
  python panel_transcript.py <video_id_or_url> [--headed] [--json OUT.json] [--timeout 40]

Exit 0 + JSON to stdout (and OUT.json if given) on success; exit 2 on failure.
"""
import sys, os, re, json, time, tempfile, argparse

def vid_of(s):
    m = re.search(r"(?:v=|youtu\.be/|/watch\?v=)([A-Za-z0-9_-]{11})", s)
    return m.group(1) if m else (s if re.fullmatch(r"[A-Za-z0-9_-]{11}", s) else None)

def build_driver(headed):
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    o = Options()
    o.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if not headed:
        o.add_argument("--headless=new")
    o.add_argument("--window-size=1400,1000")
    o.add_argument("--lang=en-US")
    o.add_argument("--mute-audio")
    o.add_argument("--no-first-run")
    o.add_argument("--no-default-browser-check")
    o.add_argument("--disable-blink-features=AutomationControlled")
    o.add_argument("--user-data-dir=" + tempfile.mkdtemp(prefix="ytpanel_"))
    o.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36")
    o.add_experimental_option("excludeSwitches", ["enable-automation"])
    return webdriver.Chrome(service=Service(), options=o)

def dismiss_consent(d):
    # fresh profile -> EU-style consent interstitial. Click reject/accept if present.
    try:
        if "consent." in d.current_url:
            d.execute_script("""
              const b=[...document.querySelectorAll('button')].find(x=>/reject all|accept all|i agree/i.test(x.textContent||x.ariaLabel||''));
              if(b) b.click();
            """)
            time.sleep(2)
    except Exception:
        pass

def open_transcript(d):
    from selenium.webdriver.common.by import By
    # 1) expand the description ("...more") so the transcript section is in the DOM
    d.execute_script("""
      const e=document.querySelector('tp-yt-paper-button#expand, #expand');
      if(e) e.click();
    """)
    time.sleep(1.2)
    # 2a) direct "Show transcript" button (lives in the expanded description section)
    clicked = d.execute_script("""
      const b=[...document.querySelectorAll('button, a, yt-button-shape button, ytd-button-renderer button')]
        .find(x=>/show transcript|transcript/i.test((x.getAttribute('aria-label')||'')+' '+(x.textContent||'')));
      if(b){ b.click(); return true; } return false;
    """)
    if not clicked:
        # 2b) fallback: kebab "More actions" -> menu item "Show transcript"
        d.execute_script("""
          const k=document.querySelector('#button-shape button[aria-label*="More actions" i], ytd-menu-renderer button[aria-label*="More" i]');
          if(k) k.click();
        """)
        time.sleep(1.0)
        clicked = d.execute_script("""
          const mi=[...document.querySelectorAll('tp-yt-paper-item, ytd-menu-service-item-renderer, yt-formatted-string')]
            .find(x=>/show transcript/i.test(x.textContent||''));
          if(mi){ mi.click(); return true; } return false;
        """)
    return bool(clicked)

def read_segments(d, timeout):
    end = time.time() + timeout
    last = -1
    # wait for segments to appear, then scroll the panel until the count stabilises
    while time.time() < end:
        n = d.execute_script("return document.querySelectorAll('ytd-transcript-segment-renderer').length;")
        if n and n == last:
            break
        last = n
        d.execute_script("""
          const p=document.querySelector('ytd-transcript-segment-list-renderer #segments-container')
              || document.querySelector('ytd-transcript-segment-list-renderer');
          if(p) p.scrollTop = p.scrollHeight;
        """)
        time.sleep(0.8)
    return d.execute_script("""
      return [...document.querySelectorAll('ytd-transcript-segment-renderer')].map(s=>({
        t:(s.querySelector('.segment-timestamp')?.textContent||'').trim(),
        text:(s.querySelector('.segment-text, yt-formatted-string.segment-text')?.textContent||'').trim()
      })).filter(x=>x.text);
    """)

def clean(segs):
    seen=set(); out=[]
    for s in segs:
        key=(s["t"], s["text"])
        if key in seen: continue
        seen.add(key); out.append(s)
    text=re.sub(r"\s+"," "," ".join(x["text"] for x in out)).strip()
    return out, text

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--json", default=None)
    ap.add_argument("--timeout", type=int, default=40)
    a=ap.parse_args()
    vid=vid_of(a.video)
    if not vid:
        print("ERR: could not parse a video id from", a.video, file=sys.stderr); sys.exit(2)
    d=build_driver(a.headed)
    try:
        d.set_page_load_timeout(45)
        d.get("https://www.youtube.com/watch?v="+vid+"&hl=en")
        dismiss_consent(d)
        d.get("https://www.youtube.com/watch?v="+vid+"&hl=en")
        time.sleep(3.5)
        if not open_transcript(d):
            print("ERR: could not open the transcript panel (no Show transcript control found)", file=sys.stderr); sys.exit(2)
        time.sleep(1.5)
        segs=read_segments(d, a.timeout)
        if not segs:
            print("ERR: transcript panel opened but no segments read", file=sys.stderr); sys.exit(2)
        segs, text = clean(segs)
        res={"id":vid,"count":len(segs),"chars":len(text),"segments":segs,"text":text}
        if a.json:
            open(a.json,"w",encoding="utf-8").write(json.dumps(res,ensure_ascii=False,indent=2))
        print(json.dumps({"id":vid,"count":len(segs),"chars":len(text),"first":segs[0] if segs else None,"last":segs[-1] if segs else None}, ensure_ascii=False))
        sys.exit(0)
    finally:
        try: d.quit()
        except Exception: pass

if __name__=="__main__":
    main()