"""Fail closed on non-source Git blobs, without importing game dependencies.

Checks the index by default; --tracked checks HEAD for clean-clone validation.
The working tree and ignored research outputs are never used as blob inputs.
"""

import argparse
import ast
import io
import json
from pathlib import Path
import posixpath
import re
import subprocess
import sys

from vendor_integrity import verify_dependencies
from publication_privacy import check_privacy_examples, local_identity_markers, validate_commit_metadata, validate_privacy_text

ROOT = Path(__file__).resolve().parents[1]
MAX_BLOB_BYTES = 512 * 1024
EXACT_PATHS = {
    ".gitignore", ".gitattributes", "AGENTS.md", "README.md", "NOTICE",
    "requirements.txt", "dependencies.lock.json", ".githooks/pre-commit",
    "third_party/README.md", "third_party/ed8pkg2glb/LICENSE",
    "third_party/ed8pkg2glb/src/ed8pkg2glb.py",
    "third_party/srw-og-infinite-battle-korean/LICENSE",
    "third_party/srw-og-infinite-battle-korean/tools/csvb.py",
}
REQUIRED_PATHS = EXACT_PATHS | {
    "docs/repository-policy.md", "docs/tools-and-attribution.md",
    "scripts/check_public_tree.py", "scripts/vendor_integrity.py", "scripts/publication_privacy.py",
}
NON_ENGLISH_SCRIPT = re.compile(
    r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af\U00020000-\U0003134f]"
)


def git(*args, data=None):
    return subprocess.run(
        ["git", *args], cwd=ROOT, input=data, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=True,
    ).stdout


def allowed_path(path):
    return path in EXACT_PATHS or bool(re.fullmatch(
        r"(?:docs/[A-Za-z0-9_-]+\.md|scripts/[A-Za-z0-9_]+\.py)", path
    ))


def validate_blob(path, data, mode="100644"):
    if not allowed_path(path):
        raise ValueError(f"Path is outside the public source allowlist: {path}")
    if mode not in {"100644", "100755"}:
        raise ValueError(f"Symlinks and submodules are forbidden: {path}")
    if path == ".githooks/pre-commit" and mode != "100755":
        raise ValueError("The pre-commit hook must be executable in Git")
    if len(data) > MAX_BLOB_BYTES:
        raise ValueError(f"Public text exceeds the size limit: {path}")
    if b"\0" in data or data.startswith((
        b"\x7fELF", b"MZ", b"CPK ", b"BLENDER", b"glTF", b"\x89PNG",
        b"\xff\xd8\xff", b"PK\x03\x04", b"SQLite format 3",
    )):
        raise ValueError(f"Binary/game payload is forbidden: {path}")
    text = data.decode("utf-8-sig")
    if any(ord(char) < 32 and char not in "\t\r\n" for char in text):
        raise ValueError(f"Non-text control bytes are forbidden: {path}")
    if re.search(r"-----BEGIN [A-Z ]*PRIVATE KEY-----", text):
        raise ValueError(f"Private key material is forbidden: {path}")
    if path.endswith(".md") and NON_ENGLISH_SCRIPT.search(text):
        raise ValueError(f"Markdown must be written in English: {path}")
    if path.endswith(".py"):
        ast.parse(text, filename=path)
    if path.endswith(".json"):
        json.loads(text)
    return text


def check_policy_examples():
    """Exercise forced-add, disguised binary, language and syntax rejection."""
    validate_blob("docs/example.md", b"# English research note\n")
    validate_blob("scripts/example.py", b"value = 1\n")
    forbidden = [
        ("analysis/EBOOT.ELF", b"\x7fELF\0"),
        ("playable/model.blend", b"BLENDER"),
        ("manifests/raw-table.json", b"{}"),
        ("docs/dump.md", b"\x7fELFdata"),
        ("scripts/hidden.py", b"x\0y"),
        ("docs/note.md", "\u4e2d\u6587".encode()),
        ("scripts/broken.py", b"def broken("),
    ]
    for path, data in forbidden:
        try:
            validate_blob(path, data)
        except (ValueError, SyntaxError):
            continue
        raise ValueError(f"Repository guard failed its rejection example: {path}")


def read_entries(tracked, revision="HEAD"):
    entries = {}
    if tracked:
        records = git("ls-tree", "-r", "-z", revision).split(b"\0")
    else:
        records = git("ls-files", "--stage", "-z").split(b"\0")
    for record in filter(None, records):
        metadata, name = record.split(b"\t", 1)
        path = name.decode("utf-8")
        first, second, third = metadata.decode("ascii").split()
        if tracked:
            mode, kind, oid = first, second, third
            if kind != "blob":
                raise ValueError(f"Non-blob Git entry is forbidden: {path}")
        else:
            mode, oid, stage = first, second, third
            if stage != "0":
                raise ValueError(f"Unresolved index conflict: {path}")
        if not allowed_path(path) or mode not in {"100644", "100755"}:
            raise ValueError(f"Excluded path or Git mode: {path} ({mode})")
        entries[path] = (mode, oid)
    missing = REQUIRED_PATHS - entries.keys()
    if missing:
        raise ValueError("Required public files missing: " + ", ".join(sorted(missing)))
    return entries


