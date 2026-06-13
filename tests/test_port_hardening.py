import os
import socket
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import compare_server as cs


def _a_free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


class TestPortHardening(unittest.TestCase):
    def test_port_in_use_detects_bound_socket(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.bind(("127.0.0.1", 0))
        srv.listen(1)
        port = srv.getsockname()[1]
        try:
            self.assertTrue(cs._port_in_use("127.0.0.1", port))
        finally:
            srv.close()

    def test_resolve_free_port_returns_same(self):
        free = _a_free_port()
        self.assertEqual(cs._resolve_port("127.0.0.1", free, None), (free, False))

    def test_resolve_busy_stale_picks_next(self):
        orig_in_use, orig_serves = cs._port_in_use, cs._serves_session
        cs._port_in_use = lambda h, p: p == 6000
        cs._serves_session = lambda h, p, s: False
        try:
            self.assertEqual(cs._resolve_port("127.0.0.1", 6000, "sid"), (6001, False))
        finally:
            cs._port_in_use, cs._serves_session = orig_in_use, orig_serves

    def test_resolve_busy_serving_reuses(self):
        orig_in_use, orig_serves = cs._port_in_use, cs._serves_session
        cs._port_in_use = lambda h, p: True
        cs._serves_session = lambda h, p, s: True
        try:
            self.assertEqual(cs._resolve_port("127.0.0.1", 6000, "sid"), (6000, True))
        finally:
            cs._port_in_use, cs._serves_session = orig_in_use, orig_serves


if __name__ == "__main__":
    unittest.main()
