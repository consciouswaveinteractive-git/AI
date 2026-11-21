import pathlib,os,json,urllib.request,http.cookiejar
p=pathlib.Path(os.environ['LOCALAPPDATA'])/'MultiVibe-Codex-Pilot'
op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
op.open(urllib.request.Request('http://localhost:1455/admin/session',data=json.dumps({'token':(p/'admin-password.txt').read_text()}).encode(),headers={'Content-Type':'application/json'}),timeout=5).close()
for x in ['session','accounts','config','dashboard/models','model-aliases','settings','proxy-api-keys','application-policies','modules']:
    try:
        r=op.open('http://localhost:1455/admin/'+x,timeout=5)
        b=r.read()
        try: json.loads(b); kind='JSON'
        except Exception: kind='NOT_JSON'
        print(x,r.status,r.headers.get('Content-Type'),kind)
    except Exception as e: print(x,type(e).__name__)
