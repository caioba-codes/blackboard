"""Public CLI contract for explicit lesson routing and publication receipts."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "bin/lesson_routing.py"


def config(author="author-v1", reviewer="reviewer-v1", support="support-v1"):
    return {"version": 1, "roles": {
        "author": {"model": author, "effort": "high"},
        "reviewer": {"model": reviewer, "effort": "medium"},
        "support": {"model": support, "effort": "low"}}}


class LessonRoutingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.user = self.root / "config/blackboard/lesson-routing.json"
        self.user.parent.mkdir(parents=True)
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        self.local = self.workspace / ".blackboard/lesson-routing.json"
        self.override = self.root / "override.json"

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))

    def call(self, command="resolve", *extra):
        return subprocess.run([sys.executable, str(SCRIPT), command,
                               "--workspace", str(self.workspace), *extra],
                              env={**os.environ, "XDG_CONFIG_HOME": str(self.root / "config")},
                              text=True, capture_output=True)

    def test_precedence_and_no_policy_default(self):
        self.assertEqual(json.loads(self.call().stdout), {"mode": "automatic", "roles": {}})
        for flag, path in (("--user-config", self.user),
                           ("--workspace-config", self.local)):
            with self.subTest(flag=flag):
                result = self.call("resolve", flag, str(path))
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(str(path), result.stderr)
        self.write(self.user, config())
        self.write(self.local, config(author="workspace-author"))
        self.write(self.override, {"version": 1, "roles": {
            "author": {"model": "requested-author", "effort": "medium"}}})
        result = self.call("resolve", "--override", str(self.override))
        self.assertEqual(result.returncode, 0, result.stderr)
        roles = json.loads(result.stdout)["roles"]
        self.assertEqual(roles["author"]["requested"], {"model": "requested-author", "effort": "medium"})
        self.assertEqual(roles["author"]["source"], "explicit user request")
        self.assertEqual(roles["reviewer"]["requested"]["model"], "reviewer-v1")
        self.assertEqual(roles["reviewer"]["source"], str(self.local))
        self.local.unlink()
        self.assertEqual(json.loads(self.call().stdout)["roles"]["author"]["requested"]["model"], "author-v1")
        none_effort = config()
        none_effort["roles"]["author"]["effort"] = "none"
        self.write(self.user, none_effort)
        self.assertEqual(json.loads(self.call().stdout)["roles"]["author"]["requested"]["effort"], "none")

    def test_malformed_or_incomplete_policy_blocks_instead_of_falling_back(self):
        self.user.write_text("{broken")
        self.assertNotEqual(self.call().returncode, 0)
        for broken in (
            {"version": 1, "roles": {"author": {"model": "a", "effort": "high"}}},
            {"version": 1, "roles": {**config()["roles"], "author": {"effort": "high"}}},
            {"version": 1, "roles": {**config()["roles"], "author": {"model": "a"}}},
            {"version": 1, "roles": {**config()["roles"], "author": {"model": "", "effort": "high"}}},
            *({"version": 1, "roles": {**config()["roles"],
                                         "author": {"model": marker, "effort": "high"}}}
              for marker in ("inherit", "DEFAULT", "Auto", "automatic")),
            *({"version": 1, "roles": {**config()["roles"],
                                         "author": {"model": "author-v1", "effort": marker}}}
              for marker in ("INHERIT", "default", "AUTO", "Automatic")),
        ):
            with self.subTest(broken=broken):
                self.write(self.user, broken)
                result = self.call()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("blocked", result.stderr)

    def test_full_direct_request_overrides_broken_lower_policy(self):
        self.user.write_text("{broken")
        self.write(self.override, config(author="direct"))
        result = self.call("resolve", "--override", str(self.override))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["roles"]["author"]["requested"]["model"], "direct")

    def test_receipt_requires_actual_identity_and_independent_resolved_review(self):
        self.write(self.user, config())
        selection = json.loads(self.call().stdout)
        runs = {name: {"requested": entry["requested"], "resolved": entry["requested"],
                       "outcome": "passed" if name == "reviewer" else "complete"}
                for name, entry in selection["roles"].items()}
        runs["reviewer"].update(fresh_agent=True, findings_resolved=True)
        runs["tone_editor"] = {"requested": runs["author"]["requested"],
                               "resolved": runs["author"]["requested"],
                               "fresh_agent": True, "outcome": "complete"}
        receipt = self.root / "receipt.json"
        self.write(receipt, {"selection": selection, "long_lesson": False, "runs": runs})
        self.assertEqual(self.call("check", "--receipt", str(receipt)).returncode, 0)
        for change in (
            lambda r: r["runs"]["author"]["resolved"].update(model="other"),
            lambda r: r["runs"]["support"]["resolved"].update(effort="high"),
            lambda r: r["runs"]["reviewer"].update(fresh_agent=False),
            lambda r: r["runs"].pop("reviewer"),
            lambda r: r["runs"].pop("tone_editor"),
            lambda r: r["runs"].update(tone_editor={"requested": r["runs"]["author"]["requested"],
                                                     "resolved": {"model": "other", "effort": "high"},
                                                     "fresh_agent": True, "outcome": "complete"}),
        ):
            with self.subTest(change=change):
                data = json.loads(receipt.read_text())
                change(data)
                self.write(receipt, data)
                self.assertNotEqual(self.call("check", "--receipt", str(receipt)).returncode, 0)
                self.write(receipt, {"selection": selection, "long_lesson": False, "runs": runs})
        self.write(receipt, {"selection": selection, "long_lesson": True, "runs": runs})
        self.assertEqual(self.call("check", "--receipt", str(receipt)).returncode, 0)
        self.write(self.user, config(author="changed-policy"))
        self.assertNotEqual(self.call("check", "--receipt", str(receipt)).returncode, 0)

    def test_direct_author_request_still_requires_reviewer_runtime(self):
        self.write(self.override, {"version": 1, "roles": {
            "author": {"model": "direct", "effort": "high"}}})
        selection = json.loads(self.call("resolve", "--override", str(self.override)).stdout)
        receipt = self.root / "receipt.json"
        self.write(receipt, {"selection": selection, "long_lesson": False, "runs": {
            "author": {"requested": {"model": "direct", "effort": "high"},
                       "resolved": {"model": "direct", "effort": "high"}, "outcome": "complete"}}})
        result = self.call("check", "--override", str(self.override), "--receipt", str(receipt))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing reviewer", result.stderr)


if __name__ == "__main__":
    unittest.main()
