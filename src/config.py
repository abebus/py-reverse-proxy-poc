import yaml

from .trie import RouteTrie, Target


def load_routes(path="routes.yaml"):
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    trie = RouteTrie()
    for route, target in data["routes"].items():
        trie.insert(route, Target(target["host"], target.get("port", 0)))
    return trie
