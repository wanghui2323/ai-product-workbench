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


def svg_start(height, number, title, subtitle):
    return [f'''<svg xmlns="http://www.w3.org/2000/svg" width="1062" height="{height}" viewBox="0 0 1062 {height}">
<defs><marker id="arrow" markerWidth="12" markerHeight="12" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L6,3 z" fill="#9aafa9"/></marker></defs>
<style>text{{font-family:"PingFang SC","Microsoft YaHei","Noto Sans CJK SC",sans-serif;fill:#193d38}}.muted{{fill:#58766f}}</style>
<rect width="1062" height="{height}" fill="#f3f7f4"/>
<rect x="52" y="48" width="66" height="10" rx="5" fill="#178571"/>
<text x="136" y="65" font-size="28" letter-spacing="3">AI 产品开发工作台 / {number}</text>
<text x="52" y="142" font-size="54" font-weight="650">{html.escape(title)}</text>
<text class="muted" x="52" y="203" font-size="34">{html.escape(subtitle)}</text>''']


def card(parts, y, index, title, line, fill="#ffffff", height=154):
    parts.append(f'''<rect x="52" y="{y}" width="958" height="{height}" rx="24" fill="{fill}" stroke="#d3e2dc" stroke-width="2"/>
<circle cx="102" cy="{y+49}" r="24" fill="#dcece5"/>
<text x="102" y="{y+59}" font-size="28" text-anchor="middle">{index}</text>
<text x="148" y="{y+62}" font-size="42" font-weight="600">{html.escape(title)}</text>
<text x="88" y="{y+120}" font-size="38" class="muted">{html.escape(line)}</text>''')


def arrow(parts, y, to):
    parts.append(f'<path d="M531 {y} V{to}" stroke="#9aafa9" stroke-width="4" marker-end="url(#arrow)"/>')


def save(parts, name, height, footer):
    parts.append(f'<text x="52" y="{height-38}" font-size="29" class="muted">{html.escape(footer)}</text></svg>')
    (ASSETS / f"{name}.svg").write_text("\n".join(parts), encoding="utf-8")


p = svg_start(1560, "01", "让每个阶段留下可接手的结果", "从一句想法，到有依据的下一步")
stages = [
    ("原始诉求", "“做一个能让团队分享资料的文档助手”"),
    ("澄清关键问题 · 比较路线", "谁来用？分享给谁？怎样算做好？"),
    ("记录用户明确选择", "答案 + 理由 + 来源 + 受影响范围"),
    ("同步七个管理域", "需求、技术、选型、规范、计划、测试、版本"),
    ("实现后补验收证据", "把产物、条件、环境和结果绑定起来"),
    ("交付当前版本 · 回流下一轮", "核对目标环境，留下未过项和下一步"),
]
for i, (title, line) in enumerate(stages):
    y = 256 + i * 194
    card(p, y, str(i+1), title, line, "#e6f2eb" if i == 2 else "#ffffff")
    if i < len(stages)-1:
        arrow(p, y+160, y+186)
save(p, "01-workflow", 1560, "AI 负责对话与回写；项目记录保存事实；工作台提供阅读入口。")

p = svg_start(1550, "02", "一次选择，改变整条交付链", "虚构示例 · 首版选择“仅项目内分享”")
stages = [
    ("需求边界", "仅项目内分享，成员仍受资料权限限制"),
    ("技术方案与选型", "先核验成员与资料权限，再检索内容"),
    ("视觉交互与 AI 规范", "标明分享范围；无权访问时说明下一步"),
    ("开发计划及模式", "先定权限合同，再拆独立任务并行实现"),
    ("测试规范", "有权成员可读；无权与退出成员被拒绝"),
    ("上线版本管理", "用同一候选产物核对目标环境和回退"),
]
for i, (title, line) in enumerate(stages):
    y = 250 + i * 194
    card(p, y, str(i+1), title, line)
    if i < len(stages)-1:
        arrow(p, y+160, y+186)
save(p, "02-decision", 1550, "改变分享对象时，顺着关联记录重查方案、任务、测试与版本。")

