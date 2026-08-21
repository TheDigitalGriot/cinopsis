import os,json
sd=os.path.join(os.environ["TEMP"],"cinopsis_sync")
d=json.load(open(os.path.join(sd,"final_new.json")))
ids=d["to_fetch"]
open(os.path.join(sd,"ids177.txt"),"w").write("\n".join(ids))
print("wrote",len(ids))
