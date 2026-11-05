"""Repository-level structural checks; not a simulation of agent behavior."""
import datetime
import re
import unittest
from pathlib import Path


SKILLS = Path(__file__).resolve().parents[1]


class SkillStandardTests(unittest.TestCase):
    def test_yomihime_init_identity_and_agent_execution(self):
        root = SKILLS / 'yomihime-init'
        skill = (root / 'SKILL.md').read_text(encoding='utf-8')
        interface = (root / 'agents' / 'openai.yaml').read_text(encoding='utf-8')
        self.assertIn('name: yomihime-init', skill)
        self.assertIn('不是已安装的 shell 命令', skill)
        self.assertIn('不自带联网程序', skill)
        self.assertIn('由使用该技能的 Agent', skill)
        self.assertIn('display_name: "yomihime init"', interface)
        self.assertNotIn('project-init', interface)

    def test_each_skill_has_release_version_update_time_author_and_license(self):
        entries = sorted(SKILLS.glob('*/SKILL.md'))
        self.assertEqual(len(entries), 8)
        version_pattern = r'(?:0|[1-9][0-9]{0,8})(?:\.(?:0|[1-9][0-9]{0,8})){2}'
        for entry in entries:
            with self.subTest(skill=entry.parent.name):
                text = entry.read_text(encoding='utf-8')
                front = text.split('---', 2)[1]
                self.assertIn('metadata:', front)
                # The single version authority is nested metadata.version.
                self.assertNotRegex(front, r'(?m)^version:')
                version = re.findall(r'^  version: "(' + version_pattern + r')"$', front, re.M)
                self.assertEqual(len(version), 1)
                self.assertEqual(len(re.findall(r'^  version:', front, re.M)), 1)
                updated = re.findall(r'^  updated_at: "(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ)"$', front, re.M)
                self.assertEqual(len(updated), 1)
                datetime.datetime.strptime(updated[0], '%Y-%m-%dT%H:%M:%SZ')
                self.assertIn('  author: "yomihime（如月怜） <evenia@evenia.moe>"', front)
                self.assertTrue((entry.parent / 'LICENSE').is_file())

    def test_planning_english_mirror_has_same_release_metadata(self):
        root = SKILLS / 'interactive-planning-doc'
        fronts = [(root / name).read_text(encoding='utf-8').split('---', 2)[1]
                  for name in ('SKILL.md', 'SKILL.en.md')]
        for key in ('version', 'updated_at', 'author'):
            values = [re.search(r'^  ' + key + r': "([^\n]+)"$', f, re.M).group(1)
                      for f in fronts]
            self.assertEqual(values[0], values[1], key)

    def test_skill_local_markdown_links_do_not_escape_install(self):
        for root in sorted(p.parent for p in SKILLS.glob('*/SKILL.md')):
            for path in root.rglob('*.md'):
                for target in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
                    if target.startswith(('http:', 'https:', '#', 'mailto:')):
                        continue
                    destination = (path.parent / target.split('#')[0]).resolve()
                    with self.subTest(file=str(path), target=target):
                        self.assertTrue(destination.is_relative_to(root.resolve()))
                        self.assertTrue(destination.exists())

    def test_legacy_paths_only_appear_in_init_migration_guidance(self):
        old = ('.agent-work/', '.project-memory/', '.local-dev/', '.local_dev/')
        for root in sorted(p.parent for p in SKILLS.glob('*/SKILL.md')):
            if root.name == 'yomihime-init':
                continue
            for path in root.rglob('*.md'):
                with self.subTest(file=str(path)):
                    content = path.read_text(encoding='utf-8')
                    for legacy in old:
                        self.assertNotIn(legacy, content)



    def test_multi_agent_entry_states_the_current_run_failure_barrier(self):
        # Static contract: this does not prove a runtime obeys the barrier.
        text = (SKILLS / 'multi-agent-engineering' / 'SKILL.md').read_text(encoding='utf-8')
        entry = text.split('## 触发示例与运行要求', 1)[0]
        for pattern in (
            r"当前 run.*禁止在该 run 启动新工作或放行下游",
            r"未受影响的就绪任务也不例外",
            r"needs_decision.*consulting.*blocked.*在途任务.*真实终态.*候选.*证据",
            r"接收结果不解除失败或已有决策状态",
        ):
            with self.subTest(pattern=pattern):
                self.assertRegex(entry, re.compile(pattern, re.S))

    def test_multi_agent_routes_coordination_before_dispatch_and_recovery(self):
        root = SKILLS / 'multi-agent-engineering'
        text = (root / 'SKILL.md').read_text(encoding='utf-8')
        route = next(line for line in text.splitlines()
                     if line.startswith('- [调度与工作区](references/coordination.md)'))
        self.assertTrue((root / 'references' / 'coordination.md').is_file())
        for condition in ('首次调度前', '任务失败', '在途结果接收', '返回/阻塞决策'):
            with self.subTest(condition=condition):
                self.assertIn(condition, route)


    def test_task_handoff_keeps_assignment_and_ready_separate_from_authorization(self):
        root = SKILLS / 'multi-agent-engineering'
        text = (root / 'references' / 'task-cards.md').read_text(encoding='utf-8')
        for pattern in (
            r"主调度者.*任务 owner、结果接收者与验收职责.*identity/goal/outputs.*不新增强制字段",
            r"角色名不能代替任务定义.*主计划、任务包和知识摘录都不增加权限",
            r"相关章节、全部适用约束.*候选/dirty 基准.*允许动作.*run/attempt.*失败、顾问或阻塞状态",
            r"ready 只表示本任务输入与权限就绪.*当前 run 无未解决失败、轮次已开放且依赖已接收",
        ):
            with self.subTest(pattern=pattern):
                self.assertRegex(text, re.compile(pattern, re.S))

    def test_revised_task_inputs_keep_old_identity_and_current_run_failure(self):
        root = SKILLS / 'multi-agent-engineering' / 'references'
        cards = (root / 'task-cards.md').read_text(encoding='utf-8')
        self.assertRegex(cards, re.compile(r"旧输入的结果保留原版本、候选与证据.*适用性.*复用或重验", re.S))
        self.assertIn("新 input-version 不解除当前 run 的失败、顾问或阻塞状态，也不扩大允许动作", cards)
        self.assertRegex(cards, re.compile(r"旧 owner 的停写/交回和在途操作.*新 owner 的准确范围.*通知不等于转移完成", re.S))
        coordination = (root / 'coordination.md').read_text(encoding='utf-8')
        self.assertIn("更新计划/input-version 不解除当前 run 的失败或既有决策状态", coordination)

    def test_knowledge_and_pipeline_handoff_keep_result_acceptance_and_write_scope(self):
        memory = (SKILLS / 'project-memory' / 'references' / 'collaboration.md').read_text(encoding='utf-8')
        self.assertIn("知识摘录只提供有来源的上下文，不授予源码或外部动作权限", memory)
        self.assertIn("记忆 writer 只在获配记忆范围内归并已接收事实", memory)
        for field in ('source:', 'scope:', 'constraints:', 'facts:', 'freshness:', 'gaps:'):
            self.assertIn(field, memory)
        pipeline = (SKILLS / 'development-pipeline' / 'SKILL.md').read_text(encoding='utf-8')
        self.assertRegex(pipeline, re.compile(r"主调度者负责分派和结果接收.*JOB 的 owner、产物接收者与验收职责", re.S))
        self.assertIn("执行者只在获配任务和写入/动作范围内交付", pipeline)
        self.assertIn("记忆维护职责只归并已接收事实", pipeline)

if __name__ == '__main__':
    unittest.main()
