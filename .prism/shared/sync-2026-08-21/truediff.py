import os,glob,json,re
home=os.path.expanduser("~")
sd=os.path.join(os.environ["TEMP"],"cinopsis_sync")
def rd(n):return [x for x in open(os.path.join(sd,n),encoding="utf-8").read().strip().split(",") if len(x)==11]
cur={"AI News":("PLkshWCz_wLN_NvwkHTNG6X-I5ctGueHdy",rd("ainews.txt")),
     "Idea Systems":("PLkshWCz_wLN_d9MF_D-pjlqWFuH8kt5_-",rd("idea_full.txt")),
     "3D PixelArt style":("PLkshWCz_wLN_loLw-KouBIEnEZUGtJyue",rd("3d_full.txt"))}
seen=json.load(open(os.path.join(home,"GriotApps","Cinopsis","data","playlist_seen.json"),encoding="utf-8"))
# transcribed cache across dev repo + marketplace + plugin data
cachedirs=[os.path.join(home,"GriotApps","Cinopsis","data"),
           os.path.join(home,".claude","plugins","marketplaces","cinopsis","data"),
           os.path.join(home,".claude","plugins","data","cinopsis-cinopsis"),
           os.path.join(home,".claude","plugins","data","cinopsis-inline")]
trans=set()
r=re.compile(r'transcript_([\w-]{11})\.(?:json|txt)$')
for d in cachedirs:
    for root,_,files in os.walk(d) if os.path.isdir(d) else []:
        for f in files:
            m=r.search(f)
            if m:trans.add(m.group(1))
res={}; survivors={}; boundary={}
allnew=[]
for name,(pid,ids) in cur.items():
    s=set(seen.get(pid,[]))
    new=[i for i in ids if i not in s]
    # boundary check for AI (is the diff a clean top-prefix?)
    firstseen=next((k for k,i in enumerate(ids) if i in s),None)
    boundary[name]={"len":len(ids),"first_seen_pos":firstseen,"new_count":len(new)}
    res[name]=new
    for i in new: allnew.append(i)
uniq=[]; seenset=set()
for i in allnew:
    if i not in seenset:seenset.add(i);uniq.append(i)
to_fetch=[i for i in uniq if i not in trans]
already=[i for i in uniq if i in trans]
out={"transcribed_cache":len(trans),
     "new_per_playlist":{k:len(v) for k,v in res.items()},
     "union_new":len(uniq),"already_transcribed":len(already),"to_fetch":len(to_fetch),
     "boundary":boundary}
json.dump({"to_fetch":to_fetch,"per_playlist_new":res,"already":already},
          open(os.path.join(sd,"true_new.json"),"w"),indent=1)
print(json.dumps(out,indent=1))
