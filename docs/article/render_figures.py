"""Editable mechanism figures. Real product captures are maintained separately."""
from pathlib import Path
from html import escape

ASSETS = Path(__file__).resolve().parent / "assets"
NAVY, TEAL, AMBER, MUTED = "#172c40", "#138e97", "#b68427", "#637281"


def start(height, label, title, subtitle):
    return [f'''<svg xmlns="http://www.w3.org/2000/svg" width="1062" height="{height}" viewBox="0 0 1062 {height}">
<defs><marker id="arr" markerWidth="12" markerHeight="12" refX="7" refY="4" orient="auto"><path d="M0 0L0 8L8 4z" fill="{TEAL}"/></marker></defs>
<style>text{{font-family:"PingFang SC","Microsoft YaHei","Noto Sans CJK SC",sans-serif;fill:{NAVY}}}</style>
<rect width="1062" height="{height}" fill="#fbfaf7"/>
<text x="60" y="68" font-size="32" font-weight="650" style="fill:{TEAL}">{label}</text>
<text x="60" y="148" font-size="50" font-weight="700">{title}</text>
<text x="60" y="208" font-size="34" style="fill:{MUTED}">{subtitle}</text>
<path d="M60 245H1002" stroke="#c8d1d4" stroke-width="2"/>''']


def box(parts, x, y, w, h, title, lines=(), tone="white", font=38):
    fill = {"white": "#ffffff", "teal": "#e1f0f1", "navy": NAVY, "amber": "#f6ecd4"}[tone]
    stroke = {"white": "#cbd4d8", "teal": TEAL, "navy": NAVY, "amber": AMBER}[tone]
    color = "#ffffff" if tone == "navy" else NAVY
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="24" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
    parts.append(f'<text x="{x+28}" y="{y+56}" font-size="{font}" font-weight="650" style="fill:{color}">{escape(title)}</text>')
    for i, line in enumerate(lines):
        parts.append(f'<text x="{x+28}" y="{y+109+i*46}" font-size="34" style="fill:{"#c6dbe3" if tone=="navy" else MUTED}">{escape(line)}</text>')


def arrow(parts, x1, y1, x2, y2, label="", lx=None, ly=None):
    parts.append(f'<path d="M{x1} {y1}L{x2} {y2}" fill="none" stroke="{TEAL}" stroke-width="4" marker-end="url(#arr)"/>')
    if label:
        parts.append(f'<text x="{lx if lx is not None else (x1+x2)/2+18}" y="{ly if ly is not None else (y1+y2)/2}" font-size="30" font-weight="600" style="fill:{TEAL}">{escape(label)}</text>')


def save(parts, name, height, footer):
    parts.append(f'<path d="M60 {height-102}H1002" stroke="#c8d1d4" stroke-width="2"/>')
    parts.append(f'<text x="60" y="{height-53}" font-size="30" style="fill:{MUTED}">{escape(footer)}</text></svg>')
    (ASSETS / name).write_text("\n".join(parts), encoding="utf-8")


def build_figures():
    ASSETS.mkdir(exist_ok=True)
    p = start(1500, "01 · 系统分工", "AI、项目记录和网页，各自负责什么", "每次继续开发，先回到有来源的记录")
    box(p,60,290,330,180,"用户",["表达需求与约束","明确回答和选择"])
    box(p,500,290,502,180,"AI 会话",["读取项目事实与 skill","澄清、比较、推进任务"],"teal")
    arrow(p,396,380,485,380)
    arrow(p,750,479,750,546,"依据明确回答回写",lx=411,ly=520)
    box(p,60,565,942,195,"项目记录 · 状态的编辑入口",["保留已有 SPEC / ADR；关联需求、任务与证据","workbench.json 是生成器读取的结构化来源"],"navy",42)
    arrow(p,300,766,300,831,"校验与生成",lx=335,ly=807)
    box(p,60,850,442,176,"校验器",["检查结构、关联与状态","不判断证据内容是否真实"])
    box(p,562,850,440,176,"生成器",["将同一份记录呈现为","首页与独立版本页面"],"teal")
    arrow(p,510,938,547,938)
    arrow(p,782,1035,782,1085)
    box(p,60,1105,942,170,"网页工作台 · 阅读与检查入口",["浏览 / 搜索 / 下钻；填写回答与选择的草稿"],"white",42)
    p.append(f'<path d="M65 1342H990" stroke="{AMBER}" stroke-width="3" stroke-dasharray="8 8"/>')
    p.append(f'<text x="60" y="1379" font-size="34" font-weight="600" style="fill:{AMBER}">用户将明确回答交给 AI → 回写记录并重新生成</text>')
    save(p,"01-system.svg",1500,"页面点击不直接改源文件；新一轮会话从项目记录继续。")

    p = start(1690,"02 · 决策的影响范围","一个选择，要落到哪些地方", "条件推演：如果用户选择“按项目统一共享”")
    box(p,60,290,942,162,"当前仍待选择 · 图中演示影响关系",["真实示例的选择字段为空，推荐不等于已决定。"],"amber",40)
    arrow(p,531,460,531,512,"明确选择之后",lx=564,ly=498)
    box(p,60,530,942,166,"需求方案 · REQ-03",["以项目为共享边界；成员只读取所属项目资料。"],"navy",42)
    arrow(p,295,704,295,760)
    arrow(p,765,704,765,760)
    box(p,60,780,442,242,"技术方案 + 技术选型",["成员与资料绑定项目","检索前先限制范围","代价：权限粒度较粗"],"teal",34)
    box(p,560,780,442,242,"视觉交互 AI 规范",["显示当前项目与范围","无权访问时给出反馈","切换项目后重查状态"],"white",35)
    arrow(p,295,1029,295,1082)
    arrow(p,765,1029,765,1082)
    box(p,60,1100,442,194,"开发计划及模式",["先定身份与范围合同","再拆分独立实现任务"],"white",38)
    box(p,560,1100,442,194,"测试规范",["两个项目、同一问题","检查是否混入越权内容"],"teal",38)
    p.append(f'<path d="M295 1304V1340H765V1304M531 1340V1380" fill="none" stroke="{TEAL}" stroke-width="4" marker-end="url(#arr)"/>')
    box(p,60,1400,942,163,"上线版本管理 · V0.2",["确定范围、核对对应证据，再判断能否推进版本。"],"navy",42)
    save(p,"02-decision-impact.svg",1690,"改变共享方案时，沿 REQ-03 的关联重查，而不只改一处标题。")


if __name__ == "__main__":
    build_figures()