p = svg_start(1180, "03", "每种证据，只证明对应的状态", "任务与版本有不同的验收对象")
p.append('<text x="52" y="283" font-size="34" font-weight="600">任务这一层</text>')
card(p, 310, "A", "done · 实现完成", "已有对应产物，仍需核对退出条件")
arrow(p, 470, 508)
card(p, 522, "B", "accepted · 任务已验收", "退出条件有对应、可核对的证据", "#e6f2eb")
p.append('<text x="52" y="743" font-size="34" font-weight="600">版本这一层</text>')
card(p, 770, "A", "local_verified · 本地验证", "结果只覆盖记录中的本地条件", height=146)
arrow(p, 920, 949)
card(p, 960, "B", "released · 目标交付已验证", "目标产物、交付与环境回归均有依据", "#e6f2eb", height=146)
save(p, "03-evidence", 1180, "结构校验通过 ≠ 证据真实；旧结果不能自动证明新版本。")

cover = '''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="383" viewBox="0 0 900 383">
<rect width="900" height="383" fill="#143c35"/><circle cx="820" cy="25" r="260" fill="#1c5145"/>
<g font-family="PingFang SC,Microsoft YaHei,sans-serif"><text x="50" y="62" font-size="19" letter-spacing="3" fill="#a8d6bd">OPEN SOURCE · AI PRODUCT WORKBENCH</text>
<text x="50" y="152" font-size="48" font-weight="600" fill="#f3f6ed">AI 产品开发工作台</text><text x="50" y="211" font-size="26" fill="#c1daca">从模糊需求，到有依据的产品交付</text>
<g font-size="19" fill="#d5eadc"><text x="50" y="306">澄清</text><text x="147" y="306">方案</text><text x="244" y="306">实现</text><text x="341" y="306">验证</text><text x="438" y="306">交付</text></g></g>
<g stroke="#72b496" fill="none" stroke-width="2"><path d="M96 299h35m62 0h35m62 0h35m62 0h35"/><rect x="663" y="118" width="158" height="182" rx="18"/><path d="M690 157h105m-105 32h76m-76 32h94m-94 32h58"/></g></svg>'''
(ASSETS / "cover.svg").write_text(cover, encoding="utf-8")

source = (ROOT / "article.md").read_text(encoding="utf-8")
lines = source.splitlines()
title = lines[0].removeprefix("# ").strip()
body = markdown.markdown("\n".join(lines[1:]), extensions=["fenced_code", "tables", "sane_lists"])
# Inline paragraph formatting survives a rich-text clipboard transfer.
inline = {"p": "margin:18px 0;font-size:17px;line-height:1.95;color:#263d36;", "h2": "margin:40px 0 18px;font-size:24px;line-height:1.5;color:#183e34;font-weight:700;", "h3": "margin:28px 0 12px;font-size:20px;line-height:1.6;color:#183e34;", "img": "display:block;width:100%;height:auto;margin:24px auto;border-radius:8px;", "blockquote": "margin:22px 0;padding:2px 20px;border-left:4px solid #558b74;background:#eff5f0;", "pre": "white-space:pre-wrap;word-break:break-word;background:#eff3f0;padding:18px;border-radius:8px;font-size:14px;line-height:1.7;", "li": "margin:10px 0;font-size:17px;line-height:1.85;", "a": "color:#276d52;text-decoration:underline;overflow-wrap:anywhere;", "table": "width:100%;border-collapse:collapse;font-size:14px;line-height:1.65;", "td": "border:1px solid #d8e2da;padding:8px;", "th": "border:1px solid #d8e2da;padding:8px;background:#eff5f0;"}
for tag, style in inline.items():
    body = re.sub(r"<" + tag + r"(?=[\s>])", f'<{tag} style="{style}"', body)
