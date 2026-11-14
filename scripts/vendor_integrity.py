"""Verify minimal upstream source snapshots without nested Git repositories."""

import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def verify_dependencies(read_bytes=None):
    """Return pinned commits after checking every source and license blob.

    A custom reader lets the repository checker verify index/HEAD bytes rather
    than accidentally trusting the working tree.
    """
    if read_bytes is None:
        read_bytes = lambda name: (ROOT / name).read_bytes()
    lock = json.loads(read_bytes("dependencies.lock.json"))
    if lock.get("schema_version") != 1:
        raise ValueError("Unsupported dependency lock schema")
    dependencies = lock["dependencies"]
    expected_paths = {
        "ed8pkg2glb": {
            "third_party/ed8pkg2glb/src/ed8pkg2glb.py",
            "third_party/ed8pkg2glb/LICENSE",
        },
        "csvb": {
            "third_party/srw-og-infinite-battle-korean/tools/csvb.py",
            "third_party/srw-og-infinite-battle-korean/LICENSE",
        },
    }
    if dependencies.keys() != expected_paths.keys():
        raise ValueError("Unexpected dependency set")
    revisions = {}
    for name, dependency in dependencies.items():
        if set(dependency["files"]) != expected_paths[name]:
            raise ValueError(f"Unexpected vendored file set: {name}")
        if not re.fullmatch(r"[0-9a-f]{40}", dependency["commit"]):
            raise ValueError(f"Invalid pinned commit: {name}")
        if not all(dependency.get(key) for key in ("author", "repository", "license")):
            raise ValueError(f"Incomplete attribution: {name}")
        for path, expected in dependency["files"].items():
            actual = hashlib.sha256(read_bytes(path)).hexdigest()
            if actual != expected:
                raise ValueError(f"Pinned dependency bytes differ: {path}")
        revisions[name] = dependency["commit"]
    return revisions
