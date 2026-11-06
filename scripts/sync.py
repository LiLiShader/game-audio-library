#!/usr/bin/env python3
"""Synchronize a local audio folder, regenerate catalog/bundles, then publish."""
import argparse,fcntl,hashlib,json,os,shutil,subprocess,sys,time
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];REPO='LiLiShader/game-audio-library';os.environ.setdefault('GODEBUG','http2client=0')
GH=os.environ.get('GH_BIN') or shutil.which('gh') or 'gh'
ALLOWED={'.mp3','.wav','.ogg','.md','.txt'}
def run(args,**kw):
    for i in range(3):
        try:return subprocess.run(args,check=True,text=True,**kw)
        except subprocess.CalledProcessError:
            if i==2:raise
            print('网络操作重试…',flush=True);time.sleep(3)
def gh(*args,**kw):return run([GH,*args],**kw)
def git(*args,**kw):return run(['git','-c','credential.helper=','-c',f'credential.helper=!{GH} auth git-credential',*args],cwd=ROOT,**kw)
def files(source):
    return {p.relative_to(source).as_posix():p for p in source.rglob('*') if p.is_file() and not p.is_symlink() and p.suffix.lower() in ALLOWED and not any(v.startswith('.') for v in p.relative_to(source).parts) and p.name!='AGENTS.md'}
def signature(source):
    if not source.is_dir():raise RuntimeError('原文件夹不存在，请确认移动硬盘已连接。')
    return tuple((n,p.stat().st_size,p.stat().st_mtime_ns) for n,p in sorted(files(source).items()))
def sync(source,allow_large=False,dry=False):
    if not source.is_dir():raise RuntimeError('原文件夹不存在，请确认移动硬盘已连接。')
    incoming=files(source);audio_count=sum(p.suffix.lower() in {'.mp3','.wav','.ogg'} for p in incoming.values())
    if not audio_count:raise RuntimeError('源目录没有音频，为避免误删，本次同步已停止。')
    target=ROOT/'audio';existing=files(target);removed=set(existing)-set(incoming)
    if len(removed)>max(20,len(existing)*.2) and not allow_large:raise RuntimeError(f'检测到 {len(removed)} 个文件将移除，超过保护阈值。确认确实删除后添加 --allow-large-deletions。')
    changed=[]
    for rel,p in incoming.items():
        dst=target/rel
        if not dst.exists() or dst.stat().st_size!=p.stat().st_size or hashlib.sha256(dst.read_bytes()).digest()!=hashlib.sha256(p.read_bytes()).digest():changed.append(rel)
    print(f'音频 {audio_count} 个；新增/更新 {len(changed)} 个文件；移除 {len(removed)} 个文件。',flush=True)
    if dry:return
    branch=git('branch','--show-current',capture_output=True).stdout.strip()
    if branch!='main':raise RuntimeError('请先切换到 main 分支。')
    git('fetch','origin','main',stdout=subprocess.DEVNULL)
    head=git('rev-parse','HEAD',capture_output=True).stdout.strip();remote=git('rev-parse','origin/main',capture_output=True).stdout.strip()
    if head!=remote:
        ancestor=subprocess.run(['git','merge-base','--is-ancestor','origin/main','HEAD'],cwd=ROOT).returncode==0
        pending=git('log','--format=%s','origin/main..HEAD',capture_output=True).stdout.splitlines()
        if ancestor and pending and all(m.startswith('Update audio collection ') for m in pending):git('push','origin','main')
        else:raise RuntimeError('本地与远端版本不一致。请先检查并合并；脚本不会强制覆盖。')
    staged=git('diff','--cached','--name-only',capture_output=True).stdout.splitlines()
    if any(not (p.startswith('audio/') or p in {'README.md','catalog.json'}) for p in staged):raise RuntimeError('暂存区含其他改动，请先单独提交或取消暂存。')
    target.mkdir(exist_ok=True)
    for rel in changed:
        p=incoming[rel];dst=target/rel;before=(p.stat().st_size,p.stat().st_mtime_ns);data=p.read_bytes()
        if before!=(p.stat().st_size,p.stat().st_mtime_ns):raise RuntimeError('文件仍在写入，请稍后重试：'+rel)
        dst.parent.mkdir(parents=True,exist_ok=True);tmp=dst.with_name(dst.name+'.sync-part');tmp.write_bytes(data);tmp.replace(dst)
    for rel in removed:existing[rel].unlink()
    run([sys.executable,str(ROOT/'scripts/build_catalog.py')])
    git('add','audio','catalog.json','README.md')
    status=git('diff','--cached','--name-only',capture_output=True).stdout.strip()
    if status:
        git('commit','-m','Update audio collection '+datetime.now().strftime('%Y-%m-%d %H:%M'))
        git('push','origin','main')
    publish_bundles()
    print('发布完成。GitHub Pages 部署完成后网页会更新：\nhttps://lilishader.github.io/game-audio-library/',flush=True)
def publish_bundles():
    current=json.loads(gh('release','view','library','--repo',REPO,'--json','assets',capture_output=True).stdout)
    existing={a['name']:a for a in current['assets']}
    for p in sorted((ROOT/'.dist').glob('*.zip')):
        digest='sha256:'+hashlib.sha256(p.read_bytes()).hexdigest();old=existing.get(p.name)
        if old and old.get('digest')==digest:continue
        print('上传下载包：'+p.name,flush=True);gh('release','upload','library',str(p),'--repo',REPO,'--clobber')
    catalog=json.loads((ROOT/'catalog.json').read_text())
    notes=ROOT/'.dist/release-notes.md';notes.write_text(f"持续更新的音频下载包。当前 {catalog['stats']['count']} 个音频；内容更新时间 {catalog['updatedAt']}。\n\n可下载全部音频或单个分类。包内包含来源说明、许可与 SHA256SUMS.txt。\n\n在线试听：https://lilishader.github.io/game-audio-library/\n")
    gh('release','edit','library','--repo',REPO,'--notes-file',str(notes))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--watch',action='store_true');ap.add_argument('--dry-run',action='store_true');ap.add_argument('--allow-large-deletions',action='store_true');args=ap.parse_args()
    (ROOT/'.local').mkdir(exist_ok=True)
    lock=(ROOT/'.local/sync.lock').open('w')
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:sys.exit('已有同步进程运行，请先关闭另一个窗口。')
    try:
        if args.watch:
            print('监听已启动，每 5 秒检查；文件稳定 15 秒后同步。按 Ctrl+C 停止。',flush=True)
            last=signature(args.source);published=None;stable_since=time.monotonic();last_publish=0
            while True:
                try:
                    now=signature(args.source)
                    if now!=last:last=now;stable_since=time.monotonic()
                    if last!=published and time.monotonic()-stable_since>=15 and time.monotonic()-last_publish>=60:
                        sync(args.source,args.allow_large_deletions,args.dry_run);published=last;last_publish=time.monotonic()
                except Exception as exc:
                    print('同步暂缓：'+str(exc),flush=True);time.sleep(30)
                time.sleep(5)
        else:sync(args.source,args.allow_large_deletions,args.dry_run)
    except KeyboardInterrupt:print('\n监听已停止。')
    except Exception as exc:sys.exit('同步未完成：'+str(exc))
