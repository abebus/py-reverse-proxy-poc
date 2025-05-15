import pytest
from route_trie import RouteTrie, Target


@pytest.fixture
def trie():
    trie = RouteTrie()
    trie.insert(b"/", Target(host=b"default.local", port=b"80"))
    trie.insert(b"/api", Target(host=b"api.local", port=b"8080"))
    trie.insert(b"/api/v1", Target(host=b"apiv1.local", port=b"8081"))
    trie.insert(b"/static/assets", Target(host=b"static.local", port=b"8082"))
    return trie
