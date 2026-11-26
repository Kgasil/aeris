"""Real loopback HTTP tests, with a synthetic server (not an AI model)."""
from contextlib import contextmanager
import http.client
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import socket
import threading
import time
import unittest
from aeris.companion import chat, suggest_command

@contextmanager
def synthetic_server(status=200, payload=None, delay=0):
    records = []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def do_POST(self):
            body = self.rfile.read(int(self.headers["Content-Length"]))
            records.append((self.path, json.loads(body)))
            if delay:
                time.sleep(delay)
            data = json.dumps(payload if payload is not None else {
                "done": True, "message": {"role": "assistant", "content": "Synthetic answer"}
            }).encode()
            try:
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                if status == 302:
                    self.send_header("Location", "http://127.0.0.1:1/never-follow")
                self.end_headers()
                self.wfile.write(data)
            except OSError:
                pass
    with HTTPServer(("127.0.0.1", 11434), Handler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield records
        finally:
            server.shutdown()
            thread.join(timeout=3)

class LoopbackTests(unittest.TestCase):
    def test_real_http_only_explicit_message(self):
        with synthetic_server() as records:
            self.assertEqual(chat("fixture:local", (), "Synthetic question"), "Synthetic answer")
        self.assertEqual(len(records), 1)
        path, body = records[0]
        self.assertEqual(path, "/api/chat")
        self.assertEqual([m["role"] for m in body["messages"]], ["system", "user"])
        self.assertEqual(body["messages"][-1]["content"], "Synthetic question")
        self.assertFalse(body["stream"])
        self.assertEqual(body["keep_alive"], 0)
        self.assertNotIn("tools", body)

    def test_rejects_cloud_before_network(self):
        with synthetic_server() as records:
            with self.assertRaises(ValueError):
                chat("model-cloud", (), "Synthetic question")
            self.assertFalse(records)

    def test_refuses_redirect(self):
        with synthetic_server(status=302) as records:
            with self.assertRaises(OSError):
                chat("fixture", (), "Synthetic question")
            self.assertEqual(len(records), 1)

    def test_rejects_tool_calls(self):
        with synthetic_server(payload={"done": True, "message": {"role": "assistant",
                                "content": "Synthetic", "tool_calls": [{"function": {"name": "untrusted"}}]}}):
            with self.assertRaises(ValueError):
                chat("fixture", (), "Synthetic question")

    def test_suggestion_only_and_rejects_invalid_action(self):
        with synthetic_server(payload={"done": True, "message": {"role": "assistant",
                                "content": "Lembre-me de revisar em 20 minutos"}}) as records:
            self.assertEqual(suggest_command("fixture", "Synthetic reminder"), "Lembre-me de revisar em 20 minutos")
            self.assertEqual(len(records), 1)
            self.assertEqual(len(records[0][1]["messages"]), 2)
        with synthetic_server(payload={"done": True, "message": {"role": "assistant",
                                "content": "Delete all files"}}):
            with self.assertRaises(ValueError):
                suggest_command("fixture", "Synthetic request")

    def test_socket_timeout_with_shortened_test_deadline(self):
        def connection(host, port, timeout):
            self.assertEqual((host, port, timeout), ("127.0.0.1", 11434, 45))
            return http.client.HTTPConnection(host, port, timeout=0.2)
        with synthetic_server(delay=0.8):
            with self.assertRaises((TimeoutError, socket.timeout)):
                chat("fixture", (), "Synthetic question", connection_factory=connection)

    def test_unavailable_service(self):
        # Reserve the port first, proving we do not contact an existing Ollama instance.
        with socket.socket() as guard:
            guard.bind(("127.0.0.1", 11434))
            with self.assertRaises(OSError):
                chat("fixture", (), "Synthetic question")

if __name__ == "__main__":
    unittest.main(verbosity=2)
