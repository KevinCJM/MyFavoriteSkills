"""Keep installed vendor dependencies outside the Skill-owned structure checks."""
import importlib.util
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    'check_bundle', Path(__file__).resolve().parents[1] / 'scripts/check_bundle.py')
bundle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bundle)


class BundleScopeTests(unittest.TestCase):
    def test_explicit_only_bundle_passes(self):
        output = io.StringIO()
        with redirect_stdout(output):
            result = bundle.main()
        self.assertEqual(result, 0, output.getvalue())

    def test_enabling_implicit_invocation_fails_bundle_check(self):
        original_read = Path.read_text
        metadata = Path(bundle.__file__).resolve().parents[1] / 'agents/openai.yaml'

        def read_with_implicit_invocation(path, *args, **kwargs):
            text = original_read(path, *args, **kwargs)
            if path == metadata:
                return text.replace('allow_implicit_invocation: false',
                                    'allow_implicit_invocation: true')
            return text

        output = io.StringIO()
        with patch.object(Path, 'read_text', read_with_implicit_invocation), redirect_stdout(output):
            result = bundle.main()
        self.assertEqual(result, 1)
        self.assertIn('agents/openai.yaml: explicit-only invocation metadata required',
                      json.loads(output.getvalue())['errors'])

    def test_vendor_is_pruned_but_skill_and_provenance_are_checked(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            paths = ['README.md', 'references/mcp-v3.md', 'mcp/UPSTREAM.json',
                     'mcp/opencode-mcp/README.md',
                     'mcp/opencode-mcp/node_modules/dependency/package.json',
                     '.git/config', '__pycache__/generated.py',
                     'node_modules/dependency/package.json']
            for name in paths:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()
            self.assertEqual({path.relative_to(root).as_posix()
                              for path in bundle.skill_files(root)}, set(paths[:3]))
