# Layer 4-ish (layer 7 path routing aware) reverse proxy

This proxy is Layer 7 in theory (it reads the URL/Connection header) but Layer 4 in practice (forwards everything else as raw TCP).

Run test from repo root (not from `./test`)
```
uv run python -m pytest tests/
```

Building wheels
```
uv build
```