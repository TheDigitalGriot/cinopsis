import json,io,os,glob,sys
TEMP=r"C:\Users\digit\AppData\Local\Temp"
cat=json.load(io.open(os.path.join(os.path.dirname(__file__),"catalog_local.json"),encoding='utf-8'))
ing=set()
for p in glob.glob("data/sessions/*/comparison_data.json"):
    d=json.load(io.open(p,encoding='utf-8'))
    for v in d.get("videos",[]):
        i=v.get("id") or v.get("video_id")
        if i and not str(i).startswith("unresolved-"): ing.add(i)
# transcripts + descriptions on disk also count as "have"
have=set(ing)
for p in glob.glob("artifacts/transcripts/*"):
    b=os.path.basename(p).split('.')[0]
    if len(b)==11: have.add(b)
print("ingested (sessions):",len(ing)," + on-disk transcripts =",len(have))
def vid(x):
    if isinstance(x,str): return x
    return x.get("id") or x.get("videoId") or x.get("video_id")
out={}
for name,lst in cat.items():
    ids=[vid(x) for x in lst]
    ids=[i for i in ids if i]
    # backlog = un-ingested videos ABOVE the newest already-ingested one (newest-first order)
    first=None
    for n,i in enumerate(ids):
        if i in have: first=n; break
    front = ids[:first] if first is not None else ids
    backlog=[i for i in front if i not in have]
    out[name]={"total":len(ids),"frontier_depth":first if first is not None else len(ids),
               "backlog":len(backlog),"ids":backlog}
    print(f"{name:22s} total={len(ids):5d}  newest-ingested-at={first}  BACKLOG={len(backlog)}")
json.dump(out, io.open(os.path.join(os.path.dirname(__file__),"chip.json"),"w",encoding='utf-8'))
