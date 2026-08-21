import os,json,time,shutil,subprocess,urllib.request
import websocket
home=os.path.expanduser("~")
UD=os.path.join(home,"AppData","Local","Google","Chrome","User Data")
tmp=os.path.join(os.environ["TEMP"],"cin_cdp_ud")
if os.path.isdir(tmp): shutil.rmtree(tmp,ignore_errors=True)
os.makedirs(os.path.join(tmp,"Default","Network"),exist_ok=True)
shutil.copy2(os.path.join(UD,"Local State"),os.path.join(tmp,"Local State"))
src=os.path.join(UD,"Profile 1")
for rel in ["Network\\Cookies","Preferences","Secure Preferences"]:
    s=os.path.join(src,rel); d=os.path.join(tmp,"Default",rel)
    os.makedirs(os.path.dirname(d),exist_ok=True)
    if os.path.exists(s):
        try: shutil.copy2(s,d)
        except Exception as e: print("copy warn",rel,e)
chrome=r"C:\Program Files\Google\Chrome\Application\chrome.exe"
proc=subprocess.Popen([chrome,f"--user-data-dir={tmp}","--remote-debugging-port=9222",
   "--remote-allow-origins=*","--no-first-run","--no-default-browser-check",
   "--disable-extensions","--headless=new","about:blank"])
wsurl=None
for _ in range(30):
    time.sleep(0.7)
    try:
        v=json.load(urllib.request.urlopen("http://127.0.0.1:9222/json/version",timeout=3))
        wsurl=v.get("webSocketDebuggerUrl")
        if wsurl: break
    except Exception: pass
if not wsurl:
    print("NO_WS"); 
    subprocess.run(["taskkill","/F","/IM","chrome.exe"],capture_output=True); raise SystemExit
time.sleep(1.5)
ws=websocket.create_connection(wsurl,timeout=20,header=["Origin: http://127.0.0.1:9222"],max_size=None)
ws.send(json.dumps({"id":1,"method":"Network.getAllCookies"}))
cookies=[]
for _ in range(60):
    m=json.loads(ws.recv())
    if m.get("id")==1:
        cookies=m.get("result",{}).get("cookies",[]); break
ws.close()
subprocess.run(["taskkill","/F","/IM","chrome.exe"],capture_output=True)
want=[c for c in cookies if any(h in c["domain"] for h in ("youtube.com","google.com","googlevideo.com"))]
auth=sorted(set(c["name"] for c in want if c["name"] in ("SAPISID","__Secure-3PSID","SID","LOGIN_INFO","HSID","SSID","APISID","__Secure-1PSID")))
emptyvals=sum(1 for c in want if not c.get("value"))
lines=["# Netscape HTTP Cookie File",""]
for c in want:
    dom=c["domain"]; flag="TRUE" if dom.startswith(".") else "FALSE"
    sec="TRUE" if c.get("secure") else "FALSE"
    exp=int(c.get("expires") or 0); exp=exp if exp>0 else 0
    lines.append("\t".join([dom,flag,c.get("path","/"),sec,str(exp),c["name"],c.get("value","")]))
txt="\n".join(lines)+"\n"
dests=[os.path.join(home,"GriotApps","Cinopsis","data","cookies.txt"),
       os.path.join(home,".claude","plugins","marketplaces","cinopsis","data","cookies.txt"),
       os.path.join(home,".claude","plugins","data","cinopsis-cinopsis","cookies.txt")]
for d in dests:
    os.makedirs(os.path.dirname(d),exist_ok=True); open(d,"w",encoding="utf-8").write(txt)
shutil.rmtree(tmp,ignore_errors=True)
print(json.dumps({"total":len(cookies),"yt_google":len(want),"empty_values":emptyvals,"auth":auth}))
