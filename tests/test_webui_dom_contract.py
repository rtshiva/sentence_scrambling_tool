import unittest
import os
import re
import subprocess
import shutil

class TestWebUIDOMContract(unittest.TestCase):
    """
    Automated DOM and Frontend Contract Test Suite.
    Ensures that:
    1. 100% of DOM element IDs queried by app.js exist in index.html.
    2. Dynamic gameplay loading (blanks, jigsaw, studios) executes without JS errors
       and properly renders blanks, slots, and candidate chips.
    """

    def setUp(self):
        self.repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.html_path = os.path.join(self.repo_root, "ui", "web", "index.html")
        self.js_path = os.path.join(self.repo_root, "ui", "web", "app.js")
        self.node_test_path = os.path.join(self.repo_root, "tests", "test_webui_frontend.js")

    def test_dom_ids_exist_in_html(self):
        """Verify that every document.getElementById call in app.js has a matching element in index.html."""
        with open(self.html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        with open(self.js_path, 'r', encoding='utf-8') as f:
            js_content = f.read()

        js_ids = set(re.findall(r"document\.getElementById\(['\"]([^'\"]+)['\"]\)", js_content))
        html_ids = set(re.findall(r'id=["\']([^"\']+)["\']', html_content))

        missing = sorted([i for i in js_ids if i not in html_ids])
        self.assertEqual(
            missing,
            [],
            f"The following DOM IDs are queried in app.js but are missing from index.html: {missing}"
        )

    def test_frontend_node_dom_execution(self):
        """Execute the headless mock DOM frontend test suite using Node.js."""
        node_bin = shutil.which("node")
        if not node_bin:
            self.skipTest("Node.js is not available in environment to run headless DOM execution test.")

        result = subprocess.run(
            [node_bin, self.node_test_path],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )

        if result.returncode != 0:
            safe_out = (result.stdout or '').encode('ascii', errors='replace').decode()
            safe_err = (result.stderr or '').encode('ascii', errors='replace').decode()
            print("Node Test Stdout:\n", safe_out)
            print("Node Test Stderr:\n", safe_err)

        safe_fail_msg = f"Frontend DOM test failed with exit code {result.returncode}:\n{(result.stdout or '').encode('ascii', errors='replace').decode()}\n{(result.stderr or '').encode('ascii', errors='replace').decode()}"
        self.assertEqual(
            result.returncode,
            0,
            safe_fail_msg
        )
        self.assertIn("USE CASE & GAMEPLAY SCENARIOS PASSED", result.stdout)

if __name__ == '__main__':
    unittest.main()
