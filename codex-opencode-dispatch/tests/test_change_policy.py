"""Regression checks for policy propagation/format only, not semantic or LLM enforcement."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('policy_prompt_contract', ROOT / 'scripts/prompt_contract.py')
pc = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = pc
SPEC.loader.exec_module(pc)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


class ChangePolicyWiringTests(unittest.TestCase):
    def test_core_gate_precedes_work_routing(self):
        text = read('SKILL.md')
        self.assertLess(text.index('## 0. Admit changes'), text.index('## 2. Choose'))
        for q in ('Q1', 'Q2', 'Q3', 'Q4'):
            self.assertIn(q, text)
        self.assertIn('references/change-admission.md', text)
        self.assertIn('Codex direct work', text)

    def test_worker_rules_are_self_contained(self):
        text = read('templates/worker-rules.md')
        for term in ('Q1', 'Q2', 'Q3', 'Q4', 'historical technical debt',
                     'unsolicited suspected bugs', 'Codex cannot waive', 'contracts preserved'):
            self.assertIn(term, text)

    def test_fresh_dispatch_renders_gate_once_before_brief(self):
        brief = read('examples/prompts/builder.md')
        rendered = pc.compose(brief)
        rules = read('templates/worker-rules.md').rstrip()
        self.assertTrue(rendered.startswith(rules + '\n\n---\n'))
        self.assertEqual(1, rendered.count('# Worker rules — ocw/1'))
        self.assertIn('Q1', rendered.split('# Task contract', 1)[0])

    def test_rework_render_is_delta_without_duplicate_rules(self):
        brief = read('examples/prompts/rework.md')
        rendered = pc.compose(brief)
        self.assertEqual(brief.rstrip() + '\n', rendered)
        self.assertNotIn('# Worker rules', rendered)
        self.assertIn('Admission delta C-1/C-2', rendered)

    def test_full_builder_and_designer_require_change_answers(self):
        for name in ('builder-brief', 'designer-brief'):
            text = read(f'templates/prompts/{name}.md')
            with self.subTest(template=name):
                for term in ('Q1', 'Q2', 'Q3', 'Q4', 'C-ID'):
                    self.assertIn(term, text)
                self.assertIn('contract', text)

    def test_compact_example_passes_existing_format_without_cid_table(self):
        text = read('examples/prompts/compact.md')
        self.assertIn('Boundary:', text)
        self.assertNotIn('C-1: Q1', text)
        self.assertEqual([], pc.validate(text)['errors'])
        self.assertEqual('structure_pass', pc.validate(text)['status'])

    def test_rework_preserves_parent_contract_and_has_gate_delta(self):
        parent = read('examples/prompts/builder.md')
        delta = read('examples/prompts/rework.md')
        self.assertEqual([], pc.validate(delta, parent_text=parent)['errors'])
        for q in ('Q1', 'Q2', 'Q3', 'Q4'):
            self.assertIn(q, delta)
        self.assertEqual('1', pc.parse(delta).metadata['Revision'])

    def test_verifier_cannot_create_style_or_debt_rework(self):
        text = read('templates/prompts/verifier-brief.md')
        self.assertIn('Q1–Q4', text)
        self.assertIn('Do not mandate style-only refactoring', text)
        self.assertIn('historical debt cleanup', text)
        self.assertIn('finding cannot authorize', text)

    def test_contract_revision_requires_user_authority(self):
        text = read('references/change-admission.md')
        self.assertIn('Only the user can explicitly revise', text)
        self.assertIn('Codex does not have authority to waive', text)
        self.assertIn('explicit user authorization', read('templates/prompts/clarification.md'))

    def test_relevant_contract_inventory_is_explicit(self):
        text = read('references/change-admission.md')
        for term in ('API / CLI', 'Configuration', 'Logs / observability', 'Data',
                     'Dependencies', 'User workflow / compatibility'):
            self.assertIn(term, text)

    def test_new_vs_baseline_defects_are_distinguished(self):
        text = read('references/change-admission.md')
        for term in ('Defect/extra work introduced by this task', 'Existing unrelated issue or debt',
                     'Suspected unrelated bug', 'Serious unrelated security/data-loss hazard'):
            self.assertIn(term, text)

    def test_integration_and_report_reference_admitted_changes(self):
        self.assertIn('four-question gate', read('references/workspaces.md'))
        self.assertIn('Q1–Q4', read('references/verification.md'))
        self.assertIn('admitted C-IDs/ACs', read('templates/worker-report.md'))
        self.assertIn('user-authorized requirement', read('references/workspaces.md'))

    def test_resident_rules_are_optional_manual_merge(self):
        text = read('templates/project-rules-snippet.md')
        self.assertIn('手动合并', text)
        self.assertIn('不覆盖或自动修改', text)
        for term in ('API', '配置', '日志', '数据结构', '下游依赖', '用户工作流', '兼容'):
            self.assertIn(term, text)

    def test_structural_pass_does_not_claim_semantic_gate(self):
        # Deliberately valid ocw/1 with no admission answers: backwards-compatible syntax.
        text = read('examples/prompts/compact.md')
        start, end = text.index('Boundary:'), text.index('## Acceptance')
        without_gate = text[:start] + '\n' + text[end:]
        result = pc.validate(without_gate)
        self.assertEqual('structure_pass', result['status'])
        self.assertIn('semantics', result['not_verified'])
        self.assertIn('authorization', result['not_verified'])
        self.assertNotIn('admission_pass', json.dumps(result))
        self.assertIn('不强制检查四问是否填写', read('README.md'))

    def test_behavior_cases_are_not_claimed_executed(self):
        doc = json.loads(read('evals/scenarios.json'))
        cases = [c for c in doc['cases'] if c['id'].startswith('C')]
        self.assertEqual(24, len(cases))
        self.assertEqual('not_run_against_live_codex', doc['execution_status'])
        self.assertTrue(all(c['reference'] == 'references/change-admission.md' for c in cases))


    def test_compact_policy_avoids_management_overhead(self):
        core = read('SKILL.md')
        compact = read('templates/prompts/compact-brief.md')
        state = read('references/state-and-context.md')
        self.assertIn('one `Boundary:` sentence', core)
        self.assertIn('No C-ID table or ledger is required', compact)
        self.assertIn('Simple one-shot work', state)

    def test_mcp_variant_is_supported_but_not_hardcoded_to_max(self):
        mcp = read('references/mcp-v3.md')
        ledger = json.loads(read('templates/ledger.json'))
        profile = read('templates/project-profile.md')
        self.assertIn('variant?', mcp)
        self.assertIn('Do **not** assume `max`', mcp)
        self.assertIn('variant', ledger['model_binding'])
        self.assertIsNone(ledger['model_binding']['variant'])
        self.assertIn('do not invent `max`', profile)

    def test_authorization_persists_and_sessions_are_reused_safely(self):
        core = read('SKILL.md')
        state = read('references/state-and-context.md')
        metadata = read('agents/openai.yaml')
        cases = {case['id']: case for case in json.loads(read('evals/scenarios.json'))['cases']}
        self.assertIn('same Codex conversation and project/workspace', ' '.join(core.split()))
        self.assertIn('the human need not repeat the Skill name', core)
        self.assertIn('controller-owned session map', state)
        self.assertIn('pass its `sessionId` explicitly', state)
        self.assertIn('Parallel Workers and independent Reviewer roles use separate sessions', state)
        self.assertIn('allow_implicit_invocation: false', metadata)
        self.assertEqual('new_turn_same_session', cases['A06']['expected_route'])
        self.assertEqual('fresh_session', cases['A07']['expected_route'])
        self.assertEqual('direct', cases['A08']['expected_route'])

    def test_version_and_protocol_remain_compatible(self):
        self.assertEqual('2.5.2', read('VERSION').strip())
        self.assertIn('name: codex-opencode-dispatch', read('SKILL.md'))
        for name in ('builder', 'designer', 'compact', 'rework', 'verifier', 'scout', 'clarification'):
            self.assertEqual('ocw/1', pc.parse(read(f'examples/prompts/{name}.md')).metadata['Protocol'])


if __name__ == '__main__':
    unittest.main()
