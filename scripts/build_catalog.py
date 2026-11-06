#!/usr/bin/env python3
"""Build a deterministic audio catalog and downloadable bundles from audio/."""
import argparse,collections,hashlib,json,re,zipfile
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
from pathlib import Path
from urllib.parse import quote
import mutagen
ROOT=Path(__file__).resolve().parents[1]
REPO='LiLiShader/game-audio-library'
PAGE='https://lilishader.github.io/game-audio-library/'
RELEASE=f'https://github.com/{REPO}/releases/download/library'
CATEGORIES=[('01','背景音乐','BGM','场景氛围与循环音乐'),('02','界面交互','UI','按钮、弹窗、开关与翻页'),('03','核心玩法','GAMEPLAY','消除、攻击、脚步与环境'),('04','道具技能','SKILLS','魔法、增益与道具触发'),('05','障碍机关','OBSTACLES','碰撞、破碎与机关解锁'),('06','奖励收获','REWARDS','金币、宝箱与礼物'),('07','收集图鉴','COLLECTION','相册、拼图与成就收集'),('08','关卡结果','RESULTS','胜利、失败与结算'),('09','商店消费','SHOP','购买与交易反馈'),('10','体力生命','LIFE','生命、体力与状态变化'),('11','人声语音','VOICE','语音播报与人物反馈')]
def source_info(p):
    data={}
    if p.exists():
        for line in p.read_text(errors='replace').splitlines():
            if ':' in line:
                k,v=line.split(':',1);data[k.strip()]=v.strip()
    return data

def main(bundles=True):
    audio=ROOT/'audio'; old={}
    if (ROOT/'catalog.json').exists():old=json.loads((ROOT/'catalog.json').read_text())
    cached={a['path']:a for a in old.get('tracks',[])}
    descriptions={}
    for listing in audio.rglob('音频清单.md'):
        category=''
        for line in listing.read_text(errors='replace').splitlines():
            hit=re.match(r'## (\d{2}_[^\s]+)',line)
            if hit:category=hit.group(1)
            cells=[x.strip().strip('`') for x in line.split('|')[1:-1]]
            if category and len(cells)>=4 and Path(cells[0]).suffix.lower() in {'.mp3','.wav','.ogg'}:
                descriptions[str((listing.parent/category/cells[0]).relative_to(ROOT))]=cells[-1]
    tracks=[];sources={};errors=[]
    for p in sorted(audio.rglob('*')):
        if not p.is_file() or p.suffix.lower() not in {'.mp3','.wav','.ogg'} or any(x.startswith('.') for x in p.relative_to(audio).parts):continue
        parts=p.relative_to(audio).parts;rel=p.relative_to(ROOT).as_posix();cat=next((x[:2] for x in parts if re.match(r'^\d{2}_',x)),'03')
        if cat not in {c[0] for c in CATEGORIES}:raise SystemExit('未知分类编号：'+rel)
        public=parts[0]=='网络公共音效库';pack=parts[2] if public else parts[0]
        inf=source_info(p.parent/'SOURCE.txt');source_id=('public/' if public else 'project/')+pack
        if source_id not in sources:
            sources[source_id]={'id':source_id,'name':inf.get('包名',pack),'author':inf.get('作者',parts[0] if not public else '见来源文件'),'url':inf.get('来源',''),'license':('CC0 1.0' if 'CC0' in inf.get('许可','') else inf.get('许可','待补充许可')) if public else (inf.get('许可') or ('课堂共享授权' if parts[0] in {'Blossom','mahjong-match','tile-vertical'} else '待补充许可')),'licenseUrl':inf.get('许可原文',''),'group':'公共音效' if public else '项目音频'}
        if sources[source_id]['license']=='待补充许可':raise SystemExit('请为新增来源提供 SOURCE.txt 中的许可说明：'+source_id)
        digest=hashlib.sha256(p.read_bytes()).hexdigest();prior=cached.get(rel,{})
        try:
            if prior.get('sha256')==digest:duration=prior['duration']
            else:
                parsed=mutagen.File(p)
                if parsed is None:raise ValueError('Unrecognized audio')
                duration=round(parsed.info.length,3)
        except Exception as exc:errors.append({'path':rel,'error':str(exc)});continue
        label=re.sub(r'[_\-]+',' ',p.stem).strip()
        tracks.append({'id':hashlib.sha256(rel.encode()).hexdigest()[:16],'name':p.name,'title':label,'description':descriptions.get(rel,''),'path':rel,'url':quote(rel,safe='/'),'category':cat,'source':source_id,'format':p.suffix[1:].upper(),'bytes':p.stat().st_size,'duration':duration,'sha256':digest,'license':sources[source_id]['license']})
    if errors:raise SystemExit('Audio metadata errors: '+json.dumps(errors,ensure_ascii=False))
    if not tracks:raise SystemExit('No audio files; refusing to publish an empty catalog')
    counts=collections.Counter(t['category'] for t in tracks);sha_groups=collections.Counter(t['sha256'] for t in tracks)
    cats=[{'id':id,'name':name,'en':en,'description':desc,'count':counts[id],'download':f'{RELEASE}/category-{id}.zip'} for id,name,en,desc in CATEGORIES]
    stable={'schemaVersion':1,'tracks':tracks,'categories':cats,'sources':list(sources.values()),'stats':{'count':len(tracks),'bytes':sum(t['bytes'] for t in tracks),'unique':len(sha_groups),'categories':sum(bool(n) for n in counts.values()),'sources':len(sources),'formats':dict(collections.Counter(t['format'] for t in tracks))},'allDownload':f'{RELEASE}/game-audio-library-all.zip','repository':f'https://github.com/{REPO}'}
    compare={k:v for k,v in old.items() if k!='updatedAt'}
    stable['updatedAt']=old.get('updatedAt') if stable==compare else datetime.now(timezone.utc).isoformat(timespec='seconds')
    (ROOT/'catalog.json').write_text(json.dumps(stable,ensure_ascii=False,separators=(',',':'))+'\n')
    if bundles:
        dist=ROOT/'.dist';dist.mkdir(exist_ok=True)
        notes=(ROOT/'LICENSE.md').read_bytes()
        def archive(name,items):
            with zipfile.ZipFile(dist/name,'w',zipfile.ZIP_DEFLATED,compresslevel=3) as z:
                paths=set()
                for t in items:
                    paths.add(t['path']);parent=(ROOT/t['path']).parent
                    if (parent/'SOURCE.txt').exists():paths.add((parent/'SOURCE.txt').relative_to(ROOT).as_posix())
                for path in sorted(paths):
                    zi=zipfile.ZipInfo(path,date_time=(2026,1,1,0,0,0));zi.compress_type=zipfile.ZIP_DEFLATED;z.writestr(zi,(ROOT/path).read_bytes())
                zi=zipfile.ZipInfo('LICENSE.md',date_time=(2026,1,1,0,0,0));zi.compress_type=zipfile.ZIP_DEFLATED;z.writestr(zi,notes)
                checks=''.join(f"{t['sha256']}  {t['path']}\n" for t in items)
                zi=zipfile.ZipInfo('SHA256SUMS.txt',date_time=(2026,1,1,0,0,0));zi.compress_type=zipfile.ZIP_DEFLATED;z.writestr(zi,checks)
        archive('game-audio-library-all.zip',tracks)
        for c in cats:
            archive(f"category-{c['id']}.zip",[t for t in tracks if t['category']==c['id']])
    render_readme(stable)
    print(json.dumps(stable['stats'],ensure_ascii=False))

