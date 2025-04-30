from pathlib import Path

import yaml

from route_trie import RouteTrie, Target


def load_routes(path: Path = Path(__file__).parent / "routes.yaml") -> RouteTrie:
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    trie = RouteTrie()
    data: dict[str, dict[str, dict[str, str]]]
    for route, target in data["routes"].items():
        trie.insert(
            route.encode(),
            Target(target["host"].encode(), str(target.get("port", "0")).encode()),
        )
    return trie
