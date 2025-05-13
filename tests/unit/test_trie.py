import unittest

from route_trie import RouteTrie, Target


class TestRouteTrie(unittest.TestCase):
    def setUp(self):
        self.trie = RouteTrie()
        self.trie.insert(b"/", Target(host=b"default.local", port=b"80"))
        self.trie.insert(b"/api", Target(host=b"api.local", port=b"8080"))
        self.trie.insert(b"/api/v1", Target(host=b"apiv1.local", port=b"8081"))
        self.trie.insert(b"/static/assets", Target(host=b"static.local", port=b"8082"))

    def test_root_match(self):
        key, target = self.trie.match(b"/")
        self.assertEqual(key, b"/")
        self.assertEqual(target.host, b"default.local")
        self.assertEqual(target.port, b"80")

    def test_exact_match(self):
        key, target = self.trie.match(b"/api")
        self.assertEqual(key, b"/api")
        self.assertEqual(target.host, b"api.local")
        self.assertEqual(target.port, b"8080")

    def test_partial_match(self):
        key, target = self.trie.match(b"/api/v1/resource")
        self.assertEqual(key, b"/api/v1")
        self.assertEqual(target.host, b"apiv1.local")
        self.assertEqual(target.port, b"8081")

    def test_nested_match(self):
        key, target = self.trie.match(b"/static/assets/css/style.css")
        self.assertEqual(key, b"/static/assets")
        self.assertEqual(target.host, b"static.local")
        self.assertEqual(target.port, b"8082")

    def test_no_match_fallback_to_root(self):
        key, target = self.trie.match(b"/unknown/path")
        self.assertEqual(key, b"/")
        self.assertEqual(target.host, b"default.local")
        self.assertEqual(target.port, b"80")

    def test_trailing_slashes(self):
        key, target = self.trie.match(b"/api/")
        self.assertEqual(key, b"/api")
        self.assertEqual(target.host, b"api.local")
        self.assertEqual(target.port, b"8080")

    def test_double_slashes(self):
        key, target = self.trie.match(b"//api//v1//")
        self.assertEqual(key, b"/api/v1")
        self.assertEqual(target.host, b"apiv1.local")
        self.assertEqual(target.port, b"8081")

    def test_empty_path(self):
        key, target = self.trie.match(b"")
        self.assertEqual(key, b"/")
        self.assertEqual(target.host, b"default.local")
        self.assertEqual(target.port, b"80")