def read_blobs(entries):
    # Inspect sizes before asking Git to materialize any blob content.
    oids = list(dict.fromkeys(oid for mode, oid in entries.values()))
    request = ("\n".join(oids) + "\n").encode("ascii")
    metadata = git("cat-file", "--batch-check", data=request).decode("ascii")
    for line in metadata.splitlines():
        oid, kind, size = line.split()
        if kind != "blob" or int(size) > MAX_BLOB_BYTES:
            raise ValueError(f"Excluded Git object type or size: {oid}")
    stream = io.BytesIO(git("cat-file", "--batch", data=request))
    objects = {}
    for expected_oid in oids:
        oid, kind, size = stream.readline().decode("ascii").split()
        if oid != expected_oid or kind != "blob":
            raise ValueError("Unexpected Git batch object")
        payload = stream.read(int(size))
        if len(payload) != int(size) or stream.read(1) != b"\n":
            raise ValueError("Truncated Git batch object")
        objects[oid] = payload
    return {path: objects[oid] for path, (mode, oid) in entries.items()}


def check_local_links(texts):
    for path, text in texts.items():
        if not path.endswith(".md"):
            continue
        for target in re.findall(r"\[[^\]]*\]\(([^)\s]+)\)", text):
            if target.startswith(("https://", "http://", "mailto:", "#")):
                continue
            target = target.split("#", 1)[0]
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(path), target))
            if resolved not in texts:
                raise ValueError(f"Markdown links to a non-public file: {path}: {target}")


def audit_tree(entries, markers):
    blobs = read_blobs(entries)
    texts = {path: validate_blob(path, data, entries[path][0]) for path, data in blobs.items()}
    revisions = verify_dependencies(blobs.__getitem__)
    lock = json.loads(blobs["dependencies.lock.json"])
    vendored = {path for dependency in lock["dependencies"].values() for path in dependency["files"]}
    for path, text in texts.items():
        validate_privacy_text(path, text, markers, upstream=path in vendored)
    check_local_links(texts)
    return blobs, revisions


def audit_history(markers, checked_commit, checked_entries):
    refs = git("for-each-ref", "--format=%(refname)").decode().splitlines()
    heads = [ref for ref in refs if ref.startswith("refs/heads/")]
    if heads != ["refs/heads/main"]:
        raise ValueError("Publication history must contain only the main local branch")
    validate_privacy_text("Git references", "\n".join(refs), markers)
    commits = git("rev-list", "--all").decode().splitlines()
    identity = tuple(git("config", "--get", key).decode().strip() for key in ("user.name", "user.email"))
    blob_ids = set()
    for commit in commits:
        metadata = git("cat-file", "commit", commit).decode("utf-8")
        validate_commit_metadata(metadata, markers, identity)
        entries = checked_entries if commit == checked_commit else read_entries(True, commit)
        if commit != checked_commit:
            audit_tree(entries, markers)
        blob_ids.update(oid for mode, oid in entries.values())
    unreachable = git("fsck", "--full", "--no-reflogs", "--unreachable").decode().strip()
    if unreachable:
        raise ValueError("Unreachable Git objects remain; review private historical copies")
    return {"reachable_commits": len(commits), "unique_history_blobs": len(blob_ids), "unreachable_objects": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--staged", action="store_true", help="Check the complete Git index")
    mode.add_argument("--tracked", action="store_true", help="Check committed HEAD blobs")
    mode.add_argument("--history", action="store_true", help="Audit every reachable commit and metadata")
    args = parser.parse_args()
    check_policy_examples()
    privacy_examples = check_privacy_examples()
    markers = local_identity_markers()
    entries = read_entries(args.tracked or args.history)
    blobs, revisions = audit_tree(entries, markers)
    history = audit_history(markers, git("rev-parse", "HEAD").decode().strip(), entries) if args.history else {}
    print("PUBLIC_TREE_PASSED " + json.dumps({
        "source": "history" if args.history else "HEAD" if args.tracked else "index",
        "files": len(blobs), "bytes": sum(map(len, blobs.values())),
        "english_markdown_files": sum(path.endswith(".md") for path in blobs),
        "vendored_files_hash_verified": 4, "rejection_examples": 7,
        "privacy_rejection_examples": privacy_examples, **history,
    }, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, SyntaxError, KeyError, OSError, subprocess.CalledProcessError) as error:
        print(f"PUBLIC_TREE_FAILED: {error}", file=sys.stderr)
        sys.exit(1)