css = '''*{box-sizing:border-box}body{margin:0;background:#f2f5ef;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;color:#243b32}a{color:#246848}.shell{max-width:940px;margin:0 auto;padding:32px 24px 70px}.top{display:flex;gap:16px;justify-content:space-between;flex-wrap:wrap;font-size:13px;margin:0 0 24px}.hero{padding:38px 40px;background:#173e34;border-radius:20px;color:#f3f7f0}.eyebrow{font-size:12px;letter-spacing:2px;color:#add1bc}h1{font-size:34px;line-height:1.45;margin:15px 0}.sub{font-size:14px;line-height:1.8;color:#c1d7c7}.paper{background:#fff;border:1px solid #e1e7de;border-radius:18px;padding:28px 58px 48px;margin-top:22px}.toolbar{padding:20px 0;display:flex;gap:10px;align-items:center;flex-wrap:wrap}.toolbar button{cursor:pointer;border:1px solid #a9bfae;border-radius:8px;background:#fff;color:#214a35;padding:11px 16px;font:inherit}.toolbar button.primary{background:#24553f;color:white}.note{font-size:13px;line-height:1.7;color:#687b6d}#copy-status{min-height:24px;font-size:14px}code{overflow-wrap:anywhere;font-family:ui-monospace,monospace}article{overflow-wrap:break-word}article>p:has(>img){margin-left:-20px!important;margin-right:-20px!important}article ul,article ol{padding-left:24px}footer{margin:30px 0;color:#687b6d;font-size:13px;line-height:1.8}@media(max-width:600px){.shell{padding:16px 14px 36px}.hero{padding:25px 22px;border-radius:14px}h1{font-size:27px}.paper{padding:16px 19px 30px;border-radius:12px}article>p:has(>img){margin-left:-8px!important;margin-right:-8px!important}article h2{font-size:22px!important}article pre{padding:12px!important;font-size:12px!important}article table{font-size:12px!important}article td,article th{padding:5px!important}}'''
script = '''const content=document.getElementById('article-body'),status=document.getElementById('copy-status');function selectBody(){const range=document.createRange();range.selectNodeContents(content);const sel=window.getSelection();sel.removeAllRanges();sel.addRange(range)}document.getElementById('select-body').onclick=()=>{selectBody();status.textContent='已选中正文，可用系统复制快捷键。'};document.getElementById('copy-body').onclick=async()=>{const clone=content.cloneNode(true);clone.querySelectorAll('img').forEach(img=>img.src=new URL(img.getAttribute('src'),location.href).href);try{await navigator.clipboard.write([new ClipboardItem({'text/html':new Blob([clone.innerHTML],{type:'text/html'}),'text/plain':new Blob([content.innerText],{type:'text/plain'})})]);status.textContent='正文已复制。请在目标编辑器核对文字、图片与排版。'}catch(e){selectBody();status.textContent='浏览器未开放剪贴板；已选中正文，请按系统复制快捷键。'}};'''
for filename, copying in [("index.html", False), ("wechat-copy.html", True)]:
    toolbar = '''<div class="toolbar"><button class="primary" id="copy-body">复制正文</button><button id="select-body">选中正文</button><a href="assets/cover.png">单独打开封面</a></div><p class="note">复制范围仅含正文。标题与封面单独使用；本地复制结果需在目标编辑器核对，本文尚未发布到公众号。</p><p role="status" id="copy-status"></p>''' if copying else ''
    nav = '<a href="wechat-copy.html">正文复制工作台 →</a>' if not copying else '<a href="index.html">← 返回阅读版</a>'
    page = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}{' · 正文复制' if copying else ''}</title><style>{css}</style></head><body><main class="shell"><nav class="top"><a href="https://github.com/wanghui2323/ai-product-workbench">AI 产品开发工作台 / GitHub</a>{nav}</nav><header class="hero"><div class="eyebrow">OPEN SOURCE / 从需求到交付</div><h1>{html.escape(title)}</h1><div class="sub">一套可以带到其他项目的 AI 协作协议、项目记录与可视化工作台。</div></header>{toolbar}<section class="paper"><article id="article-body">{body}</article></section><footer>配图与文章源文件随仓库开放。<a href="article.md">Markdown 原文</a> · <a href="sources.md">来源说明</a> · <a href="../../LICENSE">MIT 许可证</a></footer></main>{'<script>'+script+'</script>' if copying else ''}</body></html>'''
    (ROOT / filename).write_text(page, encoding="utf-8")
print("Built article previews and 4 editable SVG figures.")
