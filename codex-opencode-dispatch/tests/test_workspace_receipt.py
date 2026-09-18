from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "workspace_receipt.py"
spec = importlib.util.spec_from_file_location("receipt", SCRIPT)
assert spec is not None and spec.loader is not None
receipt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(receipt)


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.area = Path(self.tmp.name)
        self.root = self.area / "repo"
        self.root.mkdir()
        self.g("init", "-q")
        self.g("config", "user.email", "skill-test@example.invalid")
        self.g("config", "user.name", "Skill Tests")
        self.g("config", "core.filemode", "true")
        self.write("src/main.py", "value = 1\n")
        self.write("tests/test_main.py", "assert True\n")
        self.write(".gitignore", "cache/\n")
        self.g("add", ".")
        self.g("commit", "-qm", "baseline")
        self.base = self.g("rev-parse", "HEAD").strip()

    def g(self, *args):
        result = subprocess.run(["git", "-C", str(self.root), *args], capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(result.stderr)
        return result.stdout

    def write(self, name, text):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        return p

    def snap(self):
        return receipt.snapshot(self.root, self.base)

    def entry(self, data, name):
        return next(f for f in data["files"] if f["path"] == name)

    def test_clean_baseline(self):
        data = self.snap()
        self.assertEqual(data["changed_paths"], [])
        self.assertEqual(receipt.scope(data, ["src/"], [])["acceptance"], "not_evaluated")

    def test_unstaged_change(self):
        self.write("src/main.py", "value = 2\n")
        self.assertEqual(self.snap()["changed_paths"], ["src/main.py"])

    def test_staged_change(self):
        self.write("src/main.py", "value = 2\n")
        self.g("add", "src/main.py")
        self.assertIn("src/main.py", self.snap()["changed_paths"])

    def test_staged_change_restored_in_worktree(self):
        self.write("src/main.py", "value = 2\n")
        self.g("add", "src/main.py")
        self.write("src/main.py", "value = 1\n")
        data = self.snap()
        self.assertIn("src/main.py", data["changed_paths"])
        self.assertEqual(receipt.scope(data, ["tests/"], [])["status"], "scope_violation")

    def test_committed_change_with_clean_status(self):
        self.write("src/main.py", "value = 2\n")
        self.g("add", "src/main.py")
        self.g("commit", "-qm", "worker change")
        self.assertEqual(self.g("status", "--porcelain"), "")
        self.assertIn("src/main.py", self.snap()["changed_paths"])

    def test_untracked_file(self):
        self.write("tests/new_test.py", "assert 1 == 1\n")
        data = self.snap()
        self.assertTrue(self.entry(data, "tests/new_test.py")["untracked"])

    def test_rename_includes_old_and_new(self):
        self.g("mv", "src/main.py", "src/new_name.py")
        data = self.snap()
        self.assertEqual(data["changed_paths"], ["src/main.py", "src/new_name.py"])
        self.assertEqual(self.entry(data, "src/main.py")["working"]["kind"], "missing")

    def test_unicode_space_and_newline_paths(self):
        path = "src/新增 file\nname.py"
        self.write(path, "test = 1\n")
        self.assertIn(path, self.snap()["changed_paths"])

    def test_leading_dash_filename(self):
        self.write("-odd.py", "value = 2")
        self.assertIn("-odd.py", self.snap()["changed_paths"])

    def test_binary_content_is_hashed_not_exposed(self):
        data = bytes(range(256))
        (self.root / "src" / "blob.bin").write_bytes(data)
        item = self.entry(self.snap(), "src/blob.bin")["working"]
        self.assertEqual(item["bytes"], 256)
        self.assertEqual(len(item["sha256"]), 64)
        self.assertNotIn("content", item)

    def test_symlink_does_not_read_target(self):
        outside = self.area / "outside-secret"
        outside.write_text("not repository data")
        os.symlink(outside, self.root / "src" / "link")
        item = self.entry(self.snap(), "src/link")["working"]
        self.assertEqual(item["kind"], "symlink")
        self.assertNotIn("not repository data", json.dumps(item))

    def test_parent_symlink_escape_is_flagged(self):
        outside = self.area / "outside"
        outside.mkdir()
        (outside / "main.py").write_text("private")
        (self.root / "src" / "main.py").unlink()
        (self.root / "src").rmdir()
        os.symlink(outside, self.root / "src")
        data = self.snap()
        self.assertIn("path_parent_escapes_workspace", data["manual_review_flags"])
        self.assertEqual(self.entry(data, "src/main.py")["working"]["kind"], "outside_parent_not_read")

    def test_ignored_files_excluded_and_limitation_explicit(self):
        self.write("cache/generated.txt", "noise")
        data = self.snap()
        self.assertEqual(data["changed_paths"], [])
        self.assertIn("ignored_files_and_external_state_not_covered", data["limitations"])

    def test_assume_unchanged_requires_manual_review_even_when_diff_hides_change(self):
        self.g("update-index", "--assume-unchanged", "src/main.py")
        self.write("src/main.py", "value = 9\n")
        data = self.snap()
        self.assertIn("assume_unchanged:src/main.py", data["manual_review_flags"])
        self.assertEqual(receipt.scope(data, ["src/"], [])["status"], "manual_review_required")

    def test_skip_worktree_requires_manual_review_even_when_diff_hides_change(self):
        self.g("update-index", "--skip-worktree", "src/main.py")
        self.write("src/main.py", "value = 9\n")
        data = self.snap()
        self.assertIn("skip_worktree:src/main.py", data["manual_review_flags"])
        self.assertEqual(receipt.scope(data, ["src/"], [])["status"], "manual_review_required")

    def test_executable_mode(self):
        p = self.root / "src" / "main.py"
        p.chmod(0o755)
        self.assertTrue(self.entry(self.snap(), "src/main.py")["working"]["executable"])

    def test_deny_precedes_allow(self):
        self.write("src/main.py", "value = 2")
        out = receipt.scope(self.snap(), ["src/"], ["src/main.py"])
        self.assertEqual(out["status"], "scope_violation")

    def test_directory_starstar_supported(self):
        self.write("src/deep/new.py", "x = 2")
        self.assertEqual(receipt.scope(self.snap(), ["src/**"], [])["status"], "scope_only_pass")

    def test_unsupported_glob_rejected(self):
        with self.assertRaises(receipt.ReceiptError):
            receipt.scope(self.snap(), ["*.py"], [])

    def test_path_traversal_rule_rejected(self):
        with self.assertRaises(receipt.ReceiptError):
            receipt.scope(self.snap(), ["src/../tests/"], [])

    def test_absolute_rule_rejected(self):
        with self.assertRaises(receipt.ReceiptError):
            receipt.scope(self.snap(), ["/src/"], [])

    def test_empty_allow_rejected(self):
        with self.assertRaises(receipt.ReceiptError):
            receipt.scope(self.snap(), [], [])

    def test_fingerprint_changes_on_same_path_repair(self):
        self.write("src/main.py", "value = 2\n")
        before = self.snap()
        self.write("src/main.py", "value = 3\n")
        after = self.snap()
        out = receipt.delta(before, after)
        self.assertFalse(out["same_snapshot"])
        self.assertEqual(out["changed_since_review"], ["src/main.py"])

    def test_fingerprint_stable_without_change(self):
        self.write("src/main.py", "value = 2\n")
        self.assertTrue(receipt.delta(self.snap(), self.snap())["same_snapshot"])

    def test_reverted_change_in_delta(self):
        self.write("src/main.py", "value = 2\n")
        before = self.snap()
        self.write("src/main.py", "value = 1\n")
        self.assertEqual(receipt.delta(before, self.snap())["changed_since_review"], ["src/main.py"])

    def test_different_base_blocks_delta(self):
        before = self.snap()
        self.write("src/main.py", "value = 2\n")
        self.g("add", "src/main.py")
        self.g("commit", "-qm", "change")
        after = receipt.snapshot(self.root, "HEAD")
        with self.assertRaises(receipt.ReceiptError):
            receipt.delta(before, after)

    def test_scope_delta_ignores_preexisting_out_of_scope_user_change(self):
        self.write("src/main.py", "value = 2\n")  # pre-existing user work
        before = self.snap()
        self.write("tests/test_main.py", "assert 1 == 1\n")  # worker-period change
        after = self.snap()
        out = receipt.scope_delta(before, after, ["tests/"], [])
        self.assertEqual(out["status"], "scope_only_pass")
        self.assertEqual(out["changed_since_before"], ["tests/test_main.py"])
        self.assertEqual(out["unexpected_paths"], [])

    def test_scope_delta_catches_worker_period_change_to_preexisting_out_of_scope_file(self):
        self.write("src/main.py", "value = 2\n")
        before = self.snap()
        self.write("src/main.py", "value = 3\n")
        after = self.snap()
        out = receipt.scope_delta(before, after, ["tests/"], [])
        self.assertEqual(out["status"], "scope_violation")
        self.assertEqual(out["unexpected_paths"], ["src/main.py"])

    def test_gitlink_requires_manual_review(self):
        self.g("update-index", "--add", "--cacheinfo", f"160000,{self.base},vendor/module")
        data = self.snap()
        self.assertIn("submodules_not_recursively_inspected", data["manual_review_flags"])
        self.assertEqual(receipt.scope(data, ["vendor/"], [])["status"], "manual_review_required")

    def test_receipt_write_outside_repo_and_no_overwrite(self):
        dest = self.area / "receipt.json"
        data = self.snap()
        receipt.write_new(dest, data)
        self.assertEqual(receipt.load_receipt(dest)["fingerprint"], data["fingerprint"])
        with self.assertRaises(FileExistsError):
            receipt.write_new(dest, data)

    def test_receipt_write_inside_repo_refused(self):
        with self.assertRaises(receipt.ReceiptError):
            receipt.write_new(self.root / "receipt.json", self.snap())

    def test_tampered_receipt_fingerprint_rejected(self):
        data = self.snap()
        data["head"] = "0" * 40
        dest = self.area / "bad.json"
        dest.write_text(json.dumps(data))
        with self.assertRaises(receipt.ReceiptError):
            receipt.load_receipt(dest)

    def test_option_like_revision_rejected(self):
        with self.assertRaises(receipt.ReceiptError):
            receipt.snapshot(self.root, "--help")

    def test_missing_revision_fails_closed(self):
        with self.assertRaises(receipt.ReceiptError):
            receipt.snapshot(self.root, "not-a-real-revision")

    def test_non_repository_fails_closed(self):
        with self.assertRaises(receipt.ReceiptError):
            receipt.snapshot(self.area, "HEAD")

    def test_read_operations_do_not_change_git_state(self):
        self.write("src/main.py", "value = 2\n")
        before = self.g("status", "--porcelain")
        self.snap()
        self.assertEqual(self.g("status", "--porcelain"), before)


    def test_scope_directory_does_not_allow_sibling(self):
        self.write("src-other/file.py", "value = 2")
        self.assertEqual(receipt.scope(self.snap(), ["src/"], [])["status"], "scope_violation")

    def test_tampered_path_inventory_rejected(self):
        self.write("src/main.py", "value = 2")
        data = self.snap()
        data["changed_paths"] = []
        dest = self.area / "bad-paths.json"
        dest.write_text(json.dumps(data))
        with self.assertRaises(receipt.ReceiptError):
            receipt.load_receipt(dest)

    def test_unmerged_index_requires_manual_review(self):
        self.g("checkout", "-qb", "side")
        self.write("src/main.py", "value = 2\n")
        self.g("add", "src/main.py")
        self.g("commit", "-qm", "side")
        self.g("checkout", "-qb", "primary", self.base)
        self.write("src/main.py", "value = 3\n")
        self.g("add", "src/main.py")
        self.g("commit", "-qm", "primary")
        merge = subprocess.run(["git", "-C", str(self.root), "merge", "side"], capture_output=True)
        self.assertNotEqual(merge.returncode, 0)
        data = self.snap()
        self.assertIn("unmerged_index", data["manual_review_flags"])
        self.assertEqual(receipt.scope(data, ["src/"], [])["status"], "manual_review_required")

    def test_cli_snapshot_and_scope_exit_codes(self):
        import sys
        self.write("src/main.py", "value = 2")
        output = self.area / "cli-receipt.json"
        capture = subprocess.run([sys.executable, str(SCRIPT), "snapshot", "--repo", str(self.root),
                                  "--base", self.base, "--output", str(output)], capture_output=True, text=True)
        self.assertEqual(capture.returncode, 0, capture.stderr)
        self.assertEqual(json.loads(capture.stdout)["acceptance"], "not_evaluated")
        scoped = subprocess.run([sys.executable, str(SCRIPT), "scope", "--receipt", str(output),
                                 "--allow", "tests/"], capture_output=True, text=True)
        self.assertEqual(scoped.returncode, 2, scoped.stderr)
        self.assertEqual(json.loads(scoped.stdout)["status"], "scope_violation")

    def test_cli_scope_delta_distinguishes_preexisting_changes(self):
        import sys
        self.write("src/main.py", "value = 2\n")
        before_path = self.area / "before.json"
        after_path = self.area / "after.json"
        receipt.write_new(before_path, self.snap())
        self.write("tests/test_main.py", "assert 1 == 1\n")
        receipt.write_new(after_path, self.snap())
        scoped = subprocess.run([sys.executable, str(SCRIPT), "scope-delta",
                                 "--before", str(before_path), "--after", str(after_path),
                                 "--allow", "tests/"], capture_output=True, text=True)
        self.assertEqual(scoped.returncode, 0, scoped.stderr)
        body = json.loads(scoped.stdout)
        self.assertEqual(body["status"], "scope_only_pass")
        self.assertEqual(body["changed_since_before"], ["tests/test_main.py"])


if __name__ == "__main__":
    unittest.main()
