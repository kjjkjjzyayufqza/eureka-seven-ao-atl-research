"""Extract CPK archives with the installed PyCriCodecs parser and CRILAYLA codec.

This is a provenance/safety wrapper, not a new implementation of CPK or CRILAYLA.
"""

from __future__ import annotations

import argparse
from collections import Counter, deque
import hashlib
import json
from pathlib import Path

import CriCodecs
from PyCriCodecs import CPK


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def extract_one(source: Path, destination: Path) -> tuple[dict, list[Path]]:
    archive = CPK(str(source))
    try:
        header = archive.tables["CPK"]
        table = archive.tables.get("TOC")
        if table is None:
            raise ValueError(f"This wrapper requires a named TOC: {source}")
        base = min(header["TocOffset"][0], header["ContentOffset"][0])
        expected_count = header["Files"][0]
        if len(table["FileName"]) != expected_count:
            raise ValueError("Header and TOC entry counts disagree")
        destination = destination.resolve()
        destination.relative_to(ROOT)
        rows = []
        nested = []
        seen = set()
        for index, name in enumerate(table["FileName"]):
            directory = table["DirName"][index % len(table["DirName"])]
            relative = Path(directory.replace("\\", "/")) / name
            output = (destination / relative).resolve()
            output.relative_to(destination)
            identity = str(output).casefold()
            if identity in seen:
                raise ValueError(f"Duplicate output entry: {output}")
            seen.add(identity)
            packed_size = table["FileSize"][index % len(table["FileSize"])]
            unpacked_size = table["ExtractSize"][index % len(table["ExtractSize"])]
            offset = base + table["FileOffset"][index % len(table["FileOffset"])]
            if offset < 0 or offset + packed_size > source.stat().st_size:
                raise ValueError(f"Out-of-range archive entry: {relative}")
            archive.stream.seek(offset)
            data = archive.stream.read(packed_size)
            compressed = unpacked_size > packed_size
            if compressed:
                data = CriCodecs.CriLaylaDecompress(data)
            if len(data) != unpacked_size:
                raise ValueError(f"Extracted size mismatch: {relative}")
            digest = hashlib.sha256(data).hexdigest()
            output.parent.mkdir(parents=True, exist_ok=True)
            if output.exists():
                if sha256(output) != digest:
                    raise FileExistsError(f"Refusing to replace different data: {output}")
            else:
                with output.open("xb") as stream:
                    stream.write(data)
            rows.append({
                "index": index,
                "archive_path": relative.as_posix(),
                "output": output.relative_to(ROOT).as_posix(),
                "offset": offset,
                "packed_size": packed_size,
                "size": len(data),
                "compressed": compressed,
                "sha256": digest,
                "magic_hex": data[:16].hex(" "),
            })
            if data[:4] == b"CPK ":
                nested.append(output)
        return {
            "source": str(source),
            "source_sha256": sha256(source),
            "destination": str(destination),
            "header": header,
            "entries": rows,
        }, nested
    finally:
        archive.stream.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Researcher-provided EurekaAODataR.cpk input")
    args = parser.parse_args()
    queue = deque([(args.source.resolve(), ROOT / "extracted" / "root")])
    results = []
    while queue:
        source, destination = queue.popleft()
        result, nested = extract_one(source, destination)
        results.append(result)
        print(f"Extracted {len(result['entries'])} entries: {source.name}", flush=True)
        for child in nested:
            relative = child.relative_to(ROOT / "extracted")
            queue.append((child, ROOT / "extracted" / "nested" / (str(relative) + ".unpacked")))
    entries = [entry for archive in results for entry in archive["entries"]]
    summary = {
        "archives": len(results),
        "entries": len(entries),
        "extracted_bytes": sum(entry["size"] for entry in entries),
        "extensions": dict(Counter(Path(entry["output"]).suffix.lower() for entry in entries)),
    }
    write_json(ROOT / "manifests" / "archives.json", results)
    write_json(ROOT / "manifests" / "extraction-summary.json", summary)
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
