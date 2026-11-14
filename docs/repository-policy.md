# Repository and Publication Policy

## Purpose and language

This is a game-file research repository containing tooling and written findings. Write every project Markdown file in English, including rules, README files, notes and generated catalogs. Preserve existing upstream notices and licenses verbatim.

## Public files and private inputs

| Included in Git | Kept local and excluded from Git |
| --- | --- |
| Human-written English documentation | Original game archives and executables |
| Python research tools and format adapters | Decrypted ELF files, IDA databases and decompiled functions |
| Minimal pinned open-source parser modules and licenses | Models, textures, motions, shaders, effects, audio and video |
| Dependency attribution and source hashes | Converted GLB/Blender files and rendered previews |
| Repository rules and commit checks | Raw tables, asset manifests, logs, caches, backups and keys |

The private output roots are `analysis/`, `extracted/`, `converted/`, `playable/`, `previews/` and `manifests/`. Existing research data remains there for local use. Never add these outputs to Git, Git LFS or releases.

Concise findings, counts, format descriptions, source hashes and selected code-address observations may be documented in English. Raw publisher payloads, full disassembly and decompiled function listings must remain local. Do not disguise excluded material as source strings, Markdown or another allowed text extension.

## Enforcement

`.gitignore` denies root contents by default and admits named source/documentation categories. `scripts/check_public_tree.py` independently reads actual Git object bytes from the complete index or committed HEAD. It checks:

- Allowed paths and regular Git file modes; no symlinks or submodules.
- UTF-8 text, a 512 KiB per-file limit and rejection of binary signatures/control bytes.
- Markdown language checks, Python syntax and JSON syntax.
- Local account markers, workstation paths, unreviewed email addresses, private network addresses and credential/payload patterns.
- Exact SHA-256 values for four pinned upstream source/license files.
- Markdown links to public files rather than excluded local outputs.
- Seven negative examples covering a forced-add game path, asset output, raw table export, disguised binary, embedded binary, non-English Markdown and invalid Python.

The privacy check is heuristic and requires human review. It preserves pinned upstream author/license details and permits reserved placeholder email domains. Commit auditing separately permits the exact owner-approved Git identity in author and committer headers, with no exemption for file contents or commit messages. The language check rejects CJK writing; it is not a general natural-language classifier. Human review remains responsible for English prose and for ensuring allowed source text does not embed excluded data.

Enable the local hook in each clone; Git does not transfer local configuration:

```powershell
git config core.hooksPath .githooks
```

The hook runs `python scripts/check_public_tree.py --staged` before committing. It needs only Python's standard library and Git. Check committed contents after cloning with:

```powershell
python scripts/check_public_tree.py --tracked
```

Use `python scripts/check_public_tree.py --history` for publication auditing across all reachable commits and their metadata. This mode also requires `main` as the only local branch and rejects leftover unreachable Git objects.

Inspect the staged diff before committing. New public file categories require changes to both the ignore allowlist and the checker. Do not bypass the hook or force-add excluded data. Remote publication requires a separate user instruction.

## Pinned parsers and external tools

The complete upstream checkouts were moved outside the project. Only required source modules and original licenses remain under `third_party/`. `dependencies.lock.json` records authors, URLs, upstream commits and source/license hashes. Existing research audits now verify those hashes instead of expecting nested Git repositories.

The complete checkouts remain in a private cache outside the repository. This cache is outside the repository and is not required by the scripts. Unrelated upstream Markdown was not rewritten or republished.

PyCriCodecs/CriCodecs, Blender 5.1, IDA and scetool are separately installed tools. Their binaries, key material and proprietary databases are not included. The tested PyCriCodecs build has no verified upstream commit; see [tools and attribution](tools-and-attribution.md).

No project-wide license was inferred for original code or documentation. Included upstream licenses remain effective for their own files; see `NOTICE`.

## Cleanup record

On 2026-11-14, 32 historical console logs totaling 1,861,792 bytes were moved out of the project to the external cache's `historical-logs/` directory. This move is reversible. Model/animation outputs, original game inputs and useful JSON evidence were preserved locally. The private cleanup inventory is `manifests/repository-cleanup.json`.

The results in [validation](validation.md) describe the earlier asset audit. Repository preparation did not rerun expensive conversion or game execution. Its separate check covers actual source-only Git contents and dependency snapshot integrity.
