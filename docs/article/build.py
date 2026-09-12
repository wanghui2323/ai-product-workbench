#!/usr/bin/env python3
"""Build the checked-in article previews and editable figures (Python + Markdown).

Install the optional authoring dependency with:
    python3 -m pip install -r docs/article/requirements.txt
PNG assets are exported from the SVGs in a browser at their native dimensions.
The skill and workbench do not depend on this script or package.
"""
from pathlib import Path
import html
import re

try:
    import markdown
except ImportError as exc:
    raise SystemExit("Install article authoring dependency: python3 -m pip install -r docs/article/requirements.txt") from exc

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)


from render_figures import build_figures
build_figures()

# Cover is new AI-generated artwork. This browser canvas only exports its
# original composition to the required 900 x 383 article asset.
(ROOT / "cover.html").write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>AI 产品开发工作台 · 封面</title><style>html,body{margin:0;width:900px;height:383px;overflow:hidden;background:#030a0e}img{display:block;width:900px;height:383px;object-fit:contain}</style><img src="assets/cover-v2-source.png" alt="AI WORKBENCH 从需求到产品交付">', encoding="utf-8")

source = (ROOT / "article.md").read_text(encoding="utf-8")
lines = source.splitlines()
title = lines[0].removeprefix("# ").strip()
body = markdown.markdown("\n".join(lines[1:]), extensions=["fenced_code", "tables", "sane_lists"])
# Inline paragraph formatting survives a rich-text clipboard transfer.
inline = {"p": "margin:18px 0;font-size:17px;line-height:1.95;color:#263747;", "h2": "margin:40px 0 18px;font-size:24px;line-height:1.5;color:#162c40;font-weight:700;", "h3": "margin:28px 0 12px;font-size:20px;line-height:1.6;color:#162c40;", "img": "display:block;width:100%;height:auto;margin:24px auto;border-radius:8px;", "blockquote": "margin:22px 0;padding:2px 20px;border-left:4px solid #138e97;background:#eaf4f5;", "pre": "white-space:pre-wrap;word-break:break-word;background:#eff3f6;padding:18px;border-radius:8px;font-size:14px;line-height:1.7;", "li": "margin:10px 0;font-size:17px;line-height:1.85;", "a": "color:#0b7e89;text-decoration:underline;overflow-wrap:anywhere;", "table": "width:100%;border-collapse:collapse;font-size:14px;line-height:1.65;", "td": "border:1px solid #d8e2da;padding:8px;", "th": "border:1px solid #d8e2da;padding:8px;background:#eaf4f5;"}
for tag, style in inline.items():
    body = re.sub(r"<" + tag + r"(?=[\s>])", f'<{tag} style="{style}"', body)
css = '''*{box-sizing:border-box}body{margin:0;background:#fbfaf7;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;color:#243747}a{color:#0b7e89}.shell{max-width:940px;margin:0 auto;padding:32px 24px 70px}.top{display:flex;gap:16px;justify-content:space-between;flex-wrap:wrap;font-size:13px;margin:0 0 24px}.hero{padding:38px 40px;background:#14283b;border-radius:20px;color:#f3f7f0}.eyebrow{font-size:12px;letter-spacing:2px;color:#8ed2db}h1{font-size:34px;line-height:1.45;margin:15px 0}.sub{font-size:14px;line-height:1.8;color:#bfd4e0}.cover-preview{display:block;width:100%;height:auto;margin-top:22px;border-radius:14px}.paper{background:#fff;border:1px solid #dfe5e8;border-radius:18px;padding:28px 58px 48px;margin-top:22px}.toolbar{padding:20px 0;display:flex;gap:10px;align-items:center;flex-wrap:wrap}.toolbar button{cursor:pointer;border:1px solid #b7cbd1;border-radius:8px;background:#fff;color:#23495a;padding:11px 16px;font:inherit}.toolbar button.primary{background:#0e727b;color:white}.note{font-size:13px;line-height:1.7;color:#627685}#copy-status{min-height:24px;font-size:14px}code{overflow-wrap:anywhere;font-family:ui-monospace,monospace}article{overflow-wrap:break-word}article>p:has(>img){margin-left:-20px!important;margin-right:-20px!important}article ul,article ol{padding-left:24px}footer{margin:30px 0;color:#627685;font-size:13px;line-height:1.8}@media(max-width:600px){.shell{padding:16px 14px 36px}.hero{padding:25px 22px;border-radius:14px}h1{font-size:27px}.paper{padding:16px 19px 30px;border-radius:12px}article>p:has(>img){margin-left:-17px!important;margin-right:-17px!important}article h2{font-size:22px!important}article pre{padding:12px!important;font-size:12px!important}article table{font-size:12px!important}article td,article th{padding:5px!important}}'''
script = '''const content=document.getElementById('article-body'),status=document.getElementById('copy-status');function selectBody(){const range=document.createRange();range.selectNodeContents(content);const sel=window.getSelection();sel.removeAllRanges();sel.addRange(range)}document.getElementById('select-body').onclick=()=>{selectBody();status.textContent='已选中正文，可用系统复制快捷键。'};document.getElementById('copy-body').onclick=async()=>{const clone=content.cloneNode(true);clone.querySelectorAll('img').forEach(img=>img.src=new URL(img.getAttribute('src'),location.href).href);try{await navigator.clipboard.write([new ClipboardItem({'text/html':new Blob([clone.innerHTML],{type:'text/html'}),'text/plain':new Blob([content.innerText],{type:'text/plain'})})]);status.textContent='正文已复制。请在目标编辑器核对文字、图片与排版。'}catch(e){selectBody();status.textContent='浏览器未开放剪贴板；已选中正文，请按系统复制快捷键。'}};'''
for filename, copying in [("index.html", False), ("wechat-copy.html", True)]:
    toolbar = '''<div class="toolbar"><button class="primary" id="copy-body">复制正文</button><button id="select-body">选中正文</button><a href="assets/cover.png">单独打开封面</a></div><p class="note">复制范围仅含正文。标题与封面单独使用；本地复制结果需在目标编辑器核对，本文尚未发布到公众号。</p><p role="status" id="copy-status"></p>''' if copying else ''
    nav = '<a href="wechat-copy.html">正文复制工作台 →</a>' if not copying else '<a href="index.html">← 返回阅读版</a>'
    page = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}{' · 正文复制' if copying else ''}</title><style>{css}</style></head><body><main class="shell"><nav class="top"><a href="https://github.com/wanghui2323/ai-product-workbench">AI 产品开发工作台 / GitHub</a>{nav}</nav><header class="hero"><div class="eyebrow">OPEN SOURCE / 从需求到交付</div><h1>{html.escape(title)}</h1><div class="sub">一套可以带到其他项目的 AI 协作协议、项目记录与可视化工作台。</div></header>{toolbar}{'' if copying else '<img class="cover-preview" src="assets/cover.png" alt="AI WORKBENCH 从需求到产品交付 · 封面">'}<section class="paper"><article id="article-body">{body}</article></section><footer>配图与文章源文件随仓库开放。<a href="article.md">Markdown 原文</a> · <a href="sources.md">来源说明</a> · <a href="gallery.html">封面与配图</a> · <a href="../../LICENSE">MIT 许可证</a></footer></main>{'<script>'+script+'</script>' if copying else ''}</body></html>'''
    (ROOT / filename).write_text(page, encoding="utf-8")
print("Built article previews, 2 mechanism SVGs, and cover export page.")

# Review gallery keeps screenshots distinguishable from explanatory drawings.
images = [("封面 · AI 概念视觉，单独使用", "assets/cover.png")]
images += [("真实截图 · " + alt if "screenshot-" in path else "机制图 · " + alt, path) for alt, path in re.findall(r"!\[([^\]]+)\]\(([^)]+)\)", source)]
gallery = "".join(f'<section class="paper"><h2>{html.escape(label)}</h2><a href="{html.escape(path)}"><img style="display:block;width:100%;height:auto" src="{html.escape(path)}" alt="{html.escape(label)}"></a></section>' for label, path in images)
(ROOT / "gallery.html").write_text(f'<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AI 产品开发工作台 · 封面与配图</title><style>{css}</style><main class="shell"><nav class="top"><a href="index.html">← 返回文章</a><a href="wechat-copy.html">正文复制版</a></nav><h1>封面与配图</h1><p>真实截图来自当前运行的工作台，示例业务为虚构教学数据。点击图片可打开原图。</p>{gallery}</main></html>', encoding="utf-8")
