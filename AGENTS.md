# Research Repository Rules

This repository documents file-format research for the PS3 game Eureka Seven AO: Attack the Legend. Work here is limited to research tooling, human-written findings and reproducible instructions.

## Language

- Write every project Markdown file in English, including README files, rules, research notes and generated Markdown catalogs.
- Keep code comments, commit messages and repository metadata in English.
- Preserve upstream source notices and license text verbatim. Do not import unrelated upstream documentation.

## Source and publication boundary

- Treat original game files as read-only inputs supplied separately by each researcher.
- Never stage, commit or publish game executables, decrypted ELF files, publisher archives, extracted resources, models, textures, motion data, audio, video, shader binaries or effect data.
- Never commit full disassembly, decompiled game functions, IDA databases, raw game table exports, memory dumps, keys, credentials or generated asset manifests.
- Keep `analysis/`, `extracted/`, `converted/`, `playable/`, `previews/` and `manifests/` local and ignored.
- Publish concise human-written conclusions, format descriptions, source hashes and tool attribution instead of raw game payloads.
- Do not embed excluded payloads in text, source files, Git LFS objects, releases or repository history.
- Do not force-add ignored files or bypass repository checks. Review the staged diff before committing.
- Keep private account names, home/workstation paths, private contact details, credentials and private network addresses out of public files and commit metadata. Supply local input paths through explicit arguments or private environment settings.
- Use the project owner's approved Git name and GitHub noreply email for both author and committer attribution. Allow this identity only in the corresponding commit headers; do not replace it with anonymous attribution unless the owner requests that change. Preserve genuine upstream authors and licenses. Check reachable history before publication.
- Do not create a remote repository, publish, push or change third-party resources unless the user asks for that external action.

## Dependencies and reproducibility

- Search for existing format research before writing a new decoder.
- Preserve the upstream author, source URL, pinned commit, license and exact file hashes in `dependencies.lock.json` and the attribution document.
- Keep vendored sources unmodified; implement title-specific adapters under `scripts/`.
- Use Blender 5.1 for production conversion and playback. Historical Blender 4.2 experiments are not final verification.
- Document commands, formats, conversion assumptions and remaining uncertainty in `docs/` using English.

## Git checks

Use `main` as the project's single working branch. Do not create task-specific branches unless the user explicitly changes this policy. Keep project files and Git metadata free of AI tool branding, generated-by labels and assistant co-author trailers. Preserve genuine upstream author attribution and licenses.

The ignore file uses an explicit source-only allowlist. `scripts/check_public_tree.py` independently checks staged Git blobs, so a forced addition of an excluded path still fails the local commit hook.

After cloning, enable the local hook:

```powershell
git config core.hooksPath .githooks
```

Before committing, inspect `git diff --cached`. Run `python scripts/check_public_tree.py --staged` when checking a prepared index without committing, or `python scripts/check_public_tree.py --tracked` to check committed files. The pre-commit hook runs the staged check automatically.

New public file categories require a deliberate update to both `.gitignore` and the checker. Never relax these rules to include game data.

Before publication, run `python scripts/check_public_tree.py --history`. Private historical backups must remain outside the publication repository.
