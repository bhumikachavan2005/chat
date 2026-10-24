"""
End-to-End HTTP Integration Test Suite
Verifies all HTTP endpoints, static assets, auth guard, search, stats, memories, and insights.
"""

import urllib.request
import urllib.parse
import json
import unittest
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

BASE_URL = "http://127.0.0.1:8765"


class TestHttpE2E(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import socket
        import time
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", 8765)) != 0:
                import threading, uvicorn
                from backend.main import app
                config = uvicorn.Config(app, host="127.0.0.1", port=8765, log_level="error")
                cls.server = uvicorn.Server(config)
                cls.thread = threading.Thread(target=cls.server.run, daemon=True)
                cls.thread.start()
                time.sleep(1.5)

    def make_request(self, endpoint, method="GET", data=None, token=None):
        url = f"{BASE_URL}{endpoint}"
        headers = {}
        if token:
            headers["X-Archive-Token"] = token
        
        encoded_data = None
        if data is not None:
            headers["Content-Type"] = "application/json"
            encoded_data = json.dumps(data).encode("utf-8")

        req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                status = resp.status
                content = resp.read()
                try:
                    return status, json.loads(content.decode("utf-8"))
                except Exception:
                    return status, content
        except urllib.error.HTTPError as e:
            try:
                err_body = json.loads(e.read().decode("utf-8"))
                return e.code, err_body
            except Exception:
                return e.code, str(e)

    def test_01_static_assets(self):
        # Index HTML
        status, content = self.make_request("/")
        self.assertEqual(status, 200)
        self.assertIn(b"Vinu", content)

        # Style CSS
        status, css = self.make_request("/static/css/style.css")
        self.assertEqual(status, 200)
        self.assertIn(b":root", css)

        # App JS
        status, js = self.make_request("/static/js/app.js")
        self.assertEqual(status, 200)
        self.assertIn(b"window.App", js)

    def test_02_auth_protection_and_setup(self):
        # 1. Access protected endpoint without token -> Expect 401
        status, res = self.make_request("/api/chat/bounds")
        self.assertEqual(status, 401)

        # 2. Check auth status
        status, res = self.make_request("/api/auth/status")
        self.assertEqual(status, 200)
        self.assertIn("has_password", res)

        # 3. Setup / Login
        if not res["has_password"]:
            status, auth_res = self.make_request("/api/auth/setup", method="POST", data={"password": "SecretPassword123!"})
            self.assertEqual(status, 200)
            token = auth_res["token"]
        else:
            status, auth_res = self.make_request("/api/auth/login", method="POST", data={"password": "SecretPassword123!"})
            self.assertEqual(status, 200)
            token = auth_res.get("token")

        self.assertIsNotNone(token)
        TestHttpE2E.token = token

    def test_03_chat_bounds_and_messages(self):
        token = getattr(TestHttpE2E, "token", None)
        self.assertIsNotNone(token)

        # Bounds
        status, bounds = self.make_request("/api/chat/bounds", token=token)
        self.assertEqual(status, 200)
        self.assertGreater(bounds["total_count"], 10000)

        # Messages list
        status, msgs = self.make_request("/api/chat/messages?limit=20&offset=0", token=token)
        self.assertEqual(status, 200)
        self.assertEqual(len(msgs["messages"]), 20)
        self.assertIn("sender_clean", msgs["messages"][0])

    def test_04_search_fts5(self):
        token = getattr(TestHttpE2E, "token", None)
        status, s_res = self.make_request("/api/search?q=internship", token=token)
        self.assertEqual(status, 200)
        self.assertGreater(s_res["total"], 0)
        self.assertTrue(len(s_res["results"]) > 0)
        self.assertIn("highlighted_content", s_res["results"][0])

    def test_05_stats_timeline_evolution(self):
        token = getattr(TestHttpE2E, "token", None)

        # Stats
        status, stats = self.make_request("/api/stats/overview", token=token)
        self.assertEqual(status, 200)
        self.assertGreater(stats["total_messages"], 10000)
        self.assertIn("hourly_stats", stats)

        # Timeline
        status, tl = self.make_request("/api/stats/timeline", token=token)
        self.assertEqual(status, 200)
        self.assertTrue(len(tl) > 0)

        # Evolution
        status, evo = self.make_request("/api/stats/evolution", token=token)
        self.assertEqual(status, 200)
        self.assertIn("period_1", evo)
        self.assertIn("period_2", evo)

    def test_06_insights_and_funny(self):
        token = getattr(TestHttpE2E, "token", None)

        # Prebuilt insights list
        status, prebuilt = self.make_request("/api/insights/prebuilt", token=token)
        self.assertEqual(status, 200)
        self.assertTrue(len(prebuilt["insights"]) >= 5)

        # Query specific insight
        status, ins = self.make_request("/api/insights/query/internship_first_ask", token=token)
        self.assertEqual(status, 200)
        self.assertIn("Bhuu", ins["answer"])
        self.assertTrue(len(ins["sources"]) > 0)

        # Funny moments
        status, funny = self.make_request("/api/funny/moments", token=token)
        self.assertEqual(status, 200)
        self.assertTrue(len(funny["moments"]) > 0)

    def test_07_memories_lifecycle(self):
        token = getattr(TestHttpE2E, "token", None)

        # Get first message ID
        status, msgs = self.make_request("/api/chat/messages?limit=1&offset=0", token=token)
        msg_id = msgs["messages"][0]["id"]

        # Create memory
        status, mem = self.make_request("/api/memories", method="POST", data={
            "message_id": msg_id,
            "category": "friendship",
            "note": "Special bond test note",
            "tags": "test,friendship"
        }, token=token)
        self.assertEqual(status, 200)
        mem_id = mem["id"]

        # List memories
        status, mem_list = self.make_request("/api/memories?category=friendship", token=token)
        self.assertEqual(status, 200)
        self.assertTrue(any(m["id"] == mem_id for m in mem_list))

        # Delete memory
        status, del_res = self.make_request(f"/api/memories/{mem_id}", method="DELETE", token=token)
        self.assertEqual(status, 200)

    def test_08_wrapped_story(self):
        token = getattr(TestHttpE2E, "token", None)
        status, res = self.make_request("/api/wrapped/story", token=token)
        self.assertEqual(status, 200)
        self.assertIn("slides", res)
        self.assertTrue(len(res["slides"]) >= 1)


if __name__ == "__main__":
    unittest.main()
