import warnings
from typing import Optional

warnings.warn(
    "Using pure Python (CPython) implementation of RouteTrie. "
    "For better performance, install the compiled Cython extension (wheel).",
    RuntimeWarning,
    stacklevel=2,
)


class Target:
    __slots__ = ("host", "port")

    host: bytes
    port: bytes

    def __init__(self, host: bytes, port: bytes):
        self.host = host
        self.port = port


class RouteTrieNode:
    __slots__ = ("children", "target")

    def __init__(self) -> None:
        self.children: dict[bytes, "RouteTrieNode"] = {}
        self.target: Optional[Target] = None


class RouteTrie:
    __slots__ = ("root",)

    def __init__(self) -> None:
        self.root: RouteTrieNode = RouteTrieNode()

    def insert(self, path: bytes, target: Target) -> None:
        node: RouteTrieNode = self.root
        parts: list[bytes] = [p for p in path.strip(b"/").split(b"/") if p]
        for part in parts:
            node = node.children.setdefault(part, RouteTrieNode())
        node.target = target

    def match(self, path: bytes) -> Optional[Target]:
        node: RouteTrieNode = self.root
        parts: list[bytes] = [p for p in path.strip(b"/").split(b"/") if p]
        last_target: Optional[Target] = self.root.target  # fallback to /
        for part in parts:
            if part in node.children:
                node = node.children[part]
                if node.target is not None:
                    last_target = node.target
            else:
                break
        return last_target
