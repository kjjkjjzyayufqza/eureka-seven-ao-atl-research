"""Check publishable text for local identities, credentials and private paths."""

import ipaddress
import os
from pathlib import Path
import re
import subprocess


PATTERNS = {
    "absolute workstation path": re.compile(r"(?i)\b[A-Z]:[\\/]|[/](?:home|Users)[/][^\s/]+"),
    "provider credential": re.compile(
        r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,}"
        r"|(?:AKIA|ASIA)[A-Z0-9]{16}|AIza[A-Za-z0-9_-]{35}"
        r"|sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{24,}"
        r"|xox[baprs]-[A-Za-z0-9-]{20,}|(?:sk|rk)_live_[A-Za-z0-9]{20,}"
        r"|SG\.[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{20,})\b"
    ),
    "credential assignment": re.compile(
        r'''(?im)^\s*(?:api[_-]?key|access[_-]?token|auth[_-]?token|secret|password|passwd|client[_-]?secret)\s*[:=]\s*[rubf]?["'][^"'\r\n]{8,}["']'''
    ),
    "credential-bearing URL": re.compile(r"https?://[^\s/:@]+:[^\s/@]+@"),
    "signed token": re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
    "embedded payload candidate": re.compile(r"(?:[A-Fa-f0-9]{256,}|[A-Za-z0-9+/]{400,}={0,2})"),
}
EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b")
IP_ADDRESS = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")


def local_identity_markers():
    """Read identity values in memory; never store them in a public file."""
    values = {os.environ.get("USERNAME", ""), Path.home().name}
    for key in ("user.name", "user.email"):
        result = subprocess.run(
            ["git", "config", "--global", "--get", key],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        if result.returncode == 0:
            value = result.stdout.decode("utf-8").strip()
            values.add(value)
            if "@" in value:
                values.add(value.split("@", 1)[0])
    return {value.casefold() for value in values if len(value) >= 6}


def validate_privacy_text(path, text, markers=(), upstream=False):
    for category, pattern in PATTERNS.items():
        match = pattern.search(text)
        if match:
            line = text.count("\n", 0, match.start()) + 1
            raise ValueError(f"Publication privacy: {category}: {path}:{line}")
    lowered = text.casefold()
    if any(marker in lowered for marker in markers):
        raise ValueError(f"Publication privacy: local account identifier: {path}")
    if not upstream:
        for match in EMAIL.finditer(text):
            domain = match.group(1).lower()
            if domain not in {"example.com", "example.org", "example.net"} and not domain.endswith(".invalid"):
                raise ValueError(f"Publication privacy: unreviewed email address: {path}")
    for match in IP_ADDRESS.finditer(text):
        try:
            address = ipaddress.IPv4Address(match.group())
        except ipaddress.AddressValueError:
            continue
        if not address.is_global:
            raise ValueError(f"Publication privacy: non-public network address: {path}")


def validate_commit_metadata(metadata, markers, approved_identity):
    """Allow the approved owner identity only in author/committer headers."""
    headers, separator, message = metadata.partition("\n\n")
    if not separator:
        raise ValueError("Commit metadata has no message separator")
    remaining = []
    roles = set()
    for line in headers.splitlines():
        if line.startswith(("author ", "committer ")):
            match = re.fullmatch(r"(author|committer) (.+) <([^<>]+)> \d+ [+-]\d{4}", line)
            if not match or (match[2], match[3]) != approved_identity or match[1] in roles:
                raise ValueError("Commit attribution differs from the approved repository identity")
            roles.add(match[1])
        else:
            remaining.append(line)
    if roles != {"author", "committer"}:
        raise ValueError("Commit metadata must contain author and committer attribution")
    validate_privacy_text("commit metadata", "\n".join(remaining) + "\n\n" + message, markers)


def check_privacy_examples():
    validate_privacy_text("example", "Use a researcher-provided input archive.")
    rejected = [
        "Z:" + "/workstation/private.txt",
        "/" + "home" + "/person/private.txt",
        "person" + "@" + "mail.test",
        "ghp_" + "X" * 36,
        "https://" + "person:password" + "@" + "host.invalid",
        str(ipaddress.IPv4Address(0x0A010203)),
    ]
    for text in rejected:
        try:
            validate_privacy_text("privacy rejection example", text)
        except ValueError:
            continue
        raise ValueError("Publication privacy guard accepted a forbidden example")
    identity = ("Public Maintainer", "maintainer" + "@" + "users.noreply.github.com")
    markers = {identity[0].casefold(), "maintainer"}
    headers = f"author {identity[0]} <{identity[1]}> 0 +0000\ncommitter {identity[0]} <{identity[1]}> 0 +0000\n\n"
    validate_commit_metadata(headers + "Research commit\n", markers, identity)
    invalid_metadata = [
        headers + identity[0],
        headers.replace("author Public Maintainer", "author Another Person") + "Research commit\n",
        headers + "ghp_" + "X" * 36,
    ]
    for metadata in invalid_metadata:
        try:
            validate_commit_metadata(metadata, markers, identity)
        except ValueError:
            continue
        raise ValueError("Commit privacy guard accepted a forbidden example")
    return len(rejected) + len(invalid_metadata)
