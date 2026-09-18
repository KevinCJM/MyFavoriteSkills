"""Keep installed vendor dependencies outside the Skill-owned structure checks."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location(
    'check_bundle', Path(__file__).resolve().parents[1] / 'scripts/check_bundle.py')
bundle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bundle)


class BundleScopeTests(unittest.TestCase):
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
