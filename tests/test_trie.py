import unittest

from src.trie import RouteTrie, Target


class TestRouteTrie(unittest.TestCase):
    def setUp(self):
        self.trie = RouteTrie()
        self.trie.insert(b"/", Target(host="default.local", port=80))
        self.trie.insert(b"/api", Target(host="api.local", port=8080))
        self.trie.insert(b"/api/v1", Target(host="apiv1.local", port=8081))
        self.trie.insert(b"/static/assets", Target(host="static.local", port=8082))

    def test_root_match(self):
        target = self.trie.match(b"/")
        self.assertEqual(target.host, "default.local")
        self.assertEqual(target.port, 80)

    def test_exact_match(self):
        target = self.trie.match(b"/api")
        self.assertEqual(target.host, "api.local")
        self.assertEqual(target.port, 8080)

    def test_partial_match(self):
        target = self.trie.match(b"/api/v1/resource")
        self.assertEqual(target.host, "apiv1.local")
        self.assertEqual(target.port, 8081)

    def test_nested_match(self):
        target = self.trie.match(b"/static/assets/css/style.css")
        self.assertEqual(target.host, "static.local")
        self.assertEqual(target.port, 8082)

    def test_no_match_fallback_to_root(self):
        target = self.trie.match(b"/unknown/path")
        self.assertEqual(target.host, "default.local")
        self.assertEqual(target.port, 80)

    def test_trailing_slashes(self):
        target = self.trie.match(b"/api/")
        self.assertEqual(target.host, "api.local")
        self.assertEqual(target.port, 8080)

    def test_double_slashes(self):
        target = self.trie.match(b"//api//v1//")
        self.assertEqual(target.host, "apiv1.local")
        self.assertEqual(target.port, 8081)

    def test_empty_path(self):
        target = self.trie.match(b"")
        self.assertEqual(target.host, "default.local")
        self.assertEqual(target.port, 80)
