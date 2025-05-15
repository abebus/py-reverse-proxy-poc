def test_root_match(trie):
    key, target = trie.match(b"/")
    assert key == b"/"
    assert target.host == b"default.local"
    assert target.port == b"80"


def test_exact_match(trie):
    key, target = trie.match(b"/api")
    assert key == b"/api"
    assert target.host == b"api.local"
    assert target.port == b"8080"


def test_partial_match(trie):
    key, target = trie.match(b"/api/v1/resource")
    assert key == b"/api/v1"
    assert target.host == b"apiv1.local"
    assert target.port == b"8081"


def test_nested_match(trie):
    key, target = trie.match(b"/static/assets/css/style.css")
    assert key == b"/static/assets"
    assert target.host == b"static.local"
    assert target.port == b"8082"


def test_no_match_fallback_to_root(trie):
    key, target = trie.match(b"/unknown/path")
    assert key == b"/"
    assert target.host == b"default.local"
    assert target.port == b"80"


def test_trailing_slashes(trie):
    key, target = trie.match(b"/api/")
    assert key == b"/api"
    assert target.host == b"api.local"
    assert target.port == b"8080"


def test_double_slashes(trie):
    key, target = trie.match(b"//api//v1//")
    assert key == b"/api/v1"
    assert target.host == b"apiv1.local"
    assert target.port == b"8081"


def test_empty_path(trie):
    key, target = trie.match(b"")
    assert key == b"/"
    assert target.host == b"default.local"
    assert target.port == b"80"
