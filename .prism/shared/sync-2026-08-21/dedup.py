import os,glob,json,re
home=os.path.expanduser("~")
data_dirs=[os.path.join(home,".claude","plugins","marketplaces","cinopsis","data"),
           os.path.join(home,".claude","plugins","data","cinopsis-cinopsis"),
           os.path.join(home,".claude","plugins","data","cinopsis-inline")]
cached=set()
idre=re.compile(r'(?:transcript|sub)_([\w-]{11})')
for d in data_dirs:
    if not os.path.isdir(d):continue
    for root,_,files in os.walk(d):
        for f in files:
            m=idre.search(f)
            if m:cached.add(m.group(1))
        for cf in glob.glob(os.path.join(root,"comparison_data.json")):
            try:
                j=json.load(open(cf,encoding="utf-8"))
                for v in j.get("videos",[]):
                    for k in ("video_id","id"):
                        if v.get(k):cached.add(v[k])
            except Exception:pass
sd=os.path.join(os.environ["TEMP"],"cinopsis_sync")
def rd(n):return [x for x in open(os.path.join(sd,n),encoding="utf-8").read().strip().split(",") if len(x)==11]
lists=[("AI News",rd("ainews.txt")),("Idea Systems",rd("idea.txt")),("3D PixelArt style",rd("pixel3d.txt"))]
master=[]; seen=set(); attribution={}
percounts={}
for name,ids in lists:
    fresh_here=0
    for i in ids:
        if i in cached: continue
        if i in seen:
            continue
        seen.add(i); master.append(i); attribution[i]=name; fresh_here+=1
    percounts[name]=fresh_here
# per-playlist cache-only counts
detail={}
for name,ids in lists:
    detail[name]={"raw":len(ids),"in_cache":sum(1 for i in ids if i in cached),
                  "net_new_attributed":percounts[name]}
out={"cached_total":len(cached),"master_net_new":len(master),"detail":detail}
json.dump({"generated":"2026-08-21","master":master,"attribution":attribution,"summary":out},
          open(os.path.join(sd,"playlist_new_2026-08-21.json"),"w",encoding="utf-8"),indent=1)
print(json.dumps(out,indent=1))
