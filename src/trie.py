from collections import namedtuple

Target = namedtuple("Target", ("host", "port"))


class RouteTrieNode:
    __slots__ = ("children", "target")

    def __init__(self) -> None:
        self.children: dict[bytes, RouteTrieNode] = {}
        self.target: None | Target = None


class RouteTrie:
    __slots__ = "root"

    def __init__(self) -> None:
        self.root = RouteTrieNode()

    def insert(self, path: bytes, target: Target) -> None:
        node = self.root
        parts = [p for p in path.strip(b"/").split(b"/") if p]
        for part in parts:
            node = node.children.setdefault(part, RouteTrieNode())
        node.target = target

    def match(self, path: bytes) -> None | Target:
        node = self.root
        parts = [p for p in path.strip(b"/").split(b"/") if p]
        last_target = self.root.target  # fallback to /
        for part in parts:
            if part in node.children:
                node = node.children[part]
                if node.target:
                    last_target = node.target
            else:
                break
        return last_target
