"""Kernel Lab routes Phase 5 API calls through the shared USGApplication."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import threading
import time
import unittest
from urllib.request import Request, urlopen
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = ROOT / "tools" / "usg-kernel-lab" / "server.py"
SPEC = importlib.util.spec_from_file_location("usg_phase5_kernel_lab_server", SERVER_PATH)
SERVER_MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SERVER_MODULE)


class Phase5KernelLabTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.server = SERVER_MODULE.create_lab_server(
            str(Path(self.temp.name) / "kernel-lab.sqlite3"), port=0
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"
        for _ in range(30):
            try:
                self.request("GET", "/health")
                break
            except Exception:
                time.sleep(0.1)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.temp.cleanup()

    def request(self, method, path, payload=None):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(
            self.base + path, data=data, method=method,
            headers={"Content-Type": "application/json"} if data is not None else {},
        )
        with urlopen(request, timeout=10) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def test_kernel_lab_health_and_phase5_resource_route(self):
        status, health = self.request("GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(health["phase5Pipeline"], "USG-INTERPRET/0.2.0")
        status, resources = self.request("GET", "/v2/resources")
        self.assertEqual(status, 200)
        self.assertGreaterEqual(len(resources["manifest"]["resources"]), 10)

    def test_kernel_lab_phase5_interpretation_and_replay_routes(self):
        status, result = self.request("POST", "/v2/interpret", {
            "text": "Ada writes code.", "language": "en", "persist": True,
        })
        self.assertEqual(status, 200)
        run_id = result["persistence"]["run_id"]
        status, replay = self.request(
            "POST", "/v2/interpretations/" + run_id + "/replay", {}
        )
        self.assertEqual(status, 200)
        self.assertTrue(replay["deterministic_match"])
        status, exported = self.request(
            "GET", "/v2/interpretations/" + run_id + "/export"
        )
        self.assertEqual(status, 200)
        self.assertEqual(exported["source"]["text"], "Ada writes code.")

    def test_kernel_lab_page_exposes_phase5_controls(self):
        with urlopen(self.base + "/", timeout=10) as response:
            status = response.status
            html = response.read().decode("utf-8")
        self.assertEqual(status, 200)
        self.assertIn("phase5InterpretBtn", html)
        self.assertIn("phase5ResourcesBtn", html)
        self.assertIn("phase5ReplayBtn", html)
        self.assertIn("phase5Explanation", html)
        self.assertIn("PHASE5_STAGE_GUIDE", html)
        self.assertIn("Inspect token candidates and morphology evidence", html)
        self.assertIn("Earliest stage with an explicit diagnostic", html)


if __name__ == "__main__":
    unittest.main()
