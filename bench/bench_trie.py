import timeit
from random import choice, randint

from route_trie import RouteTrie, Target

trie = RouteTrie()
test_paths = [
    b"/",
    b"/api",
    b"/api/v1",
    b"/api/v1/users",
    b"/api/v1/users/profile",
    b"/api/v1/users/profile/settings/security/password/static",
    b"/static/css",
    b"/static/js",
    b"/static/images",
    b"/products",
    b"/products/electronics",
    b"/products/clothing",
    b"/admin",
    b"/admin/dashboard",
    b"/blog",
    b"/blog/posts",
    b"/contact",
]

# Populate trie
for path in test_paths:
    trie.insert(
        path,
        Target(
            host=f"{path.decode('ascii').replace('/', '')}.local".encode("ascii"),
            port=str(randint(8000, 9000)).encode("ascii"),
        ),
    )


def benchmark_insert(num_inserts=10000):
    def insert_operation():
        path = b"/benchmark/" + str(randint(1, 1000)).encode("ascii")
        trie.insert(path, Target(host=b"benchmark.local", port=b"9999"))

    time = timeit.timeit(insert_operation, number=num_inserts)
    print(f"Insert {num_inserts:,} random paths: {time:.4f} seconds")


def benchmark_exact_match(num_iter=100000):
    def exact_match_operation():
        path = choice(test_paths)
        trie.match(path)

    time = timeit.timeit(exact_match_operation, number=num_iter)
    print(f"Exact match lookup ({num_iter:,} iterations): {time:.4f} seconds")


def benchmark_partial_match(num_iter=100000):
    def partial_match_operation():
        base_path = choice(test_paths)
        path = base_path + b"/extra/parts" if base_path != b"/" else b"/extra/parts"
        trie.match(path)

    time = timeit.timeit(partial_match_operation, number=num_iter)
    print(f"Partial match lookup ({num_iter:,} iterations): {time:.4f} seconds")


def benchmark_root_match(num_iter=100000):
    def root_match_operation():
        trie.match(b"/")

    time = timeit.timeit(root_match_operation, number=num_iter)
    print(f"Root path lookup ({num_iter:,} iterations): {time:.4f} seconds")


def benchmark_no_match(num_iter=100000):
    def no_match_operation():
        trie.match(b"/nonexistent/path")

    time = timeit.timeit(no_match_operation, number=num_iter)
    print(f"Non-existent path lookup ({num_iter:,} iterations): {time:.4f} seconds")


def benchmark_deep_nested_match(num_iter=100000):
    def deep_match_operation():
        trie.match(b"/api/v1/users/profile/settings/security/password")

    time = timeit.timeit(deep_match_operation, number=num_iter)
    print(f"Deep nested path lookup ({num_iter:,} iterations): {time:.4f} seconds")


def run_all():
    print("=== RouteTrie Performance Benchmarks ===")
    for num_iter in [10_000, 100_000, 1_000_000]:
        print(f"\n--- Benchmarking {num_iter:,} iterations ---")
        benchmark_insert(num_iter)
        benchmark_exact_match(num_iter)
        benchmark_partial_match(num_iter)
        benchmark_root_match(num_iter)
        benchmark_no_match(num_iter)
        benchmark_deep_nested_match(num_iter)


if __name__ == "__main__":
    run_all()
