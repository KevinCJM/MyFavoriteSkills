from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('prompt_contract_tested', ROOT / 'scripts/prompt_contract.py')
pc = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = pc
SPEC.loader.exec_module(pc)
EXAMPLES = ROOT / 'examples/prompts'
BUILDER = (EXAMPLES / 'builder.md').read_text()
REWORK = (EXAMPLES / 'rework.md').read_text()


class PromptContractTests(unittest.TestCase):
    def errors(self, text, **kw):
        return '\n'.join(pc.validate(text, **kw)['errors'])

    def test_all_resolved_examples(self):
        for path in EXAMPLES.glob('*.md'):
            if path.name == 'README.md':
                continue
            with self.subTest(path=path.name):
                parent = BUILDER if path.name in {'rework.md', 'clarification.md'} else None
                self.assertEqual([], pc.validate(path.read_text(), parent_text=parent)['errors'])

    def test_templates_are_not_ready_to_dispatch(self):
        for path in (ROOT / 'templates/prompts').glob('*brief.md'):
            with self.subTest(path=path.name):
                self.assertIn('unresolved template', self.errors(path.read_text()))

    def test_missing_identity(self):
        for key in pc.IDENTITY:
            import re
            value = re.sub(r'^' + key + r':.*\n', '', BUILDER, flags=re.MULTILINE)
            with self.subTest(key=key):
                self.assertIn('missing metadata: ' + key, self.errors(value))

    def test_duplicate_metadata(self):
        self.assertIn('duplicate metadata', self.errors('Task: shadow\n' + BUILDER))

    def test_protocol_version(self):
        self.assertIn('unsupported Protocol', self.errors(BUILDER.replace('ocw/1','ocw/9')))

    def test_invalid_kind(self):
        self.assertIn('Kind must', self.errors(BUILDER.replace('Kind: dispatch','Kind: cancel')))

    def test_invalid_role(self):
        self.assertIn('Role must', self.errors(BUILDER.replace('Role: builder','Role: manager')))

    def test_invalid_task(self):
        self.assertIn('portable identifier', self.errors(BUILDER.replace('Task: WP-07','Task: ../foo')))

    def test_invalid_revisions(self):
        for val in ['0','-1','latest','1.5']:
            with self.subTest(value=val):
                self.assertIn('positive integer', self.errors(BUILDER.replace('Revision: 1','Revision: '+val)))

    def test_relative_directory(self):
        self.assertIn('absolute server path', self.errors(BUILDER.replace('/srv/example-project/wt-config','relative/wt')))

    def test_parent_traversal(self):
        self.assertIsNone(pc.remote_path_identity('/srv/work/../elsewhere'))
        self.assertIsNone(pc.remote_path_identity('C:\\work\\..\\elsewhere'))

    def test_windows_server_directory(self):
        text = BUILDER.replace('/srv/example-project/wt-config','C:\\repo\\worker')
        self.assertEqual([],pc.validate(text)['errors'])

    def test_expected_directory_match(self):
        self.assertEqual([],pc.validate(BUILDER, expected_directory='/srv/example-project/wt-config/')['errors'])
        self.assertIn('expected directory', self.errors(BUILDER,expected_directory='/different'))

    def test_snapshot_alias_rejected(self):
        for alias in ['HEAD','latest','same as before']:
            text = BUILDER.replace('git:'+'a'*40+'; clean',alias)
            with self.subTest(alias=alias):
                self.assertIn('Snapshot must be concrete',self.errors(text))

    def test_dirty_identity_accepted(self):
        value = BUILDER.replace('; clean','; dirty:sha256:'+'e'*64)
        self.assertEqual([],pc.validate(value)['errors'])

    def test_compact_high_risk_rejected(self):
        text=(EXAMPLES/'compact.md').read_text().replace('Risk: low','Risk: high')
        self.assertIn('compact mode', self.errors(text))

    def test_unknown_mode_and_risk(self):
        self.assertIn('Mode must',self.errors(BUILDER.replace('Mode: full','Mode: unlimited')))
        self.assertIn('Risk must',self.errors(BUILDER.replace('Risk: medium','Risk: none')))

    def test_missing_full_sections(self):
        for label in ['Inputs','Decisions','Stop']:
            with self.subTest(label=label):
                self.assertIn('missing/empty section: '+label,self.errors(BUILDER.replace('## '+label,'## Removed'+label)))

    def test_nonbuilder_cannot_have_write_scope(self):
        for role in ['scout','designer','verifier']:
            with self.subTest(role=role):
                self.assertIn('require Write: none',self.errors(BUILDER.replace('Role: builder','Role: '+role)))

    def test_duplicate_scope(self):
        self.assertIn('exactly one Write:',self.errors(BUILDER.replace('## Scope','## Scope\nWrite: none')))

    def test_duplicate_section(self):
        self.assertIn('duplicate section',self.errors(BUILDER+'\n## Goal\nconflicting goal\n'))

    def test_missing_evidence_mapping(self):
        text=BUILDER.replace('## Checks','- AC-4: additional observable requirement\n\n## Checks')
        self.assertIn('no planned evidence: AC-4',self.errors(text))

    def test_unknown_criterion_reference(self):
        self.assertIn('unknown criterion AC-99',self.errors(BUILDER.replace('V-2 -> AC-3','V-2 -> AC-99')))

    def test_duplicate_criteria(self):
        text=BUILDER.replace('## Checks','- AC-1: duplicate\n\n## Checks')
        self.assertIn('duplicate acceptance ID',self.errors(text))

    def test_duplicate_checks(self):
        self.assertIn('duplicate verification ID',self.errors(BUILDER.replace('V-2 ->','V-1 ->')))

    def test_fenced_fake_checks_do_not_count(self):
        compact=(EXAMPLES/'compact.md').read_text()
        start=compact.index('- V-1')
        end=compact.index('\n## Return')
        text=compact[:start]+'```text\n'+compact[start:end]+'\n```\n'+compact[end:]
        self.assertIn('Checks requires',self.errors(text))

    def test_unclosed_fence(self):
        self.assertIn('unclosed fenced block',self.errors(BUILDER+'\n```text\n'))

    def test_cpp_generics_are_not_template_placeholders(self):
        text=BUILDER.replace('## Goal','## Goal\nUse vector<T> as an example notation, not a placeholder.')
        self.assertEqual([],pc.validate(text)['errors'])

    def test_known_placeholder_rejected(self):
        self.assertIn('unresolved template',self.errors(BUILDER.replace('WP-07','<task-id>')))

    def test_large_prompt_warns_not_truncates(self):
        text=BUILDER+'\n'+'大'*6000
        result=pc.validate(text)
        self.assertEqual([],result['errors'])
        self.assertTrue(any('large brief' in w for w in result['warnings']))
        self.assertEqual(len(text),result['chars'])

    def test_rework_parent_mismatch(self):
        for a,b in [('Task: WP-07','Task: WP-99'),('Revision: 1','Revision: 2'),('Role: builder','Role: scout')]:
            with self.subTest(field=a):
                self.assertIn('differs from parent',self.errors(REWORK.replace(a,b),parent_text=BUILDER))

    def test_rework_new_attempt_required(self):
        self.assertIn('Attempt must be newer',self.errors(REWORK.replace('Attempt: 2','Attempt: 1'),parent_text=BUILDER))

    def test_rework_unknown_failure(self):
        self.assertIn('failure refers to unknown',self.errors(REWORK.replace('F-1 -> AC-2','F-1 -> AC-80'),parent_text=BUILDER))

    def test_rework_failure_needs_recheck(self):
        self.assertIn('failed criterion has no recheck',self.errors(REWORK.replace('V-1 -> AC-1, AC-2','V-1 -> AC-1'),parent_text=BUILDER))

    def test_rework_parent_warning(self):
        self.assertTrue(any('parent brief not supplied' in w for w in pc.validate(REWORK)['warnings']))

    def test_invalid_parent(self):
        self.assertIn('parent must be',self.errors(REWORK,parent_text=BUILDER.replace('Protocol: ocw/1','Protocol: bad')))

    def test_question_identifier_required(self):
        text=(EXAMPLES/'clarification.md').read_text().replace('Q-1:','Question:')
        self.assertIn('Q-n:',self.errors(text,parent_text=BUILDER))

    def test_fresh_render_includes_rules_once_and_exact_brief(self):
        result=pc.compose(BUILDER)
        self.assertEqual(1,result.count('# Worker rules — ocw/1'))
        self.assertTrue(result.endswith(BUILDER))
        self.assertIn('True, 1.0, "1", 0 and -1',result)

    def test_delta_render_avoids_duplicate_rules(self):
        self.assertEqual(REWORK,pc.compose(REWORK))

    def test_render_exclusive_private_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'prompt.md'
            pc.write_exclusive(target,BUILDER)
            self.assertEqual(BUILDER,target.read_text())
            if os.name=='posix': self.assertEqual(0o600,target.stat().st_mode & 0o777)
            with self.assertRaises(FileExistsError): pc.write_exclusive(target,'overwrite')
            self.assertEqual(BUILDER,target.read_text())

    def test_render_symlink_not_followed(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'target'
            target.write_text('preserve')
            link=Path(tmp)/'link'
            link.symlink_to(target)
            with self.assertRaises(FileExistsError): pc.write_exclusive(link,'overwrite')
            self.assertEqual('preserve',target.read_text())

    def test_cli_render_does_not_execute_prompt_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            brief=Path(tmp)/'brief.md'; output=Path(tmp)/'out.md'; marker=Path(tmp)/'never-created'
            brief.write_text(BUILDER.replace('run python -m pytest',f'touch {marker}; python -m pytest'))
            run=subprocess.run([sys.executable,str(ROOT/'scripts/prompt_contract.py'),'render',str(brief),'--output',str(output)],text=True,capture_output=True)
            self.assertEqual(0,run.returncode,run.stdout+run.stderr)
            self.assertFalse(marker.exists())
            receipt=json.loads(run.stdout)
            self.assertIn('sha256',receipt['rendered'])
            self.assertNotIn('Reject invalid timeout_ms',run.stdout)

    def test_cli_bad_input_and_invalid_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            script=str(ROOT/'scripts/prompt_contract.py')
            absent=subprocess.run([sys.executable,script,'lint',str(Path(tmp)/'absent')],text=True,capture_output=True)
            self.assertEqual(1,absent.returncode)
            bad=Path(tmp)/'bad.md';bad.write_text('No contract')
            dest=Path(tmp)/'out.md'
            run=subprocess.run([sys.executable,script,'render',str(bad),'--output',str(dest)],text=True,capture_output=True)
            self.assertEqual(2,run.returncode)
            self.assertFalse(dest.exists())

    def test_utf8_and_size_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'brief.md';p.write_text('中文',encoding='utf-8')
            self.assertEqual('中文',pc.read_text(p))
            p.write_bytes(b'x'*(pc.MAX_BYTES+1))
            with self.assertRaises(ValueError):pc.read_text(p)

    def test_structure_is_not_semantic_approval(self):
        result=pc.validate(BUILDER)
        self.assertEqual('structure_pass',result['status'])
        self.assertIn('evidence_truth',result['not_verified'])
        self.assertIn('remote_paths',result['not_verified'])


if __name__=='__main__': unittest.main()
