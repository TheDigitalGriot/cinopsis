import os,glob,json,re
home=os.path.expanduser("~")
sd=os.path.join(os.environ["TEMP"],"cinopsis_sync")
def rd(n):return [x for x in open(os.path.join(sd,n),encoding="utf-8").read().strip().split(",") if len(x)==11]
cur={"AI News":("PLkshWCz_wLN_NvwkHTNG6X-I5ctGueHdy",rd("ainews.txt")),
     "Idea Systems":("PLkshWCz_wLN_d9MF_D-pjlqWFuH8kt5_-",rd("idea_full.txt")),
     "3D PixelArt style":("PLkshWCz_wLN_loLw-KouBIEnEZUGtJyue",rd("3d_full.txt"))}
seen=json.load(open(os.path.join(home,"GriotApps","Cinopsis","data","playlist_seen.json"),encoding="utf-8"))
global_seen=set()
for v in seen.values():
    for i in v: global_seen.add(i)
cachedirs=[os.path.join(home,"GriotApps","Cinopsis","data"),
           os.path.join(home,".claude","plugins","marketplaces","cinopsis","data"),
           os.path.join(home,".claude","plugins","data","cinopsis-cinopsis"),
           os.path.join(home,".claude","plugins","data","cinopsis-inline")]
trans=set(); r=re.compile(r'transcript_([\w-]{11})\.(?:json|txt)$')
for d in cachedirs:
    for root,_,files in (os.walk(d) if os.path.isdir(d) else []):
        for f in files:
            m=r.search(f)
            if m:trans.add(m.group(1))
processed=global_seen|trans
# union current
uc=[]; s=set()
for name,(pid,ids) in cur.items():
    for i in ids:
        if i not in s: s.add(i); uc.append(i)
to_process=[i for i in uc if i not in processed]
# per-playlist attribution of the survivors, and what per-playlist diff would've wrongly kept
memb={}
for name,(pid,ids) in cur.items():
    for i in ids: memb.setdefault(i,[]).append(name.split()[0])
# cross-list-seen caught: videos new to their own list but in global_seen via another
per_list_new=set()
for name,(pid,ids) in cur.items():
    sset=set(seen.get(pid,[]))
    for i in ids:
        if i not in sset: per_list_new.add(i)
caught_by_global = [i for i in per_list_new if (i in global_seen and i not in trans)]
to_fetch=[i for i in to_process if i not in trans]
out={"global_seen":len(global_seen),"transcribed":len(trans),"processed_union":len(processed),
     "union_current":len(uc),
     "to_process(global)":len(to_process),"to_fetch":len(to_fetch),
     "extra_caught_by_global_vs_perlist":len(caught_by_global),
     "survivors_by_membership":{}}
from collections import Counter
c=Counter(tuple(sorted(set(memb[i]))) for i in to_process)
out["survivors_by_membership"]={"+".join(k):v for k,v in sorted(c.items(),key=lambda x:-x[1])}
json.dump({"to_process":to_process,"to_fetch":to_fetch},open(os.path.join(sd,"final_new.json"),"w"),indent=1)
print(json.dumps(out,indent=1))
