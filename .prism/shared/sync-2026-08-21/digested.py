import os,glob,json,re
home=os.path.expanduser("~")
dirs=[os.path.join(home,".claude","plugins","marketplaces","cinopsis","data"),
      os.path.join(home,".claude","plugins","data","cinopsis-cinopsis"),
      os.path.join(home,".claude","plugins","data","cinopsis-inline")]
idfile=re.compile(r'(?:transcript|sub)_([\w-]{11})')
vurl=re.compile(r'(?:v=|youtu\.be/|/watch\?v=|"video_id"\s*:\s*")([\w-]{11})')
digested=set(); by={}
def add(s,src):
    digested.add(s); by[src]=by.get(src,0)+1
for d in dirs:
    if not os.path.isdir(d):continue
    for root,_,files in os.walk(d):
        for f in files:
            m=idfile.search(f)
            if m: add(m.group(1),"transcript/sub")
            if f.endswith(".md") or f=="comparison_data.json" or f.endswith(".json"):
                try:
                    txt=open(os.path.join(root,f),encoding="utf-8",errors="ignore").read()
                    for mm in vurl.findall(txt):
                        add(mm, f if f.endswith(".md") else "json/session")
                except Exception:pass
print("DIGESTED_UNIQUE",len(digested))
print("BY_SOURCE",json.dumps(by))
# check output digests
out=os.path.join(dirs[0],"output")
print("OUTPUT_DIR_EXISTS",os.path.isdir(out), (os.listdir(out) if os.path.isdir(out) else []))
open(os.path.join(os.environ["TEMP"],"cinopsis_sync","digested.txt"),"w").write(",".join(sorted(digested)))
