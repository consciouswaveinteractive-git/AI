"""Two real client turns inside private pilot home; no tools or live config."""
import json,os,pathlib,secrets,subprocess,time

def probe(data, model, proxy_key, before_resume=None):
    run=data/('real-client-'+time.strftime('%Y%m%d-%H%M%S')); run.mkdir()
    home=run/'home'; home.mkdir()
    work=run/'workspace'; work.mkdir()
    config='\n'.join([
        'model = '+json.dumps(model), 'model_provider = "pilot_multivibe"',
        'model_reasoning_effort = "low"','approval_policy = "never"','sandbox_mode = "read-only"',
        '[model_providers.pilot_multivibe]','name = "Private real pilot"',
        'base_url = "http://127.0.0.1:14755/v1"','wire_api = "responses"',
        'experimental_bearer_token = '+json.dumps(proxy_key),
        'supports_websockets = false','request_max_retries = 0','stream_max_retries = 0',''])
    (home/'config.toml').write_text(config,encoding='utf-8')
    env=os.environ.copy()
    for k in list(env):
        if k.startswith(('OPENAI_','CODEX_','OAUTH_')): env.pop(k)
    env['CODEX_HOME']=str(home)
    codex=pathlib.Path(os.environ['USERPROFILE'])/'.vscode/extensions/openai.chatgpt-26.1021.22027-win32-x64/bin/windows-x86_64/codex.exe'
    nonce='PILOT_'+secrets.token_hex(6).upper()
    def invoke(label,args):
        r=subprocess.run([str(codex),'exec','--json','--skip-git-repo-check',*args],env=env,cwd=work,capture_output=True,text=True,timeout=100)
        (run/(label+'.jsonl')).write_text(r.stdout,encoding='utf-8')
        (run/(label+'.stderr.log')).write_text(r.stderr,encoding='utf-8')
        events=[]
        for line in r.stdout.splitlines():
            try: events.append(json.loads(line))
            except ValueError: pass
        messages=[e.get('item',{}).get('text','') for e in events if e.get('type')=='item.completed' and e.get('item',{}).get('type')=='agent_message']
        assert r.returncode==0, label+' failed; private diagnostics retained'
        assert not any(e.get('item',{}).get('type') in ('command_execution','mcp_tool_call') for e in events), 'unexpected tool execution'
        return events,'\n'.join(messages)
    first,reply1=invoke('first',['Do not use any tools. Remember this marker for our next turn: '+nonce+'. Reply with exactly ACK.'])
    thread=next(e['thread_id'] for e in first if e.get('type')=='thread.started')
    if before_resume: before_resume()
    second,reply2=invoke('second',['resume',thread,'Do not use tools. What marker did I give you in the previous turn? Reply with only that marker.'])
    second_thread=next((e.get('thread_id') for e in second if e.get('type')=='thread.started'),None)
    result={'real_client':True,'model':model,'first_reply_correct':reply1.strip()=='ACK',
        'second_reply_exact_nonce':reply2.strip()==nonce,'same_thread':second_thread==thread,
        'tools_requested':False,'live_codex_config_changed':False,'private_run_directory':str(run)}
    (run/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    assert result['first_reply_correct'] and result['second_reply_exact_nonce'] and result['same_thread'], 'client transcript acceptance failed; see private result'
    return result
