"""Publish an existing local commit through GitHub's Git Database API.

No force push. Confirm the remote ref still matches and validate identical trees.
Credentials are supplied exclusively by the authenticated gh CLI.
"""
import base64,json,os,subprocess,tempfile,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPO='LiLiShader/game-audio-library'
def local(*args,raw=False,env=None):
    r=subprocess.run(['git',*args],cwd=ROOT,check=True,capture_output=True,env=env)
    return r.stdout if raw else r.stdout.decode().strip()
def api(gh,path,body=None):
    args=[gh,'api',f'repos/{REPO}/{path}'];tmp=None
    if body is not None:
        (ROOT/'.local').mkdir(exist_ok=True)
        with tempfile.NamedTemporaryFile(mode='w',dir=ROOT/'.local',suffix='.json',delete=False) as f:json.dump(body,f);tmp=f.name
        args+=['--method','PATCH' if path.startswith('git/refs/') else 'POST','--input',tmp]
    try:
        for attempt in range(3):
            r=subprocess.run(args,capture_output=True,text=True,env={**os.environ,'GODEBUG':'http2client=0'})
            if r.returncode==0:return json.loads(r.stdout)
            if attempt==2:raise RuntimeError('GitHub API 请求失败：'+r.stderr.strip())
            time.sleep(3)
    finally:
        if tmp:Path(tmp).unlink(missing_ok=True)
def remote_head(gh):return api(gh,'git/ref/heads/main')['object']['sha']
def publish(gh,expected_remote):
    head=local('rev-parse','HEAD')
    if head==expected_remote:return
    if remote_head(gh)!=expected_remote:raise RuntimeError('远端已变化，停止发布以避免覆盖。')
    subprocess.run(['git','merge-base','--is-ancestor',expected_remote,head],cwd=ROOT,check=True)
    base=api(gh,'git/commits/'+expected_remote)['tree']['sha'];items=[]
    paths=local('diff','--name-only','--no-renames','-z',expected_remote,head,raw=True).decode().rstrip('\0').split('\0')
    for path in filter(None,paths):
        entry=local('ls-tree',head,'--',path)
        if not entry:items.append({'path':path,'mode':'100644','type':'blob','sha':None});continue
        mode,kind,sha=entry.split('\t',1)[0].split()
        if kind!='blob':raise RuntimeError('不支持的 Git 对象类型：'+kind)
        data=local('cat-file','blob',sha,raw=True)
        if len(data)>=100*1024*1024:raise RuntimeError('文件过大，请改用 Release 附件：'+path)
        blob=api(gh,'git/blobs',{'encoding':'base64','content':base64.b64encode(data).decode()})
        if blob['sha']!=sha:raise RuntimeError('GitHub 文件校验失败：'+path)
        items.append({'path':path,'mode':mode,'type':'blob','sha':sha})
    tree=api(gh,'git/trees',{'base_tree':base,'tree':items})
    if tree['sha']!=local('rev-parse','HEAD^{tree}'):raise RuntimeError('远端目录树与本地不一致，停止发布。')
    fields=local('show','-s','--format=%an%n%ae%n%aI%n%cn%n%ce%n%cI',head).splitlines()
    dates=[datetime.fromisoformat(fields[i]).astimezone(timezone.utc).isoformat(timespec='seconds') for i in [2,5]]
    message=local('show','-s','--format=%B',head,raw=True).decode().rstrip('\n')+'\n'
    author={'name':fields[0],'email':fields[1],'date':dates[0]};committer={'name':fields[3],'email':fields[4],'date':dates[1]}
    commit=api(gh,'git/commits',{'message':message,'tree':tree['sha'],'parents':[expected_remote],'author':author,'committer':committer})
    env={**os.environ,'GIT_AUTHOR_NAME':author['name'],'GIT_AUTHOR_EMAIL':author['email'],'GIT_AUTHOR_DATE':dates[0],'GIT_COMMITTER_NAME':committer['name'],'GIT_COMMITTER_EMAIL':committer['email'],'GIT_COMMITTER_DATE':dates[1]}
    result=subprocess.run(['git','commit-tree',tree['sha'],'-p',expected_remote],input=message,text=True,capture_output=True,check=True,cwd=ROOT,env=env)
    local_sha=result.stdout.strip()
    if local_sha!=commit['sha']:raise RuntimeError('本地与远端提交校验不一致；远端分支尚未修改。')
    if remote_head(gh)!=expected_remote:raise RuntimeError('远端在发布期间变化，停止更新分支。')
    api(gh,'git/refs/heads/main',{'sha':commit['sha'],'force':False})
    local('update-ref','refs/heads/main',local_sha,head)
    local('update-ref','refs/remotes/origin/main',local_sha)
    print('GitHub API 发布成功：'+local_sha[:12],flush=True)
