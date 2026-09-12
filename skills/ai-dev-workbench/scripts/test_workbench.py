"""Contract regressions for workbench data and safe local generation.

Run with: python3 -m unittest discover -s scripts -p test_workbench.py -v
All project data and generated output are isolated in TemporaryDirectory.
"""
from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).with_name("workbench.py")
SPEC = importlib.util.spec_from_file_location("workbench_under_test", SCRIPT)
assert SPEC and SPEC.loader
wb = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(wb)


class WorkbenchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="workbench-regression-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "project"
        self.root.mkdir()
        self.source = self.root / "docs/workbench/workbench.json"
        self.source.parent.mkdir(parents=True)
        self.report = self.root / "reports/check.md"
        self.report.parent.mkdir()
        self.report.write_text("Verified only in the local test environment.\n", encoding="utf-8")
        self.assets = Path(self.temp.name) / "test-assets"
        self.assets.mkdir()
        (self.assets / "workbench.html").write_text(
            '<!doctype html><html lang="zh-CN"><script>'
            'const DATA=__WORKBENCH_DATA__;const VERSION=__PAGE_VERSION__;'
            'const ROOT_PREFIX=__ROOT_PREFIX__;'
            '</script><body>工作台</body></html>', encoding="utf-8"
        )
        self.data = wb.blank("测试项目", "验证需求到交付的真实状态")
        self.data["project"].update(current_version="V1", sources=[{"label": "验收报告", "href": "reports/check.md"}])
        self.data["requirements"] = [{
            "id": "REQ-1", "title": "刷新后保留草稿", "problem": "编辑内容因刷新丢失", "scenario": "编辑器刷新", "priority": "P0",
            "status": "scheduled", "source": "用户反馈", "acceptance": ["刷新后内容与刷新前一致"], "version_id": "V1",
        }]
        self.data["versions"] = [{
            "id": "V1", "title": "草稿恢复", "goal": "刷新不丢草稿", "status": "local_verified",
            "product_plan": "恢复用户的编辑内容", "technical_plan": "持久化草稿并恢复", "execution_plan": "实现后验证刷新与空态",
            "next_action": "在目标环境安装并复验", "scope": ["当前编辑器草稿"], "non_goals": ["多人协作"],
            "requirements": ["REQ-1"], "risks": ["存储被浏览器清理"],
        }]
        self.data["tasks"] = [{
            "id": "TASK-1", "title": "恢复编辑器草稿", "version_id": "V1", "owner": "维护者", "module": "editor",
            "status": "accepted", "deliverable": "刷新后可恢复的编辑器", "blocker": "", "next_action": "执行目标环境验证",
            "requirement_ids": ["REQ-1"], "depends_on": [], "exit_criteria": ["正常刷新恢复内容；空草稿可用"], "evidence_ids": ["EV-1"],
        }]
        self.data["gates"] = [{
            "id": "GATE-LOCAL", "version_id": "V1", "title": "本地验证", "kind": "local", "status": "passed",
            "reason": "", "next_action": "目标环境验证", "required": True, "evidence_ids": ["EV-1"],
        }]
        self.data["evidence"] = [{
            "id": "EV-1", "version_id": "V1", "task_id": "TASK-1", "label": "本地刷新验证", "kind": "browser",
            "status": "passed", "environment": "local browser", "recorded_at": "2026-09-11T16:00:00+08:00",
            "command": "", "href": "reports/check.md", "summary": "维护者验证正常刷新与空草稿均通过。",
        }]

    def errors(self, data=None, check_links=False):
        return wb.validate(self.data if data is None else data, self.root, check_links)

    def assert_error(self, text, data=None):
        self.assertTrue(any(text in error for error in self.errors(data)), self.errors(data))

    def build(self, data=None):
        chosen = self.data if data is None else data
        self.source.write_text(json.dumps(chosen, ensure_ascii=False), encoding="utf-8")
        with patch.object(wb, "ASSETS", self.assets):
            return wb.build(chosen, self.root, self.source)

    def cli(self, *arguments):
        out, err = io.StringIO(), io.StringIO()
        with patch.object(sys, "argv", [str(SCRIPT), *arguments]), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            result = wb.main()
        return result, out.getvalue(), err.getvalue()

    def second_task(self):
        task = copy.deepcopy(self.data["tasks"][0])
        task.update(id="TASK-2", status="todo", evidence_ids=[])
        self.data["tasks"].append(task)
        return task

    def add_blueprint(self):
        """A small complete plan with one real user journey and its delivery chain."""
        self.data["blueprint"] = {
            "positioning": "让写作者刷新页面后继续编辑同一份草稿",
            "users": [{"role": "写作者", "need": "刷新不丢编辑内容", "success": "返回后继续编辑"}],
            "journey": [{
                "id": "JOURNEY-1", "title": "恢复编辑", "actor": "写作者", "action": "刷新编辑器",
                "object": "草稿", "output": "恢复后的编辑器", "module_ids": ["MOD-EDITOR"], "exception": "无草稿时显示空态",
            }],
            "modules": [{
                "id": "MOD-EDITOR", "name": "草稿编辑", "positioning": "承接输入与恢复", "value": "保留用户劳动",
                "users": ["写作者"], "stories": ["刷新后继续编辑"], "requirement_ids": ["REQ-1"],
                "pages": [{
                    "id": "PAGE-EDITOR", "name": "编辑器", "purpose": "编写和恢复草稿", "interactions": ["输入", "刷新恢复"],
                    "states": ["空草稿", "已恢复", "存储失败"], "route": "/editor", "priority": "P0",
                    "status": "built", "reality": "connected", "task_ids": ["TASK-1"], "evidence_ids": [],
                }],
                "technology": {
                    "strategy": "复用现有编辑器与持久化层", "key_tech": ["浏览器存储"], "mechanism": "输入保存，初始化恢复",
                    "objects": [{"name": "草稿", "states": ["空", "已保存"], "truth": "浏览器存储"}],
                    "apis": [{"method": "local", "path": "draft.store", "purpose": "读写草稿"}],
                    "risks": [{"risk": "存储被清理", "mitigation": "显示可见空态而不假装恢复成功"}],
                },
            }],
            "architecture": {
                "summary": "编辑器读写已有持久化层",
                "layers": [
                    {"id": "LAYER-UI", "name": "界面", "responsibility": "收集输入并恢复呈现", "module_ids": ["MOD-EDITOR"]},
                    {"id": "LAYER-STORE", "name": "存储", "responsibility": "保存草稿", "module_ids": ["MOD-EDITOR"]},
                ],
                "edges": [{"from": "LAYER-UI", "to": "LAYER-STORE", "label": "草稿读写"}],
                "flows": [{
                    "id": "FLOW-RESTORE", "title": "刷新恢复",
                    "steps": [{"from": "LAYER-STORE", "to": "LAYER-UI", "action": "读取并恢复", "data": "当前草稿"}],
                    "failure": "读取失败时显示错误与重试入口",
                }],
            },
            "development": {
                "principles": [{"title": "先验证再验收", "practice": "复现刷新场景并记录证据"}],
                "batches": [{
                    "id": "BATCH-1", "version_id": "V1", "title": "草稿恢复", "status": "current", "goal": "刷新不丢草稿",
                    "why": "先完成持久化与恢复，再开展目标环境验收", "task_ids": ["TASK-1"],
                    "entry_conditions": ["现有编辑器可编辑"], "exit_criteria": ["刷新、空草稿和失败路径通过"],
                }],
                "verification": [{"level": "浏览器", "method": "刷新前后对比", "evidence": "保存操作与结果"}],
                "sync_note": "人工更新源文件后重新生成工作台",
            },
            "evolution": [{
                "id": "DELTA-1", "version_id": "V1", "title": "刷新恢复", "problem": "刷新丢草稿", "before": "刷新后为空",
                "after": "恢复已保存草稿", "rationale": "保留用户劳动", "impact": "编辑初始化与存储", "source": "用户反馈",
            }],
        }
        return self.data["blueprint"]

    def add_second_version(self):
        version = copy.deepcopy(self.data["versions"][0])
        version.update(id="V2", status="candidate", requirements=[])
        self.data["versions"].append(version)
        return version

    def add_governance(self):
        self.data["governance"] = {
            "design": {
                "principles": [{"title": "状态可见", "rule": "保存与恢复结果应有反馈"}],
                "tokens": [{"name": "space.base", "value": "8px", "purpose": "统一间距"}],
                "components": [{"name": "编辑区", "usage": "输入与恢复草稿", "states": ["空", "编辑中", "恢复失败"]}],
                "ai_rules": ["先读页面合同，再改界面"], "checks": ["桌面和窄屏可读"], "source": "项目现有设计规范",
            },
            "stack": [{
                "id": "STACK-STORAGE", "area": "草稿存储", "choice": "复用当前持久化层", "alternatives": ["新建远程存储"],
                "why": "本轮只解决刷新恢复，不引入协作基础设施", "tradeoffs": ["设备之间不共享"],
                "status": "adopted", "version_id": "V1", "source": "SPEC 技术方案",
            }],
            "testing": {
                "strategy": "按需求验收场景验证，而不是按任务数量推断质量",
                "levels": [{"name": "浏览器", "scope": "刷新恢复", "command": "", "pass_criteria": "刷新前后内容一致", "evidence": "操作记录"}],
                "critical_paths": [{"title": "编辑刷新恢复", "steps": ["输入内容", "刷新", "对比内容"], "expected": "内容保留", "recovery": "失败时显示重试入口"}],
                "rules": ["新失败追加证据，不覆盖旧结果"], "source": "项目现有测试说明",
            },
            "releases": [{
                "id": "RELEASE-V1", "version_id": "V1", "environment": "目标安装环境", "state": "planned",
                "artifact": "待生成安装包", "recorded_at": "2026-09-11T16:00:00+08:00", "changes": ["草稿恢复"],
                "preflight": ["核对候选产物"], "deploy_steps": ["安装候选产物"], "rollback": "恢复此前产物",
                "evidence_ids": [], "notes": "仅为发布计划，尚未执行",
            }],
        }
        return self.data["governance"]

    def add_release_evidence(self, kind="deploy", version_id="V1", status="passed"):
        evidence = copy.deepcopy(self.data["evidence"][0])
        evidence.update(id="EV-RELEASE-" + kind.upper(), task_id=None, version_id=version_id, kind=kind,
                        status=status, environment="目标安装环境", label=kind, summary="维护者记录目标环境操作与结果")
        self.data["evidence"].append(evidence)
        return evidence

    def add_target_gate(self, kind, evidence_id):
        self.data["gates"].append({
            "id": "GATE-" + kind.upper(), "version_id": "V1", "title": kind, "kind": kind, "required": True,
            "status": "passed", "evidence_ids": [evidence_id], "reason": "", "next_action": "保留交付记录",
        })

    def add_discovery(self):
        self.data["discovery"] = {
            "brief": {
                "raw_request": "刷新后还想继续编辑", "users": "写作者", "problem": "刷新丢失草稿", "scenario": "刷新编辑器",
                "outcome": "恢复编辑", "success_metrics": ["刷新前后内容一致"], "constraints": ["复用现有编辑器"],
                "non_goals": ["多人协作"], "ai_role": "协助实现与验证", "baseline": "刷新后为空", "source": "本次用户请求",
            },
            "questions": [{
                "id": "QUESTION-1", "question": "是否需要跨设备恢复？", "why": "影响数据存储范围", "blocking": False,
                "requirement_ids": ["REQ-1"], "version_id": "V1", "status": "open",
                "options": [{"id": "ANSWER-LOCAL", "label": "当前设备", "description": "先覆盖浏览器刷新"},
                            {"id": "ANSWER-SHARED", "label": "跨设备", "description": "需要账号和远程保存"}],
                "selected_option_id": None, "answer": "", "answer_source": "", "answered_at": "", "next_action": "核对用户使用场景",
            }],
            "proposals": [{
                "id": "PROPOSAL-1", "title": "草稿存储范围", "question_ids": ["QUESTION-1"], "requirement_ids": ["REQ-1"],
                "version_id": "V1", "blocking": False, "options": [
                    {"id": "ROUTE-LOCAL", "title": "设备内恢复", "summary": "复用浏览器存储", "fit": "单设备使用",
                     "scope": ["刷新恢复"], "benefits": ["改动少"], "tradeoffs": ["不跨设备"], "effort": "较少",
                     "risks": ["清理存储会丢失"], "validation": "在目标浏览器刷新验证"},
                    {"id": "ROUTE-SHARED", "title": "远程草稿", "summary": "保存到账号空间", "fit": "多设备使用",
                     "scope": ["账号与同步"], "benefits": ["跨设备"], "tradeoffs": ["需要后端"], "effort": "较多",
                     "risks": ["冲突覆盖"], "validation": "用两个设备验证同步与冲突"},
                ], "recommended_option_id": "ROUTE-LOCAL", "recommendation_reason": "若当前只要求刷新恢复，可先复用现有存储",
                "status": "proposed", "selected_option_id": None, "decision": "", "decision_source": "", "decided_at": "",
            }],
            "assumptions": [{"id": "ASSUMPTION-1", "statement": "主要在单设备编辑", "risk": "可能遗漏跨设备场景",
                             "validation": "询问用户并核对使用记录", "status": "unverified", "source": ""}],
        }
        return self.data["discovery"]

    def set_discovery_pending_scope(self):
        self.data["versions"][0]["status"] = "planned"
        self.data["requirements"][0]["status"] = "idea"
        self.data["tasks"][0].update(status="todo", evidence_ids=[])

    def add_independent_requirement_task(self, version_id="V1"):
        requirement = copy.deepcopy(self.data["requirements"][0])
        requirement.update(id="REQ-2", version_id=version_id, status="scheduled")
        self.data["requirements"].append(requirement)
        next(version for version in self.data["versions"] if version["id"] == version_id)["requirements"].append("REQ-2")
        task = copy.deepcopy(self.data["tasks"][0])
        task.update(id="TASK-2", version_id=version_id, status="doing", requirement_ids=["REQ-2"], evidence_ids=[])
        self.data["tasks"].append(task)
        return task

    def test_local_verified_allows_pending_release_but_not_online_claim(self):
        self.data["gates"].append({
            "id": "GATE-DEPLOY", "version_id": "V1", "title": "目标交付", "kind": "deploy", "required": True,
            "status": "pending", "evidence_ids": [], "reason": "", "next_action": "执行真实安装",
        })
        self.assertEqual([], self.errors(check_links=True))
        self.data["project"]["online_version"] = "V1"
        self.assert_error("online_version")
        self.data["project"]["online_version"] = None
        self.data["versions"][0]["status"] = "released"
        for expected in ("必需门未通过", "deploy", "online"):
            self.assert_error(expected)

    def test_release_requires_accepted_tasks_and_target_environment_gates(self):
        self.data["versions"][0]["status"] = "released"
        self.data["project"]["online_version"] = "V1"
        for kind in ("deploy", "online"):
            eid = "EV-" + kind.upper()
            evidence = copy.deepcopy(self.data["evidence"][0])
            evidence.update(id=eid, task_id=None, kind=kind, environment="target installation", label=kind, summary="目标环境安装与操作已验证")
            self.data["evidence"].append(evidence)
            self.data["gates"].append({
                "id": "GATE-" + kind.upper(), "version_id": "V1", "title": kind, "kind": kind, "required": True,
                "status": "passed", "evidence_ids": [eid], "reason": "", "next_action": "归档",
            })
        self.assertEqual([], self.errors())
        self.data["tasks"][0]["status"] = "done"
        self.assert_error("发布版本任务未全部验收")

    def test_missing_evidence_cannot_accept_task(self):
        self.data["tasks"][0]["evidence_ids"] = []
        self.assert_error("缺少匹配的 passed 证据")

    def test_observation_or_failure_cannot_support_acceptance(self):
        for state in ("observed", "failed"):
            with self.subTest(state=state):
                self.data["evidence"][0]["status"] = state
                self.assert_error("缺少匹配的 passed 证据")

    def test_other_task_evidence_cannot_accept_task(self):
        self.second_task()
        self.data["evidence"][0]["task_id"] = "TASK-2"
        self.assert_error("属于其他版本/任务")

    def test_other_version_evidence_cannot_accept_task(self):
        version = copy.deepcopy(self.data["versions"][0])
        version.update(id="V2", status="candidate", requirements=[])
        self.data["versions"].append(version)
        self.data["evidence"][0].update(version_id="V2", task_id=None)
        self.assert_error("属于其他版本/任务")

    def test_dependency_cycle_and_self_dependency_are_rejected(self):
        task = self.second_task()
        self.data["tasks"][0]["status"] = "todo"
        self.data["tasks"][0]["depends_on"] = [task["id"]]
        task["depends_on"] = ["TASK-1"]
        self.assert_error("依赖成环")
        self.data["tasks"] = [self.data["tasks"][0]]
        self.data["tasks"][0]["depends_on"] = ["TASK-1"]
        self.assert_error("依赖成环")

    def test_dangling_dependency_requirement_and_evidence_rejected(self):
        for field, value, expected in (
            ("depends_on", ["MISSING"], "依赖 MISSING 不存在"),
            ("requirement_ids", ["MISSING"], "需求 MISSING 与任务版本不匹配"),
            ("evidence_ids", ["MISSING"], "证据 MISSING 不存在"),
        ):
            with self.subTest(field=field):
                data = copy.deepcopy(self.data)
                data["tasks"][0][field] = value
                self.assert_error(expected, data)

    def test_acceptance_requires_completed_dependencies(self):
        task = self.second_task()
        self.data["tasks"][0]["depends_on"] = [task["id"]]
        self.assert_error("依赖 TASK-2 未完成")
        task["status"] = "done"
        self.assertEqual([], self.errors())

    def test_requirement_acceptance_requires_all_linked_tasks(self):
        self.data["requirements"][0]["status"] = "accepted"
        self.second_task()
        self.assert_error("关联任务尚未全部验收")

    def test_requirement_version_binding_is_bidirectional(self):
        self.data["versions"][0]["requirements"] = []
        self.assert_error("关联不一致")

    def test_blocked_task_requires_reason_and_next_action(self):
        self.data["tasks"][0].update(status="blocked", blocker="", next_action="")
        self.assert_error("阻塞缺少原因/下一步")

    def test_duplicate_id_is_rejected_across_object_types(self):
        self.data["tasks"][0]["id"] = "REQ-1"
        self.assert_error("ID 重复")

    def test_bad_schema_returns_errors_instead_of_crashing(self):
        for data in (None, [], {}, {"schema_version": True}, {**self.data, "tasks": [None]}, {**self.data, "gates": None}):
            with self.subTest(data_type=type(data).__name__):
                self.assertTrue(wb.validate(data, self.root))
        malformed = copy.deepcopy(self.data)
        malformed["tasks"][0]["depends_on"] = [123]
        self.assertTrue(self.errors(malformed))

    def test_empty_project_is_valid_and_buildable_without_fake_progress(self):
        data = wb.blank("空项目", "等待核查事实")
        self.assertEqual([], self.errors(data, check_links=True))
        pages = self.build(data)
        self.assertEqual([self.source.parent / "index.html"], pages)
        html = pages[0].read_text(encoding="utf-8")
        self.assertIn('"current_version": null', html)
        self.assertIn('"tasks": []', html)
        self.assertEqual([], data.get("blueprint", {}).get("modules", []))
        self.assertEqual([], data.get("governance", {}).get("releases", []))
        self.assertEqual([], data.get("governance", {}).get("stack", []))

    def test_source_file_links_are_rebased_and_encoded_without_mutating_data(self):
        chinese = self.root / "docs/说明 文档.md"
        chinese.write_text("# 说明\n", encoding="utf-8")
        self.data["project"]["sources"] = [
            {"label": "源说明", "href": "docs/说明%20文档.md?view=1#details"},
            {"label": "官方说明", "href": "https://example.org/docs?q=1#usage"},
        ]
        before = copy.deepcopy(self.data)
        result = wb.browser_data(self.data, self.root, self.source.parent)
        self.assertEqual("../%E8%AF%B4%E6%98%8E%20%E6%96%87%E6%A1%A3.md?view=1#details", result["project"]["sources"][0]["href"])
        for original, rendered in zip(before["project"]["sources"], result["project"]["sources"]):
            self.assertEqual(original["label"], rendered["label"])
            self.assertEqual(original["href"], rendered["_source_href"])
        self.assertEqual(before["project"]["sources"][1]["href"], result["project"]["sources"][1]["href"])
        self.assertEqual(before, self.data)
        self.assertEqual([], self.errors(check_links=True))

    def test_windows_relpath_outputs_are_normalized_before_url_encoding(self):
        """Simulate Windows separators; this is not a Windows runtime smoke test."""
        original = wb.os.path.relpath
        before = copy.deepcopy(self.data)
        with patch.object(wb.os.path, "relpath", side_effect=lambda *args, **kwargs: original(*args, **kwargs).replace("/", "\\")):
            result = wb.browser_data(self.data, self.root, self.source.parent)
        self.assertEqual("docs/workbench/workbench.json", result["_source_file"])
        self.assertEqual("../../reports/check.md", result["project"]["sources"][0]["href"])
        self.assertEqual("../../reports/check.md", result["evidence"][0]["href"])
        self.assertEqual("reports/check.md", result["evidence"][0]["_source_href"])
        self.assertNotIn("%5C", json.dumps(result))
        self.assertEqual(before, self.data)

    def test_missing_local_link_is_a_build_error_but_optional_in_structure_check(self):
        self.report.unlink()
        self.assertEqual([], self.errors())
        self.assertTrue(any("本地链接文件不存在" in x for x in self.errors(check_links=True)))
        with self.assertRaisesRegex(ValueError, "本地链接文件不存在"):
            self.build()

    def test_script_closing_strings_and_placeholder_names_remain_inert_data(self):
        hostile = '</script><script>alert("x")</script> & __PAGE_VERSION__ __ROOT_PREFIX__ __WORKBENCH_DATA__'
        self.data["project"]["name"] = hostile
        pages = self.build()
        expected = wb.safe_json(wb.browser_data(self.data, self.root, self.source.parent))
        for page in pages:
            with self.subTest(page=page.name):
                html = page.read_text(encoding="utf-8")
                self.assertIn(expected, html)
                self.assertNotIn('</script><script>alert', html)
                self.assertEqual(1, html.count("</script>"))
                match = html.split("const DATA=", 1)[1].split(";const VERSION=", 1)[0]
                self.assertEqual(hostile, json.loads(match)["project"]["name"])

    def test_generated_pages_update_without_touching_source_content(self):
        pages = self.build()
        self.assertEqual(2, len(pages))
        before = pages[0].read_text(encoding="utf-8")
        self.data["project"]["next_action"] = "再次核查后补充目标环境证据"
        self.build()
        after = pages[0].read_text(encoding="utf-8")
        self.assertNotEqual(before, after)
        self.assertIn(self.data["project"]["next_action"], after)
        self.assertEqual(self.data, json.loads(self.source.read_text(encoding="utf-8")))
        self.assertEqual(1, after.count(wb.MARKER))

    def test_preflight_refuses_existing_human_page_before_updating_any_page(self):
        pages = self.build()
        old_index = pages[0].read_bytes()
        human_page = pages[1]
        human_page.write_text("<!doctype html><h1>人工文档，禁止覆盖</h1>", encoding="utf-8")
        old_human = human_page.read_bytes()
        self.data["project"]["next_action"] = "这次更新必须被完整阻断"
        with self.assertRaisesRegex(ValueError, "拒绝覆盖"):
            self.build()
        self.assertEqual(old_index, pages[0].read_bytes())
        self.assertEqual(old_human, human_page.read_bytes())

    def test_unsafe_local_urls_rejected_even_without_check_links(self):
        for href in ("../outside.md", "%2e%2e/outside.md", "/etc/passwd", "file:///etc/passwd", "javascript:alert(1)", "//other.example/file", "docs\\other.md", "docs/file\n.md"):
            with self.subTest(href=href):
                data = copy.deepcopy(self.data)
                data["project"]["sources"][0]["href"] = href
                self.assertTrue(self.errors(data))

    def test_symlink_link_escape_is_rejected(self):
        outside = Path(self.temp.name) / "outside.md"
        outside.write_text("private", encoding="utf-8")
        (self.root / "outside-link.md").symlink_to(outside)
        self.data["project"]["sources"][0]["href"] = "outside-link.md"
        self.assert_error("路径超出项目根目录")

    def test_symlink_output_escape_is_rejected_before_any_page_write(self):
        outside = Path(self.temp.name) / "outside-output"
        outside.mkdir()
        (self.source.parent / "versions").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "输出路径超出项目根目录"):
            self.build()
        self.assertFalse((self.source.parent / "index.html").exists())
        self.assertEqual([], list(outside.iterdir()))

    def test_init_duplicate_does_not_overwrite_existing_source(self):
        args = ("init", "--project-root", str(self.root), "--name", "首次项目", "--purpose", "真实项目目的")
        result, _, err = self.cli(*args)
        self.assertEqual(0, result, err)
        before = self.source.read_bytes()
        result, _, _ = self.cli(*args)
        self.assertEqual(1, result)
        self.assertEqual(before, self.source.read_bytes())

    def test_init_and_data_path_escape_fail_without_writing_outside(self):
        result, _, err = self.cli("init", "--project-root", str(self.root), "--directory", "../escape", "--name", "项目", "--purpose", "用途")
        self.assertEqual(1, result)
        self.assertIn("不得超出项目根目录", err)
        self.assertFalse((Path(self.temp.name) / "escape").exists())
        outside = Path(self.temp.name) / "workbench.json"
        outside.write_text(json.dumps(self.data), encoding="utf-8")
        result, _, err = self.cli("validate", "--project-root", str(self.root), "--data", str(outside))
        self.assertEqual(1, result)
        self.assertIn("源文件必须位于项目根目录内", err)

    def test_cli_invalid_json_is_actionable_and_nonzero(self):
        self.source.write_text("{bad json", encoding="utf-8")
        result, _, err = self.cli("validate", "--project-root", str(self.root), "--data", str(self.source))
        self.assertEqual(1, result)
        self.assertIn("未完成", err)
        self.assertNotIn("Traceback", err)

    def test_complete_blueprint_validates_and_builds_without_promoting_page_status(self):
        bp = self.add_blueprint()
        before = copy.deepcopy(self.data)
        self.assertEqual([], self.errors(check_links=True))
        pages = self.build()
        rendered = wb.browser_data(self.data, self.root, self.source.parent)
        page = rendered["blueprint"]["modules"][0]["pages"][0]
        self.assertEqual(("built", "connected", []), (page["status"], page["reality"], page["evidence_ids"]))
        self.assertEqual(before, self.data)
        self.assertEqual(2, len(pages))
        self.assertIn(bp["positioning"], pages[0].read_text(encoding="utf-8"))

    def test_page_verified_requires_its_own_matching_passed_evidence(self):
        self.add_blueprint()
        # An accepted backend/task record does not independently verify the page.
        for field in ("status", "reality"):
            with self.subTest(field=field):
                data = copy.deepcopy(self.data)
                page = data["blueprint"]["modules"][0]["pages"][0]
                page[field] = "verified"
                self.assert_error("PAGE-EDITOR: verified 缺少匹配的 passed 证据", data)
                page["evidence_ids"] = ["EV-1"]
                self.assertEqual([], self.errors(data))
                for state in ("observed", "failed"):
                    data["evidence"][0]["status"] = state
                    self.assert_error("PAGE-EDITOR: verified 缺少匹配的 passed 证据", data)

    def test_page_cannot_use_passed_evidence_from_other_version_or_task(self):
        self.add_blueprint()
        self.add_second_version()
        self.second_task()
        page = self.data["blueprint"]["modules"][0]["pages"][0]
        page.update(status="verified", evidence_ids=["EV-OTHER"])
        unrelated = copy.deepcopy(self.data["evidence"][0])
        unrelated.update(id="EV-OTHER", version_id="V2", task_id=None)
        self.data["evidence"].append(unrelated)
        self.assert_error("PAGE-EDITOR: 证据 EV-OTHER 与页面关联版本/任务不匹配")
        self.assert_error("PAGE-EDITOR: verified 缺少匹配的 passed 证据")
        unrelated.update(version_id="V1", task_id="TASK-2")
        self.assert_error("PAGE-EDITOR: 证据 EV-OTHER 与页面关联版本/任务不匹配")
        unrelated.update(task_id="TASK-1")
        self.assertEqual([], self.errors())

    def test_page_without_version_relationship_cannot_be_verified_by_arbitrary_evidence(self):
        bp = self.add_blueprint()
        bp["modules"][0]["requirement_ids"] = []
        bp["modules"][0]["pages"][0].update(task_ids=[], status="verified", evidence_ids=["EV-1"])
        self.assert_error("PAGE-EDITOR: 证据 EV-1 与页面关联版本/任务不匹配")

    def test_blueprint_rejects_missing_module_requirement_page_batch_and_evolution_references(self):
        self.add_blueprint()
        cases = [
            (("journey", 0, "module_ids"), ["MISSING"], "JOURNEY-1: 模块 MISSING 不存在"),
            (("architecture", "layers", 0, "module_ids"), ["MISSING"], "LAYER-UI: 模块 MISSING 不存在"),
            (("modules", 0, "requirement_ids"), ["MISSING"], "MOD-EDITOR: 需求 MISSING 不存在"),
            (("modules", 0, "pages", 0, "task_ids"), ["MISSING"], "PAGE-EDITOR: 任务 MISSING 不存在"),
            (("modules", 0, "pages", 0, "evidence_ids"), ["MISSING"], "PAGE-EDITOR: 证据 MISSING 不存在"),
            (("development", "batches", 0, "version_id"), "MISSING", "BATCH-1: 版本不存在"),
            (("development", "batches", 0, "task_ids"), ["MISSING"], "BATCH-1: 任务 MISSING 与批次版本不一致"),
            (("evolution", 0, "version_id"), "MISSING", "DELTA-1: 演进版本不存在"),
        ]
        for path, value, expected in cases:
            with self.subTest(path=path):
                data = copy.deepcopy(self.data)
                target = data["blueprint"]
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = value
                self.assert_error(expected, data)

    def test_architecture_edges_require_layer_ids_but_flow_steps_allow_human_descriptions(self):
        self.add_blueprint()
        for endpoint in ("from", "to"):
            with self.subTest(endpoint=endpoint):
                data = copy.deepcopy(self.data)
                data["blueprint"]["architecture"]["edges"][0][endpoint] = "MISSING-LAYER"
                errors = self.errors(data)
                self.assertTrue(any("MISSING-LAYER" in error for error in errors), errors)
        # Data-flow steps describe actors and services; they are not foreign keys.
        self.data["blueprint"]["architecture"]["flows"][0]["steps"][0].update(**{
            "from": "用户", "to": "外部模型服务", "action": "提交待处理内容", "data": "用户输入",
        })
        self.assertEqual([], self.errors())

    def test_batch_rejects_cross_version_tasks_and_missing_sequence_rationale(self):
        bp = self.add_blueprint()
        self.add_second_version()
        batch = bp["development"]["batches"][0]
        batch["version_id"] = "V2"
        self.assert_error("BATCH-1: 任务 TASK-1 与批次版本不一致")
        batch["version_id"] = "V1"
        for field, empty in (("why", " "), ("exit_criteria", [])):
            with self.subTest(field=field):
                data = copy.deepcopy(self.data)
                data["blueprint"]["development"]["batches"][0][field] = empty
                self.assert_error("BATCH-1: 缺少批次顺序依据/退出条件", data)

    def test_blueprint_ids_are_unique_across_base_records_and_nested_entities(self):
        self.add_blueprint()
        for duplicate in ("REQ-1", "MOD-EDITOR", "BATCH-1", "FLOW-RESTORE"):
            with self.subTest(duplicate=duplicate):
                data = copy.deepcopy(self.data)
                data["blueprint"]["modules"][0]["pages"][0]["id"] = duplicate
                self.assert_error("ID 重复 " + duplicate, data)

    def test_blueprint_rejects_unknown_page_priority_status_reality_and_batch_state(self):
        self.add_blueprint()
        for field, value, message in (
            ("priority", "P9", "priority 非法"), ("status", "accepted", "页面状态非法"), ("reality", "done", "真实度状态非法"),
        ):
            with self.subTest(field=field):
                data = copy.deepcopy(self.data)
                data["blueprint"]["modules"][0]["pages"][0][field] = value
                self.assert_error(message, data)
        self.data["blueprint"]["development"]["batches"][0]["status"] = "released"
        self.assert_error("批次状态非法")

    def test_malformed_nested_blueprint_returns_actionable_errors_without_crashing(self):
        self.add_blueprint()
        cases = [
            ((), None), ((), []), (("users",), {}), (("journey",), [None]),
            (("modules", 0, "pages"), [123]), (("modules", 0, "technology", "objects"), "not a list"),
            (("modules", 0, "pages", 0, "task_ids"), [None]), (("architecture", "edges"), [False]),
            (("architecture", "flows", 0, "steps"), [{}]), (("development", "batches", 0, "why"), None),
            (("evolution",), [None]),
        ]
        for path, value in cases:
            with self.subTest(path=path, value=value):
                data = copy.deepcopy(self.data)
                if not path:
                    data["blueprint"] = value
                else:
                    target = data["blueprint"]
                    for key in path[:-1]:
                        target = target[key]
                    target[path[-1]] = value
                errors = self.errors(data)
                self.assertTrue(errors)
                self.assertTrue(all(isinstance(error, str) for error in errors))
                self.assertTrue(any("blueprint" in error for error in errors), errors)

    def test_passed_gate_cannot_borrow_evidence_from_another_version(self):
        self.add_second_version()
        evidence = copy.deepcopy(self.data["evidence"][0])
        evidence.update(id="EV-V2", version_id="V2", task_id=None)
        self.data["evidence"].append(evidence)
        self.data["gates"][0]["evidence_ids"] = ["EV-V2"]
        self.assert_error("GATE-LOCAL: 证据 EV-V2 属于其他版本/任务")
        self.assert_error("GATE-LOCAL: 通过/验收状态缺少匹配的 passed 证据")

    def test_complete_governance_integrates_with_blueprint_without_executing_release_plan(self):
        self.add_blueprint()
        self.add_governance()
        before = copy.deepcopy(self.data)
        self.assertEqual([], self.errors(check_links=True))
        pages = self.build()
        rendered = wb.browser_data(self.data, self.root, self.source.parent)
        self.assertEqual("planned", rendered["governance"]["releases"][0]["state"])
        self.assertEqual("local_verified", rendered["versions"][0]["status"])
        self.assertIsNone(rendered["project"]["online_version"])
        self.assertEqual(before, self.data)
        self.assertIn("状态可见", pages[0].read_text(encoding="utf-8"))

    def test_historical_release_without_live_evidence_stays_unverified(self):
        gov = self.add_governance()
        self.data["versions"][0]["status"] = "archived"
        gov["releases"][0].update(state="historical", artifact="旧记录中的交付产物", notes="只有历史记录，没有现场验收证据")
        self.assertEqual([], self.errors())
        rendered = wb.browser_data(self.data, self.root, self.source.parent)
        self.assertEqual("historical", rendered["governance"]["releases"][0]["state"])
        self.assertEqual("archived", rendered["versions"][0]["status"])
        self.assertIsNone(rendered["project"]["online_version"])

    def test_release_execution_states_require_matching_passed_evidence(self):
        self.add_governance()
        evidence = self.add_release_evidence()
        self.add_target_gate("deploy", evidence["id"])
        for state in ("deployed", "verified", "rolled_back"):
            for evidence_state in (None, "observed", "failed"):
                with self.subTest(state=state, evidence_state=evidence_state):
                    data = copy.deepcopy(self.data)
                    release = data["governance"]["releases"][0]
                    release["state"] = state
                    if evidence_state is not None:
                        release["evidence_ids"] = [evidence["id"]]
                        data["evidence"][-1]["status"] = evidence_state
                    self.assert_error("RELEASE-V1: 发布事实缺少匹配的 passed 证据", data)

    def test_deployed_release_requires_deploy_gate_without_claiming_target_acceptance(self):
        gov = self.add_governance()
        evidence = self.add_release_evidence()
        gov["releases"][0].update(state="deployed", evidence_ids=[evidence["id"]])
        self.assert_error("RELEASE-V1: 发布缺少 deploy 通过记录")
        self.add_target_gate("deploy", evidence["id"])
        self.assertEqual([], self.errors())
        self.assertEqual("local_verified", self.data["versions"][0]["status"])
        self.assertIsNone(self.data["project"]["online_version"])

    def test_verified_release_requires_version_exit_conditions_and_target_regression(self):
        gov = self.add_governance()
        deploy = self.add_release_evidence("deploy")
        self.add_target_gate("deploy", deploy["id"])
        gov["releases"][0].update(state="verified", evidence_ids=[deploy["id"]])
        self.assert_error("RELEASE-V1: verified 发布必须关联已验收交付版本")
        self.data["versions"][0]["status"] = "released"
        self.assert_error("V1: 缺少 online 通过证据")
        online = self.add_release_evidence("online")
        self.add_target_gate("online", online["id"])
        gov["releases"][0]["evidence_ids"].append(online["id"])
        self.data["project"]["online_version"] = "V1"
        self.assertEqual([], self.errors(check_links=True))
        self.data["tasks"][0]["status"] = "done"
        self.assert_error("V1: 发布版本任务未全部验收")

    def test_release_evidence_cannot_come_from_another_version(self):
        gov = self.add_governance()
        self.add_second_version()
        evidence = self.add_release_evidence("rollback", version_id="V2")
        gov["releases"][0].update(state="rolled_back", evidence_ids=[evidence["id"]])
        self.assert_error("RELEASE-V1: 发布证据版本不匹配")
        self.assert_error("RELEASE-V1: 发布事实缺少匹配的 passed 证据")
        evidence["version_id"] = "V1"
        self.assertEqual([], self.errors())

    def test_governance_rejects_missing_release_version_evidence_and_invalid_date_or_state(self):
        self.add_governance()
        for field, value, message in (
            ("version_id", "MISSING", "发布版本不存在"),
            ("evidence_ids", ["MISSING"], "发布证据 MISSING 不存在"),
            ("recorded_at", "昨天", "发布记录日期必须为 ISO 8601"),
            ("state", "accepted", "发布记录状态非法"),
        ):
            with self.subTest(field=field):
                data = copy.deepcopy(self.data)
                data["governance"]["releases"][0][field] = value
                self.assert_error(message, data)

    def test_stack_choices_support_global_or_version_scope_but_require_reason_and_source(self):
        gov = self.add_governance()
        choice = gov["stack"][0]
        choice["version_id"] = None
        self.assertEqual([], self.errors())
        for field, value, message in (
            ("version_id", "MISSING", "选型关联版本不存在"),
            ("status", "verified", "选型状态非法"),
            ("why", " ", "选型缺少理由或来源"),
            ("source", "", "选型缺少理由或来源"),
        ):
            with self.subTest(field=field):
                data = copy.deepcopy(self.data)
                data["governance"]["stack"][0][field] = value
                self.assert_error(message, data)

    def test_governance_ids_are_unique_across_blueprint_base_and_governance_records(self):
        self.add_blueprint()
        self.add_governance()
        for duplicate in ("REQ-1", "PAGE-EDITOR", "STACK-STORAGE"):
            with self.subTest(duplicate=duplicate):
                data = copy.deepcopy(self.data)
                data["governance"]["releases"][0]["id"] = duplicate
                self.assert_error("治理记录 ID 重复: " + duplicate, data)
        self.data["governance"]["stack"][0]["id"] = "invalid id"
        self.assert_error("治理记录 ID 非法")

    def test_malformed_governance_returns_errors_instead_of_crashing(self):
        self.add_governance()
        cases = [
            ((), None), ((), []), (("design",), []), (("design", "components"), [None]),
            (("design", "tokens", 0, "value"), {}), (("stack",), [None]), (("stack", 0, "version_id"), []),
            (("testing", "critical_paths", 0, "steps"), [None]), (("releases",), [False]),
            (("releases", 0, "recorded_at"), 123), (("releases", 0, "evidence_ids"), "EV-1"),
        ]
        for path, value in cases:
            with self.subTest(path=path, value=value):
                data = copy.deepcopy(self.data)
                if not path:
                    data["governance"] = value
                else:
                    target = data["governance"]
                    for key in path[:-1]:
                        target = target[key]
                    target[path[-1]] = value
                errors = self.errors(data)
                self.assertTrue(errors)
                self.assertTrue(all(isinstance(error, str) for error in errors))
                self.assertTrue(any("governance" in error for error in errors), errors)
        del self.data["governance"]["stack"][0]["version_id"]
        self.assert_error("version_id 缺少字段")

    def test_cli_malformed_governance_fails_cleanly_and_preserves_existing_output(self):
        self.add_governance()
        pages = self.build()
        before = {page: page.read_bytes() for page in pages}
        self.data["governance"]["releases"] = [None]
        self.source.write_text(json.dumps(self.data), encoding="utf-8")
        result, _, err = self.cli("build", "--project-root", str(self.root), "--data", str(self.source))
        self.assertEqual(1, result)
        self.assertIn("governance.releases[0]", err)
        self.assertNotIn("Traceback", err)
        self.assertEqual(before, {page: page.read_bytes() for page in pages})

    def test_new_init_has_empty_discovery_without_fabricated_answers_or_blockers(self):
        result, _, err = self.cli("init", "--project-root", str(self.root), "--name", "新项目", "--purpose", "待澄清的用户目标")
        self.assertEqual(0, result, err)
        data = json.loads(self.source.read_text(encoding="utf-8"))
        discovery = data["discovery"]
        self.assertEqual({"brief", "questions", "proposals", "assumptions"}, set(discovery))
        self.assertEqual("", discovery["brief"]["raw_request"])
        self.assertEqual([], discovery["brief"]["success_metrics"])
        for collection in ("questions", "proposals", "assumptions"):
            self.assertEqual([], discovery[collection])
        self.assertEqual([], self.errors(data))
        self.assertIs(False, wb.empty_shape("B"))
        self.assertEqual([], wb.shape_errors(False, "B", "blocking"))

    def test_legacy_schema_without_discovery_remains_valid_and_buildable(self):
        for key in ("discovery", "blueprint", "governance"):
            self.data.pop(key, None)
        before = copy.deepcopy(self.data)
        self.assertEqual([], self.errors(check_links=True))
        self.build()
        self.assertEqual(before, self.data)
        self.assertNotIn("discovery", json.loads(self.source.read_text(encoding="utf-8")))

    def test_recommendation_does_not_select_a_proposal_or_answer_a_question(self):
        self.add_discovery()
        before = copy.deepcopy(self.data)
        self.assertEqual([], self.errors())
        rendered = wb.browser_data(self.data, self.root, self.source.parent)["discovery"]
        proposal = rendered["proposals"][0]
        self.assertEqual("ROUTE-LOCAL", proposal["recommended_option_id"])
        self.assertEqual("proposed", proposal["status"])
        self.assertIsNone(proposal["selected_option_id"])
        self.assertEqual("open", rendered["questions"][0]["status"])
        self.assertEqual(before, self.data)
        self.data["discovery"]["proposals"][0]["blocking"] = True
        self.assert_error("PROPOSAL-1: 未决事项阻塞需求 REQ-1")

    def test_answered_question_accepts_free_text_or_its_own_option_with_provenance(self):
        discovery = self.add_discovery()
        question = discovery["questions"][0]
        question.update(status="answered", blocking=True, answer="现在只用电脑，之后再考虑手机", answer_source="用户本轮明确回复",
                        answered_at="2026-09-11T17:30:00+08:00")
        self.assertIsNone(question["selected_option_id"])
        self.assertEqual([], self.errors())
        question["selected_option_id"] = "ANSWER-LOCAL"
        self.assertEqual([], self.errors())

    def test_selected_proposal_accepts_custom_combination_without_silently_choosing_recommendation(self):
        discovery = self.add_discovery()
        proposal = discovery["proposals"][0]
        proposal.update(status="selected", blocking=True, decision="先设备内恢复，再提供手动备份；暂不做账号同步",
                        decision_source="用户本轮组合方案回复", decided_at="2026-09-11", selected_option_id=None)
        self.assertEqual([], self.errors())
        self.assertIsNone(proposal["selected_option_id"])
        self.assertEqual("ROUTE-LOCAL", proposal["recommended_option_id"])
        proposal["selected_option_id"] = "ROUTE-SHARED"
        self.assertEqual([], self.errors())

    def test_answer_and_decision_require_nonempty_source_content_and_iso_dates(self):
        discovery = self.add_discovery()
        discovery["questions"][0].update(status="answered", answer="当前设备", answer_source="用户回复", answered_at="2026-09-11T09:00:00Z")
        discovery["proposals"][0].update(status="selected", decision="设备内恢复", decision_source="用户回复", decided_at="2026-09-11")
        self.assertEqual([], self.errors())
        for collection, content, source, timestamp in (
            ("questions", "answer", "answer_source", "answered_at"),
            ("proposals", "decision", "decision_source", "decided_at"),
        ):
            for field, value in ((content, " "), (source, ""), (timestamp, ""), (timestamp, "昨天"), (timestamp, "2026-13-40")):
                with self.subTest(collection=collection, field=field, value=value):
                    data = copy.deepcopy(self.data)
                    data["discovery"][collection][0][field] = value
                    self.assertTrue(self.errors(data))

    def test_open_question_and_unselected_proposal_cannot_hold_prefilled_answer_or_choice(self):
        self.add_discovery()
        for collection, changes, expected in (
            ("questions", {"selected_option_id": "ANSWER-LOCAL"}, "未回答问题不得预填"),
            ("questions", {"answer": "默认答案"}, "未回答问题不得预填"),
            ("questions", {"answer_source": "AI 推断"}, "未回答问题不得预填"),
            ("questions", {"answered_at": "2026-09-11"}, "未回答问题不得预填"),
            ("proposals", {"selected_option_id": "ROUTE-LOCAL"}, "未选择方案不得预填 selected_option_id"),
            ("proposals", {"decision": "自动采用推荐"}, "未选择方案不得预填决策记录"),
        ):
            with self.subTest(collection=collection, changes=changes):
                data = copy.deepcopy(self.data)
                data["discovery"][collection][0].update(changes)
                self.assert_error(expected, data)

    def test_selected_and_recommended_options_must_belong_to_their_own_group(self):
        discovery = self.add_discovery()
        discovery["questions"][0].update(status="answered", answer="已有回复", answer_source="用户回复", answered_at="2026-09-11")
        discovery["proposals"][0].update(status="selected", decision="已有决策", decision_source="用户回复", decided_at="2026-09-11")
        for collection, field, option in (
            ("questions", "selected_option_id", "ROUTE-LOCAL"),
            ("proposals", "selected_option_id", "ANSWER-LOCAL"),
            ("proposals", "recommended_option_id", "ANSWER-LOCAL"),
        ):
            with self.subTest(collection=collection, field=field):
                data = copy.deepcopy(self.data)
                data["discovery"][collection][0][field] = option
                self.assert_error(field + " 不属于本组选项", data)

    def test_proposal_comparison_needs_two_choices_and_reason_for_recommendation(self):
        discovery = self.add_discovery()
        discovery["proposals"][0]["recommendation_reason"] = " "
        self.assert_error("推荐方案缺少推荐理由")
        discovery["proposals"][0]["recommended_option_id"] = None
        self.assertEqual([], self.errors())
        discovery["proposals"][0]["options"] = discovery["proposals"][0]["options"][:1]
        self.assert_error("方案比较至少需要两个选项")

    def test_requirement_scope_blocks_only_related_implementation_and_version_exit(self):
        discovery = self.add_discovery()
        question = discovery["questions"][0]
        question["blocking"] = True
        for expected in ("需求 REQ-1", "任务 TASK-1", "版本 V1"):
            self.assert_error("QUESTION-1: 未决事项阻塞" + expected)
        self.set_discovery_pending_scope()
        self.data["versions"][0]["status"] = "in_progress"
        self.add_independent_requirement_task()
        self.assertEqual([], self.errors())
        self.data["tasks"].append({**copy.deepcopy(self.data["tasks"][0]), "id": "TASK-RESEARCH", "title": "独立数据研究",
                                   "status": "doing", "requirement_ids": [], "evidence_ids": []})
        self.assertEqual([], self.errors())
        self.data["versions"][0]["status"] = "local_verified"
        self.assert_error("QUESTION-1: 未决事项阻塞版本 V1 的 local_verified")

    def test_scope_status_matrix_allows_paused_records_but_not_confirmed_or_implemented_work(self):
        self.add_discovery()["questions"][0]["blocking"] = True
        self.set_discovery_pending_scope()
        for status in ("ready", "scheduled", "accepted"):
            with self.subTest(requirement_status=status):
                data = copy.deepcopy(self.data)
                data["requirements"][0]["status"] = status
                self.assert_error("QUESTION-1: 未决事项阻塞需求 REQ-1 的 " + status, data)
        for status in ("doing", "done", "accepted"):
            with self.subTest(task_status=status):
                data = copy.deepcopy(self.data)
                data["tasks"][0]["status"] = status
                self.assert_error("QUESTION-1: 未决事项阻塞任务 TASK-1 的 " + status, data)
        self.data["tasks"][0].update(status="blocked", blocker="等待范围答案", next_action="澄清后恢复")
        self.assertEqual([], self.errors())

    def test_version_scope_leaves_other_versions_running_and_global_scope_reaches_them(self):
        discovery = self.add_discovery()
        question = discovery["questions"][0]
        question.update(blocking=True, requirement_ids=[])
        self.set_discovery_pending_scope()
        self.add_second_version()["status"] = "in_progress"
        self.add_independent_requirement_task("V2")
        self.assertEqual([], self.errors())
        self.data["versions"][0]["status"] = "in_progress"
        self.assert_error("QUESTION-1: 未决事项阻塞版本 V1 的 in_progress")
        self.data["versions"][0]["status"] = "planned"
        question["version_id"] = None
        for expected in ("需求 REQ-2", "任务 TASK-2", "版本 V2"):
            self.assert_error("QUESTION-1: 未决事项阻塞" + expected)

    def test_project_blocker_does_not_reopen_archived_version_or_accepted_history(self):
        discovery = self.add_discovery()
        discovery["questions"][0].update(blocking=True, requirement_ids=[], version_id=None)
        self.data["versions"][0]["status"] = "archived"
        self.data["requirements"][0]["status"] = "accepted"
        before = copy.deepcopy(self.data)
        self.assertEqual([], self.errors())
        self.assertEqual(before, self.data)

    def test_nonblocking_questions_do_not_require_filling_brief_or_pause_implementation(self):
        discovery = self.add_discovery()
        discovery["brief"] = wb.empty_shape(wb.DISCOVERY_SHAPE["brief"])
        self.assertEqual([], self.errors())
        self.assertEqual("accepted", self.data["tasks"][0]["status"])

    def test_deferred_question_needs_next_action_and_still_blocks_its_scope(self):
        question = self.add_discovery()["questions"][0]
        question.update(status="deferred", blocking=True, next_action="")
        self.assert_error("暂缓问题缺少可执行下一步")
        question["next_action"] = "用两种设备做一轮使用访谈后回答"
        self.assert_error("QUESTION-1: 未决事项阻塞任务 TASK-1")
        self.set_discovery_pending_scope()
        self.assertEqual([], self.errors())

    def test_answered_question_does_not_resolve_a_blocking_proposal_and_vice_versa(self):
        discovery = self.add_discovery()
        question, proposal = discovery["questions"][0], discovery["proposals"][0]
        question.update(blocking=True, status="answered", answer="目前用一台电脑", answer_source="用户回复", answered_at="2026-09-11")
        proposal.update(blocking=True, status="deferred")
        self.assert_error("PROPOSAL-1: 未决事项阻塞需求 REQ-1")
        proposal.update(status="selected", decision="采用设备内恢复", decision_source="用户回复", decided_at="2026-09-11")
        self.assertEqual([], self.errors())
        question.update(status="open", answer="", answer_source="", answered_at="")
        self.assert_error("QUESTION-1: 未决事项阻塞需求 REQ-1")

    def test_superseded_proposal_can_keep_history_but_requires_replacement_note(self):
        proposal = self.add_discovery()["proposals"][0]
        proposal.update(status="superseded", blocking=True)
        self.assert_error("superseded 必须在 decision 说明替代情况")
        proposal.update(decision="原设备内方案由新的手动备份组合方案替代", decision_source="用户调整范围", decided_at="2026-09-11")
        self.assertEqual([], self.errors())
        proposal["selected_option_id"] = "ROUTE-LOCAL"
        self.assert_error("未选择方案不得预填 selected_option_id")

    def test_discovery_references_require_existing_matching_scope_and_allow_unscheduled_requirements(self):
        self.add_discovery()
        self.add_second_version()
        for collection, field, value, expected in (
            ("questions", "requirement_ids", ["MISSING"], "澄清需求 MISSING 不存在"),
            ("questions", "version_id", "MISSING", "澄清关联版本不存在"),
            ("proposals", "question_ids", ["MISSING"], "关联问题 MISSING 不存在"),
            ("proposals", "version_id", "V2", "需求 REQ-1 与澄清版本不一致"),
        ):
            with self.subTest(collection=collection, field=field):
                data = copy.deepcopy(self.data)
                data["discovery"][collection][0][field] = value
                self.assert_error(expected, data)
        self.data["requirements"][0].update(version_id=None, status="idea")
        self.data["versions"][0]["requirements"] = []
        self.data["tasks"][0]["requirement_ids"] = []
        self.assertEqual([], self.errors())

    def test_discovery_ids_include_options_and_are_unique_across_all_domains(self):
        self.add_blueprint()
        self.add_governance()
        self.add_discovery()
        for duplicate in ("REQ-1", "PAGE-EDITOR", "STACK-STORAGE", "QUESTION-1", "ROUTE-LOCAL", "ANSWER-SHARED"):
            with self.subTest(duplicate=duplicate):
                data = copy.deepcopy(self.data)
                data["discovery"]["questions"][0]["options"][0]["id"] = duplicate
                self.assert_error("澄清记录 ID 重复: " + duplicate, data)
        self.data["discovery"]["questions"][0]["id"] = "bad id"
        self.assert_error("澄清记录 ID 非法")

    def test_validated_or_rejected_assumptions_require_sources_and_never_answer_questions(self):
        discovery = self.add_discovery()
        assumption = discovery["assumptions"][0]
        for status in ("validated", "rejected"):
            with self.subTest(status=status):
                assumption.update(status=status, source="")
                self.assert_error("已核查假设缺少来源")
                assumption["source"] = "本轮访谈记录"
                self.assertEqual([], self.errors())
                self.assertEqual("open", discovery["questions"][0]["status"])
                self.assertEqual("", discovery["questions"][0]["answer"])
        assumption["status"] = "answered"
        self.assert_error("假设状态非法")

    def test_invalid_discovery_states_and_boolean_types_are_rejected(self):
        self.add_discovery()
        for collection, expected in (("questions", "问题状态非法"), ("proposals", "方案状态非法")):
            data = copy.deepcopy(self.data)
            data["discovery"][collection][0]["status"] = "done"
            self.assert_error(expected, data)
            for value in (1, 0, "false", None, []):
                with self.subTest(collection=collection, blocking=value):
                    data = copy.deepcopy(self.data)
                    data["discovery"][collection][0]["blocking"] = value
                    self.assert_error("blocking 必须为布尔值", data)

    def test_malformed_discovery_returns_errors_without_crashing(self):
        self.add_discovery()
        for path, value in (
            ((), None), ((), []), (("brief",), []), (("questions",), [None]),
            (("questions", 0, "options"), [None]), (("questions", 0, "selected_option_id"), []),
            (("questions", 0, "answered_at"), None), (("proposals", 0, "options"), {}),
            (("proposals", 0, "question_ids"), [False]), (("assumptions",), [123]),
        ):
            with self.subTest(path=path):
                data = copy.deepcopy(self.data)
                if not path:
                    data["discovery"] = value
                else:
                    target = data["discovery"]
                    for key in path[:-1]:
                        target = target[key]
                    target[path[-1]] = value
                errors = self.errors(data)
                self.assertTrue(errors)
                self.assertTrue(all(isinstance(error, str) for error in errors))
                self.assertTrue(any("discovery" in error for error in errors), errors)
        del self.data["discovery"]["questions"][0]["blocking"]
        self.assert_error("blocking 缺少字段")

    def test_real_template_integrates_with_validator_and_build(self):
        template = wb.ASSETS / "workbench.html"
        self.assertTrue(template.is_file(), "The installed skill must include its HTML template")
        self.source.write_text(json.dumps(self.data), encoding="utf-8")
        pages = wb.build(self.data, self.root, self.source)
        for page in pages:
            html = page.read_text(encoding="utf-8")
            self.assertTrue(html.startswith(wb.MARKER))
            self.assertIn("测试项目", html)
            for token in ("__WORKBENCH_DATA__", "__PAGE_VERSION__", "__ROOT_PREFIX__"):
                self.assertNotIn(token, html)


if __name__ == "__main__":
    unittest.main(verbosity=2)
