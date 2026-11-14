# Publication Privacy and Content Audit

Audit date: 2026-11-14. Scope: the local source-only repository before any remote publication.

## Findings and remediation

| Finding | Publication risk | Remediation |
| --- | --- | --- |
| Home-directory paths in two documents | Reveals a local account name and installation layout | Replaced with PATH-based Python and private environment settings |
| Workstation paths in documentation and two script defaults | Reveals local folder layout and couples reproduction to one machine | Removed absolute workstation paths; extraction and EBOOT auditing now require explicit input arguments |
| Git author and committer attribution | Must identify the project owner without exposing a private mailbox | Use the owner's approved Git name and GitHub noreply address; permit this identity only in the two attribution headers |
| Earlier unpublished Git snapshots retain prior text/metadata | Current-tree cleanup alone leaves historical exposure | Rewrite the unpublished root commit; retain a private external backup and remove superseded objects/reflogs from the publication repository |
| Original commit hook checks file boundaries but has limited privacy checks | Future source/documentation edits could reintroduce private data | Add reusable privacy checks and a full reachable-history audit mode |

The initial pattern scan covered all 44 tracked files. It found no provider-token, credential-assignment, credential-bearing URL, email, private-network address or large embedded-payload candidates in those file contents. Git metadata is checked separately: the owner's approved public Git attribution is permitted in author/committer headers, while commit messages and other metadata retain the ordinary privacy checks.

## Audited publication boundary

The repository includes only research scripts, English documentation, repository metadata and four pinned upstream source/license files. Game archives, executables, decrypted ELF files, models, textures, animation data, audio/video, IDA databases, decompiled functions, raw tables, manifests, logs and generated outputs remain excluded.

The `main` branch is the only current reference. The audit covers every commit reachable from any reference, not only the latest working tree. No remote is configured and no push is part of this audit.

Private game inputs, generated outputs and the external historical backup are outside the publishable content. They were not erased, uploaded or represented as public repository files. Share the Git repository through Git rather than uploading the entire research folder or private backup.

## Method and repeatable acceptance check

The review used local Git object inspection, Python standard-library pattern scanning and manual review of flagged locations, public paths, upstream notices and repository configuration. No scanner uploaded file contents to a service. No external scanner binary was installed.

`publication_privacy.py` checks local account markers in memory, absolute workstation/home paths, unreviewed email addresses, common provider-token formats, direct credential assignments, credential-bearing URLs, signed-token patterns, private network addresses and unusually large hex/base64 payload candidates. Private marker values are never written into public rules or reports. Exact pinned upstream files retain their legitimate author/license information. Commit auditing permits only the exact repository-configured owner identity in author/committer headers; it does not exempt commit messages, file contents or mismatched attribution.

The existing checker also verifies source-only paths, text and file sizes, Git modes, Python/JSON syntax, Markdown rules, links and dependency file hashes. Its negative examples exercise both content exclusions and privacy rejection.

```powershell
python scripts/check_public_tree.py --history
```

This must pass after the final sanitized commit is created and superseded private Git objects are removed. History mode requires `main` as the only local branch, checks all reachable trees and commit metadata across all references, and fails if unreachable Git objects remain. The normal pre-commit hook checks the complete staged index on subsequent commits.

## Limits

This is a publication privacy/content audit, not a dependency CVE audit or a proof that every possible secret format can be detected. Pattern matching cannot identify every personal name, street address, novel credential or encoded payload. The initial findings were reviewed and removed manually; future changes still require staged-diff review.

Owner-approved Git attribution, upstream author names, public repository links, licenses, game build identifiers, source hashes and concise research findings are intentional public research metadata. The audit preserves approved authorship and required attribution while excluding private owner data.