def render_readme(c):
    stats=c['stats'];rows='\n'.join(f"| {x['id']} · [{x['name']}]({PAGE}?category={x['id']}) | {x['description']} | {x['count']} | [下载 ZIP]({x['download']}) |" for x in c['categories'])
    text=f'''<div align="center">

<img src="docs/banner.svg" alt="声场 · 游戏音频资源库" width="100%">

# 声场 · 游戏音频资源库

**让你的游戏，听起来更完整。**

{stats['count']:,} 个音频 · {stats['categories']} 类用途 · {stats['sources']} 个来源 · MP3 / WAV / OGG

[**▶ 打开试听与下载目录**]({PAGE})　 ·　 [**↓ 下载全部音频**]({c['allDownload']})　 ·　 [更新指南](docs/维护指南.md)

</div>

---

## 从这里开始

1. **找声音**：打开 [在线目录]({PAGE})，按用途、来源和格式筛选，或搜索文件名与中文用途。
2. **先试听**：点击播放即可试听。收藏喜欢的声音，使用底部播放器调节进度与音量。
3. **放进游戏**：下载单个原始文件，或按分类下载 ZIP。也可以点击「复制给 AI」，获得文件链接、用途与许可信息。

无需登录即可浏览、试听和下载。收藏仅保存在当前浏览器。音频保持原始格式和音量；OGG 播放支持取决于浏览器。

## 按用途下载

| 分类 | 适合使用在 | 文件数 | 整类下载 |
| --- | --- | ---: | --- |
{rows}

## 资源与许可

- **公共音效**：来自 OpenGameArt 与 Kenney，原始来源记录标注为 CC0 1.0；随文件保留 `SOURCE.txt`、作者及来源链接。
- **项目音频**：Blossom、mahjong-match、tile-vertical；维护者已确认可以公开分发，供课堂学习使用。它们不自动适用 CC0，其他用途请向维护者确认。
- 原文件名与分类目录均保留；相同内容在不同项目中可能重复，共 {stats['unique']:,} 个不同的 SHA-256。目录保留这些版本以便追溯。
- [查看许可说明](LICENSE.md) · [原始音频目录](audio/) · [机器可读清单](catalog.json)

## 持续更新

在原音频文件夹添加或调整文件后，运行本机的「更新音频库.command」，索引、下载包与 GitHub Pages 会随发布更新。也支持保持运行的监听模式。详细操作见 [维护指南](docs/维护指南.md)。

> 在线目录会在 GitHub Pages 部署完成后更新，通常需要几分钟；并非修改本地文件后立即出现在网页上。

---

由 LiLiShader 整理，面向游戏制作学习者。最近内容更新：{datetime.fromisoformat(c['updatedAt']).astimezone(ZoneInfo('Asia/Shanghai')).date()}。
'''
    (ROOT/'README.md').write_text(text)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--no-bundles',action='store_true');args=ap.parse_args();main(not args.no_bundles)
