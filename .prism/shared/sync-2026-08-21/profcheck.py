import sqlite3,os,tempfile,shutil
base=os.path.join(os.environ["LOCALAPPDATA"],"Google","Chrome","User Data")
prof={"Default":"Digital","Profile 1":"Gavin","Profile 4":"Kromanti"}
for folder,name in prof.items():
    for rel in ("Network\\Cookies","Cookies"):
        p=os.path.join(base,folder,rel)
        if os.path.exists(p):
            try:
                tmp=os.path.join(tempfile.gettempdir(),f"ck_{folder.replace(' ','_')}.db")
                shutil.copy2(p,tmp)  # may fail if locked
                con=sqlite3.connect(f"file:{tmp}?immutable=1",uri=True)
            except Exception:
                con=sqlite3.connect(f"file:{p}?immutable=1&mode=ro",uri=True)
            try:
                cur=con.execute("select host_key,name,last_access_utc from cookies where host_key like '%youtube.com' and name in ('SAPISID','__Secure-3PSID','SID','LOGIN_INFO')")
                rows=cur.fetchall()
                names=sorted(set(r[1] for r in rows))
                la=max([r[2] for r in rows],default=0)
                print(f"{folder} ({name}): youtube-auth cookies={names} lastAccess={la}")
            except Exception as e:
                print(f"{folder} ({name}): ERR {e}")
            con.close()
            break
    else:
        print(f"{folder} ({name}): no cookies db")
