import os,sys,time,json
repo=os.path.join(os.path.expanduser("~"),"GriotApps","Cinopsis")
os.environ["CLAUDE_PLUGIN_DATA"]=os.path.join(repo,"data")
sys.path.insert(0,os.path.join(repo,"scripts"))
from _utils import DATA_DIR
from get_transcript import fetch_transcript, save_transcript
sd=os.path.join(os.environ["TEMP"],"cinopsis_sync")
ids=[x for x in open(os.path.join(sd,"ids177.txt")).read().split() if len(x)==11]
def cached(v):return (DATA_DIR/f"transcript_{v}.json").exists()
budget=35.0; start=time.time(); done=0; fail=[]
for v in ids:
    if cached(v):continue
    if time.time()-start>budget:break
    try:
        t,lang,method=fetch_transcript(v)
    except Exception as e:
        t=None;method=str(e)[:40]
    if t: save_transcript(v,t); done+=1
    else: fail.append(v)
rem=[v for v in ids if not cached(v)]
print(json.dumps({"fetched_this_call":done,"failed_this_call":fail[:20],"cached_total":sum(1 for v in ids if cached(v)),"remaining":len(rem)}))
